import argparse
import matplotlib.pyplot as plt
import numpy as np
import ast
import csv
import os
import pickle


def parse_tuple_list(value):
    try:
        # Safely evaluate the literal syntax of the input string
        result = ast.literal_eval(value)
        # Check if the result is a list of tuples
        if isinstance(result, list) and all(isinstance(item, tuple) for item in result):
            return result
        else:
            raise argparse.ArgumentTypeError("Input must be a list of tuples")
    except (ValueError, SyntaxError):
        raise argparse.ArgumentTypeError("Invalid input format. Must be a valid list of tuples")


def get_args():

    parser = argparse.ArgumentParser(description='Plot Cartesian distance vs. steps from a trajectory file.')
    parser.add_argument('file_path',
                        type=str,
                        help='Path to the trajectory file')
    parser.add_argument('--atom_pair',
                        '-a',
                        type=parse_tuple_list,
                        required=True,
                        help='atom pairs, input as list of tuples, 1-indexed')
    parser.add_argument('--time_step',
                        '-t',
                        type=float,
                        help='Simulation time step in fs')
    parser.add_argument('--skip',
                        type=int,
                        default=0,
                        help='Skip analysis of first n geometries in the trj file')
    parser.add_argument('--show_plots',
                        '-s',
                        type=bool,
                        help='Show plots after saving',
                        default=False)

    return parser.parse_args()


def get_num_steps(filename, skip_number):
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Reverse the lines to read backwards
    reversed_lines = reversed(lines)

    found_last_step = False
    found_first_step = False
    num_steps = 0

    for line in reversed_lines:
        # Check if the line contains the desired string
        if "# ORCA AIMD Position Step" in line:
            found_last_step = True
            # Extract the integer that follows the string, removing the comma
            last_step_num = int(line.split()[5].rstrip(','))
            break

    for line in lines:
        # Check if the line contains the desired string
        if "# ORCA AIMD Position Step" in line:
            found_first_step = True
            # Extract the integer that follows the string, removing the comma
            first_step_num = int(line.split()[5].rstrip(','))
            break

    num_steps = last_step_num - first_step_num + 1

    return num_steps - skip_number


def analyze_trajectory(filename, atom_number1, atom_number2, time_step, skip_number):
    distances = []
    sim_list = []
    atom1_type = []
    atom2_type = []
    atom_types_list = []
    checkpoint_file_exists = False

    print("Extracting atom types and checking for checkpoint file...")
    with open(filename, 'r') as file:
        lines = file.readlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().isdigit():
            num_atoms = int(lines[i])
            i += 2
            for j in range(num_atoms):
                atom_types = [coord for coord in lines[i].split()]
                atom_types_list.append(atom_types)
                i += 1
            break

    atom_label1 = str(atom_types_list[atom_number1 - 1][0])
    atom_label2 = str(atom_types_list[atom_number2 - 1][0])
    atom_pair_string = str(atom_label1 + str(atom_number1) + '-' + atom_label2 + str(atom_number2))

    checkpoint_filename = f'{atom_pair_string}.pkl'
    if not os.path.isfile(checkpoint_filename):
        print("Checkpoint file not found, initiating data extraction")

        i = 0
        sim_step = 0
        print("Reading trajectory")
        while i < len(lines):
            if lines[i].strip().isdigit():
                num_atoms = int(lines[i])
                i += 2
                current_coords = []

                for j in range(num_atoms):
                    atom_types = [str(coord) for coord in lines[i].split()[0]]
                    coords = [float(coord) for coord in lines[i].split()[1:]]
                    current_coords.append(coords)
                    i += 1

                if not sim_step < skip_number:
                    # switched atom numbering from 1-index to 0-index
                    if len(current_coords) == num_atoms:
                        atom1_coords = current_coords[atom_number1-1]
                        atom2_coords = current_coords[atom_number2-1]
                        distance = np.linalg.norm(np.array(atom1_coords) - np.array(atom2_coords))
                        sim_list.append(sim_step)
                        distances.append(distance)

                sim_step += 1

            else:
                i += 1

        _write_checkpoints(checkpoint_filename,sim_list,distances)

    else:
        print(f"Checkpoint file {checkpoint_filename} found, extracting distances...")
        sim_list, distances = _extract_distances_from_checkpoint(checkpoint_filename)

    print(f"Extracted atom pair data for {atom_pair_string}")
    mean_distance, min_distance, max_distance, stdev_distance = _print_analysis(distances)
    _write_csv(atom_label1, atom_number1, atom_label2, atom_number2, mean_distance, min_distance, max_distance, stdev_distance)

    _plot_distance_vs_steps(sim_list,
                           distances,
                           atom_label1,
                           atom_label2,
                           atom_number1,
                           atom_number2,
                           mean_distance,
                           stdev_distance,
                           min_distance,
                           max_distance,
                           time_step,
                           show_plots)

    return distances, atom_pair_string


