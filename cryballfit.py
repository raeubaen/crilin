#python3

#questo fa un dataset solo (anche molti file) ma una sola tchain

#va chiamato da un'altro programma lasciando plot.conf costante e variando data.conf per fare tutti i dataset in batch con gli stessi plot e gli stessi tagli

import ROOT
import sys
import pandas as pd
import os
import argparse

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin July')

parser.add_argument('dataconffile', type=str, help='dataconffile')
parser.add_argument('outputfolder', type=str, help='outfolder')
parser.add_argument("inputfolder", type=str, help="infolder")

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

def process(row, outputfolder, inputfolder):
  os.system(f"mkdir {outputfolder}/{row.label}")
  os.system(f"cp index.php {outputfolder}/{row.label}")
  for plot in ["ztiming_0_8_9", "ztiming_1_8_9"]: #, "timing_0_8_9", "timing_1_8_9"]:
    os.system(f"/bin/bash -c 'source crystalball_fit.sh {plot} {inputfolder}/{row.label} {outputfolder}/{row.label}'")

dataconf_df = pd.read_csv(dataconffile, sep=";")

os.system(f"cp index.php {outputfolder}")

dataconf_df.apply(lambda row: process(row, outputfolder, inputfolder), axis=1)
