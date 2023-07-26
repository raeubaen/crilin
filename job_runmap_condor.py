#INCOMPLETOOOOOOOOOOOOO

import os
import sys
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Run submit for condor')

parser.add_argument('mapfile', type=str, help='File with the map')
parser.add_argument('--nevents_per_job', type=int, help='nevents_per_job', default=2000)
parser.add_argument('--njobs', type=int, help='njobs', default=50)
parser.add_argument('--rootinputfolder', type=str, help="Root input folder", default='/eos/user/r/rgargiul/www/crilin/input/recoruns/')
parser.add_argument('--condorfolder', type=str, help="Folder where logs etc. are saved", default='/afs/cern.ch/work/r/rgargiul/crilin_jobs')
parser.add_argument('--rootoutfolder', type=str, help="Root/json out folder", default='/eos/user/e/edimeco/BTF/crilin/output/')

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

def reco(row):
  cmd = f"python3 submit_condor.py {row.nrun} {row.nrun} {row.board} {int(row.timeoffset)} {nevents_per_job} {njobs} --rootinputfolder {rootinputfolder} --condorfolder {condorfolder} --rootoutfolder {rootoutfolder}"
  print(cmd)
  os.system(cmd)

df = pd.read_csv(mapfile, sep=" ", header=None)
df.columns = ["nrun", "board", "timeoffset"]

print(df)

df.apply(lambda row: reco(row), axis=1)
