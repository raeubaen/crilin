import os
import sys
import argparse 
import pandas as pd
import glob
import uproot
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import subprocess
import merge
    
rundict = "runlist.csv"
df = pd.read_csv(rundict, sep=" ", header=None)
df.columns = ["run", "typ", "orientation", "label", "bias_series", "bias_parallel"]

parser = argparse.ArgumentParser(description='Wave reco H2 2023')

parser.add_argument('runlist',  type=str)
parser.add_argument('--force',  type=bool,  default=0)
parser.add_argument('--tag',    type=str,   default="")
parser.add_argument('--dry',    type=str,   default="")
parser.add_argument('--opts',   type=str,   default="")
parser.add_argument('--minevperjobs',   type=int,   default=3000)
parser.add_argument('--nspecs',   type=int,   default=10)
parser.add_argument('--afspath',   type=str,   default="/afs/cern.ch/work/r/rgargiul/condorh2/H2_23_ana/")

args = parser.parse_args()

scriptpath = F"{args.afspath}/reco.py"

for ii in df["run"].astype(int) if args.runlist == "all" else [int(item) for item in args.runlist.split(' ')]:
    print("processing run", args.runlist)

    dumppath = F"{args.afspath}/condor_stuff/run{ii}{args.tag}"
    fcondor = F"{dumppath}/jobsub{ii}{args.tag}.condor"
    inpath = f"/eos/project/i/insulab-como/testBeam/TB_H2_2023_08_HIKE/MATTIA_WRITE_HERE/splitted/run700{ii}_%06d.root"
    #outpath = F"/eos/user/d/dpaesani/data/H2_23/reco/run{ii}{args.tag}"
    outpath = F"/eos/user/r/rgargiul/www/crilin/provedanielereco/run{ii}{args.tag}"
    outfile = outpath + F"/run{ii}{args.tag}"
    spill_list_path = f"{dumppath}/spill_list_%d.txt"
    row = df[df["run"] == ii]
    
    if len(glob.glob(outpath)) > 0:
        print("already processed")
        if not args.force: 
            print("skipping")
            continue
        else: 
            print("reprocessing")
            os.system(F"rm -r {outpath}/*")

    os.system(F"mkdir {outpath}")
    os.system(F"rm -r {dumppath}")
    os.system(F"mkdir {dumppath}")

    spill_n = 0
    temp_evcounter = 0
    temp_spill_list = []
    job_counter = 0
    spill_file_list = glob.glob(inpath.replace("%06d", "*"))
    spill_file_count = len(spill_file_list)
    for file_n, spill_file in enumerate(glob.glob(inpath.replace("%06d", "*"))):
      spill_n = int(spill_file.split("_")[-1].split(".root")[0])
      temp_spill_list.append(str(spill_n))
      try:
        temp_evcounter += uproot.open(spill_file)["t"].num_entries
      except:
        print(F"{spill_file} not OK")
      if file_n == spill_file_count-1 or temp_evcounter > args.minevperjobs:
        print(f"writing in {spill_list_path%job_counter}")
        open(spill_list_path%job_counter, "w").write(",".join(temp_spill_list))
        job_counter += 1
        temp_spill_list = []
        temp_evcounter = 0
      spill_n += 1 

    argstring = F"{row.typ[0]} {inpath} {outfile} {spill_list_path}"

    for key in vars(args):      
        if key not in ['runlist', 'force', 'minevperjobs', 'afspath']:
            if vars(args)[key] != "": argstring += F" --{key} {vars(args)[key]} "

    njobs = job_counter-1
    
    sub = open("jobsub.condor", "r").read()
    sub = sub.replace(F"$*", argstring)
    sub = sub.replace(F"$condorfolder", dumppath)
    sub = sub.replace(F"$nrun", f"{ii}")
    sub = sub.replace(F"$njobs", str(njobs))
    sub = sub.replace(F"$ScriptPath", scriptpath)

    f = open(fcondor, "w")
    f.write(sub)
    f.close()

    os.system(F"condor_submit {fcondor}")
    os.system("condor_q")
    
    pool = ThreadPoolExecutor()
    f = pool.submit(subprocess.call, F"/usr/bin/condor_wait {dumppath}/log*", shell=True)
    callback = lambda x: merge.merge(outpath)
    f.add_done_callback(callback)
    pool.shutdown(wait=False) # no .submit() calls after that point
