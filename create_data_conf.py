import pandas as pd


import os
import sys
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Run submit for condor')

parser.add_argument('--mapfile', type=str, help='File with the map', default="conf_condor")
parser.add_argument('--nevents_per_job', type=int, help='nevents_per_job', default=2000)
parser.add_argument('--njobs', type=int, help='njobs', default=50)
parser.add_argument('--recooutfolder', type=str, help="Reco root out folder", default='../elisaeoscrilin/output/')

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

def reco(row, d):
    d["label"].append(f"{row.nrun}")
    d["filename"].append(f"{recooutfolder}/{row.nrun}/{row.nrun}_out_{{0..{njobs}}}.root")
    d["treename"].append("tree")

df = pd.read_csv(mapfile, sep=" ", header=None)
df.columns = ["nrun", "board", "timeoffset"]

d = {"label": [], "filename": [], "treename": []}

df.apply(lambda row: reco(row, d), axis=1)

pd.DataFrame(d).to_csv("data.conf", sep=";", index=None)
