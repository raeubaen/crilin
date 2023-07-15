import os
import sys
import argparse 

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin July')

parser.add_argument('nrun', type=str, help='nrun (input file name (in "../crilin_input/", without ".root")')
parser.add_argument('label', type=str, help='label', default="")
parser.add_argument('fb', type=int, help='Front board (0/1)', default=0)
parser.add_argument('nevents_per_job', type=int, help='nevents_per_job', default=200)
parser.add_argument('njobs', type=int, help='njobs', default=500)
parser.add_argument('--mainfolder', type=str, help="Folder where crilin_input, the repo directory and reco_data are placed", default='/afs/cern.ch/work/r/rgargiul/')
parser.add_argument('--repofolder', type=str, help="Name of the folder with the repo", default='code_reco')

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

os.system(f"mkdir ../reco_data/{nrun}")
os.system(f"mkdir ../reco_data/{nrun}/output")
os.system(f"mkdir ../reco_data/{nrun}/error")
os.system(f"mkdir ../reco_data/{nrun}/log")
os.system(f"mkdir ../reco_data/{nrun}/tree_and_json")

sub = open("jobsub.condor", "r").read()

for key in v:
  sub = sub.replace(f"${key}", str(v[key]))

f = open(f"../reco_data/{nrun}/jobsub{nrun}.condor", "w")
f.write(sub)
f.close()

os.system(f"condor_submit ../reco_data/{nrun}/jobsub{nrun}.condor")
