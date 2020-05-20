#!/usr/bin/env python3
import argparse
import os

def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", action='store', help='.out file(s) to check for imaginary frequencies', nargs='+')

    return parser.parse_args()

def print_imag(filenames):

    print('Imaginary frequency checker running...')

    for out_file in filenames:

        vib_freq_section = False
        opt_done = False
        opt_ts = False
        opt = False
        freq = False

        with open(out_file, 'r') as out_file_r:

            for line in out_file_r:
                # Grab the keywords from the output file
                if '1> !' in line:
                    for item in line.split():
                        if item == 'Opt' or 'TightOpt':
                            opt = True
                        if item == 'OptTS':
                            opt_ts = True
                        if item == 'Freq' or 'NumFreq':
                            freq = True

                if freq:

                    if '*** OPTIMIZATION RUN DONE ***' in line:
                        opt_done = True

                    if opt_done:
                        if line.startswith("VIBRATIONAL FREQUENCIES"):
                            vib_freq_section = True

                    if vib_freq_section:
                            if '***imaginary mode***' in line and opt:
                                imag_freq = line.split()[1]
                                print('Imaginary freq (', imag_freq, ') in', out_file, ': species is not a true minimum')

                            if '***imaginary mode***' in line and opt_ts:
                                imag_freq = line.split()[1]
                                print(name, ' Imaginary frequency of TS is  ', imag_freq)



if __name__ == '__main__':

    args = get_args()
    print_imag(args.filenames)
    print('Imaginary frequency checker done')
