# Orca-Scripts
Useful scripts for running Orca

1. trj_analysis.py 

      Python3 script to analyze an ORCA molecular dynamics trajectory run. Specify bond lengths to be analyzed, run script on trajectory xyz file.
      Script generates a .pkl file for each trajectory for faster analysis for subsequent analyses after trajectory has been analyzed once.
      Creates a plot showing the value of the specied bond length as a function of time, and aggregates all bond lengths into a violin plot.

2. irc.py (now obsolete)

      Python3 script to manually run an IRC calculation from an ORCA transition state calculation

4. imag.py

      Python3 script that checks for imaginary frequencies in optimisation runs with ORCA
