import os
import sys
import argparse 

parser = argparse.ArgumentParser(description='Wave reco H2 2023')

parser.add_argument('nrun',           type=str)
parser.add_argument('evtp',           type=int, default=200)
parser.add_argument('type',           type=str, default="")
parser.add_argument('njobs',          type=int, default=500)
parser.add_argument('--tag',          type=str, default="")
parser.add_argument('--dry',          type=str, default="")
parser.add_argument('--opts',         type=str,   default="")

args = parser.parse_args()

scriptpath = F"/afs/cern.ch/user/d/dpaesani/public/H2_23_ana/reco.py"
dumppath = F"/afs/cern.ch/user/d/dpaesani/public/H2_23_ana/output/run{args.nrun}{args.tag}"
dumppathout = dumppath + "/out/"
fcondor = F"{dumppath}/jobsub{args.nrun}{args.tag}.condor"
inpath = F"/eos/user/d/dpaesani/data/H2_23/merged/run700{args.nrun}{args.tag}.root"
outpath = F"/eos/user/d/dpaesani/data/H2_23/reco/run{args.nrun}{args.tag}/run{args.nrun}{args.tag}"

os.system(F"mkdir -p {outpath}")
os.system(F"mkdir -p {dumppathout}")
os.system(F"rm {dumppathout}/*")

argstring = F"{args.evtp} {args.type} {inpath} {outpath}"

for key in vars(args):
  if key not in ['nrun', 'type', 'njobs', 'evtp']:
    if vars(args)[key] != "": argstring += F" --{key} {vars(args)[key]} "

sub = open("jobsub.condor", "r").read()
sub = sub.replace(F"$*", argstring)
sub = sub.replace(F"$condorfolder", dumppathout)
sub = sub.replace(F"$nrun", f"run{args.nrun}")
sub = sub.replace(F"$njobs", str(args.njobs))
sub = sub.replace(F"$ScriptPath", scriptpath)

f = open(fcondor, "w")
f.write(sub)
f.close()

os.system(F"condor_submit {fcondor}")
os.system("condor_q")