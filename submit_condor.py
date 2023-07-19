import os
import sys
import argparse 

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin July')

parser.add_argument('nrun', type=str, help='nrun (input file name (in "../crilin_input/", without ".root")')
parser.add_argument('label', type=str, help='label', default="")
parser.add_argument('fb', type=int, help='Front board (0/1)', default=0)
parser.add_argument('timeoffset', type=float, help='Time offset (ns)', default=0)
parser.add_argument('nevents_per_job', type=int, help='nevents_per_job', default=200)
parser.add_argument('njobs', type=int, help='njobs', default=500)
parser.add_argument('--rootinputfolder', type=str, help="Root input folder", default='/eos/user/r/rgargiul/www/crilin/input/')
parser.add_argument('--condorfolder', type=str, help="Folder where logs etc. are saved", default='/afs/cern.ch/work/r/rgargiul/crilin_jobs')
parser.add_argument('--rootoutfolder', type=str, help="Root/json out folder", default='/eos/user/r/rgargiul/www/crilin/output/')

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

os.system(f"mkdir {condorfolder}/{nrun}")
os.system(f"mkdir {condorfolder}/{nrun}/output")
os.system(f"mkdir {condorfolder}/{nrun}/error")
os.system(f"mkdir {condorfolder}/{nrun}/log")
os.system(f"mkdir {rootoutfolder}/{nrun}")

sub = open("jobsub.condor", "r").read()

for key in v:
  sub = sub.replace(f"${key}", str(v[key]))

f = open(f"{condorfolder}/{nrun}/jobsub{nrun}.condor", "w")
f.write(sub)
f.close()

os.system(f"condor_submit {condorfolder}/{nrun}/jobsub{nrun}.condor")