def _print_analysis(distances):

    mean_distance = np.mean(distances)
    min_distance = np.min(distances)
    max_distance = np.max(distances)
    stdev_distance = np.std(distances)
    print(f'Mean distance: {mean_distance:.3f}\n'
          f'Min distance: {min_distance:.3f}\n'
          f'Max distance: {max_distance:.3f}\n'
          f'Std deviation: {stdev_distance:.3f}')

    return mean_distance, min_distance, max_distance, stdev_distance


def _plot_distance_vs_steps(sim_list,
                            distances,
                            atom_label1,
                            atom_label2,
                            atom_number1,
                            atom_number2,
                            mean_distance,
                            stdev_distance,
                            min_distance,
                            max_distance,
                            time_step,
                            show_plots):

    print("Plotting...")

    plt.clf()

    time_step_list = np.array(sim_list) * time_step

    plt.plot(time_step_list, distances)
    plt.axhline(y=mean_distance, color='r', linestyle='--')
    plt.axhspan(mean_distance-stdev_distance, mean_distance+stdev_distance, color='gray', alpha=0.1)
    plt.xlabel('Time / fs')
    plt.ylabel(f'Distance between Atom {atom_label1}{atom_number1} and Atom {atom_label2}{atom_number2}')
    # plt.title('Cartesian Distance vs. Steps')
    lower_limit = mean_distance-2*stdev_distance
    upper_limit = mean_distance+2*stdev_distance
    print(f'Plotting between limits of {lower_limit:.3f} and {upper_limit:.3f}')
    plt.ylim(mean_distance-2.5*stdev_distance, mean_distance+2.5*stdev_distance)
    plt.savefig(f'{atom_label1}{atom_number1}-{atom_label2}{atom_number2}.pdf')
    if show_plots:
        plt.show()

    return None


def create_csv(csv_file_path):
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Atom1", "Atom2", "Mean distance / A", "Min distance / A", "Max distance / A", "Std dev distance / A"])


def _write_csv(atom_label1, atom_number1, atom_label2, atom_number2, mean_distance, min_distance, max_distance, stdev_distance):

    atom1 = str(atom_label1)+str(atom_number1)
    atom2 = str(atom_label2)+str(atom_number2)

    print("Writing data to output.csv...")

    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow((atom1, atom2, mean_distance, min_distance, max_distance, stdev_distance))


def _write_checkpoints(checkpoint_filename,sim_list,distances):

    with open(checkpoint_filename, "wb") as file:
        pickle.dump(sim_list, file)
        pickle.dump(distances, file)

    return None


def _extract_distances_from_checkpoint(checkpoint_filename):

    with open(checkpoint_filename, "rb") as file:
        extracted_sim_list = pickle.load(file)
        extracted_distances = pickle.load(file)

    return extracted_sim_list, extracted_distances


def make_violin_plots(distances_array, atom_pair_list):

    plt.clf()

    plt.figure(figsize=(12, 4))  # Increase the width of the plot

    plt.violinplot(distances_array.T, showmedians=True)
    plt.xticks(range(1, len(atom_pair_list) + 1), atom_pair_list, rotation=45, ha='right', fontsize=10)
    plt.xlabel('Atom pair', fontsize=14)
    plt.tick_params(axis='x', labelsize=14)
    plt.ylabel(f'Distance / Å', fontsize=14)
    plt.tick_params(axis='y', labelsize=14)

    plt.axhspan(3.80, 3.86, color='red', alpha=0.1)  # alkyl radical HAT C–C distance range (2.70-2.76) + C–H bond length (1.1 A) to correct for C–H/C–H clash in MD simulations
    plt.axhspan(3.45, 3.52, color='blue', alpha=0.1)  # alkoxy radical HAT C–C distance range
    plt.axhspan(3.78, 4.33, color='green', alpha=0.1)  # peroxy radical HAT C–C distance range
    plt.axhspan(5.068, 5.109, color='purple', alpha=0.1)  # bimolecular peroxy decomposition C–C distance range

    plt.tight_layout()
    plt.savefig('violin.pdf')
    if show_plots:
        plt.show()

    return None


if __name__ == "__main__":

    print("Starting up trajectory analysis...")

    args = get_args()
    file_path = args.file_path
    atom_tuple_list = args.atom_pair
    time_step = args.time_step
    show_plots = args.show_plots
    skip_number = args.skip

    csv_file_path = "output.csv"
    create_csv(csv_file_path)

    num_steps = get_num_steps(file_path, skip_number)
    num_tuples = len(atom_tuple_list)

    distances_array = np.empty((num_tuples,num_steps))
    atom_pair_list = []

    for i in range(num_tuples):
        sim_list, distances = [], []
        print(f"Initiating analysis of atom pair {i+1} of {len(atom_tuple_list)} =============")

        distances_array[i], atom_pair_string = analyze_trajectory(file_path, atom_tuple_list[i][0], atom_tuple_list[i][1], time_step, skip_number)
        atom_pair_list.append(atom_pair_string)
        print("\n")

    print("Creating violin plots")
    make_violin_plots(distances_array, atom_pair_list)

    print("Analysis complete")
