#!<python3 path>
import sys
import os
from sys import argv

# input tmp.py filename.out
# both <filename>.inp and <filename>.out must be in same directory
filename = sys.argv[1]
name = filename.split('.')
print(name)
first = name[0]
second = name[1]
third = first + "." + second

# generate 20 frames from transition state frequency (number 6 for non-linear molecules)
# create xyz coordinates for each of these 20 structures

command = 'orca_pltvib ' + third + " 6"
os.system(command)

#filename="OptTS_Freq_benzyl-BCP_TPSS-D3_def2TZVP.out.v006.xyz"
fourth = name[0] + ".out.v006.xyz"
file=open(fourth, "r")

# frames 1 and 20 are TS geometry, so take frames 2 and 19 for IRC either side of TS

filename2="IRC_f2_" + first + ".inp"
file2=open(filename2, "w")

filename3="IRC_f19_" + first + ".inp"
file3=open(filename3, "w")

filename4=first + ".inp"
file4=open(filename4, "r")

# remove TS and Freq calculations from new file input block

star1=0
keywords=['OptTS', 'NumFreq', 'Freq']
for line in file4:
    if line.startswith('!'):
        keys=line.split()
        for keyword in keywords:
            if keyword in keys:
                keys.remove(keyword)
    if line.startswith('*'):
        charge=line.split()
        star1 += 1
        if star1 == 1:
            one=charge[1]
            two=charge[2]

# print charge and multiplicity
print(*keys, file=file2)
# this block forces orca to run steepest descent optimisation instead of Quasi-Newton algorithm
print("\n%maxcore 4000\n\n", "%geom\n", " inhess unit\n", " update noupdate\n", " step qn\n", "end\n\n", "*xyz " + one + " " + two, sep='', file=file2)


print(*keys, file=file3)
print("\n%maxcore 4000\n\n", "%geom\n", " inhess unit\n", " update noupdate\n", " step qn\n", "end\n\n", "*xyz " + one + " " + two, sep='', file=file3)

stars = 0
for line in file:
    if line.startswith('*'):
        stars += 1
    if stars == 2 and len(line.split()) == 7:
        d=line.split()
        print(d[0], d[1], d[2], d[3], sep='\t\t', file=file2)
    if stars == 19 and len(line.split()) == 7:
        d = line.split()
        print(d[0], d[1], d[2], d[3], sep='\t\t', file=file3)

print('*', file=file2)
print('*', file=file3)
