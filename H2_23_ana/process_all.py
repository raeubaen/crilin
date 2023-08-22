import os
import sys
import pandas as pd
import argparse
import ROOT

parser = argparse.ArgumentParser(description='Run submit for condor')

parser.add_argument('mapfile', type=str, help='File with the map')
parser.add_argument('--nevents_per_job', type=int, help='nevents_per_job', default=2000)
parser.add_argument('--njobs', type=int, help='njobs', default=50)
parser.add_argument('--tag', type=str,   default="")
parser.add_argument('--dry', type=str,   default="")

args = parser.parse_args()

def reco(row):
  
  if len(glob.glob(f"/eos/user/d/dpaesani/H2_23/reco/run{row.run}{row.label}")) > 0:
    if row.forceprocess: os.system(f"rm /eos/user/d/dpaesani/H2_23/reco/run{row.run}{row.label}/*")
    else: raise ValueError(f"already processed {row.run}{row.label}")
  else:
    os.system(f"mkdir /eos/user/d/dpaesani/H2_23/reco/run{row.run}{row.label}")

  njobs = ROOT.TFile(f"/eos/user/d/dpaesani/H2_23/merges/run{row.run}{row.label}.root")
  cmd = f"python3 submit_condor.py {row.run} {row.label} {nevents_per_job} {njobs}"
    " --type {row.type} --tag {tag} --forceprocess {row.forceprocess} --dry {dry}"
  
  for key in args:
    if key not in ['mapfile', 'nevents_per_job', 'njobs']:
      cmd += f" --{key} {args[key]} "

  print(cmd)
  os.system(cmd)

df = pd.read_csv(mapfilemapfile, sep=" ", header=None)
df.columns = ["nrun", "type", "orientation", "label", "x0", "y0", "bias_series", "bias_parallel", "forceprocess"]

print(df)

df.apply(lambda row: reco(row), axis=1)
