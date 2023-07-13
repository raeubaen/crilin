import os
import sys
import signal
import subprocess

nrun = sys.argv[1]

procs = []
n = 0

os.system(f"mkdir ../rawhisto/run{nrun}")
os.system(f"mkdir ../reco/run{nrun}")

label = sys.argv[2]

fb = sys.argv[3] # front board

while True:
    print(f"scp-ing fragment {n}")
    exit_code = os.system(f"sshpass -p mu2e scp mu2e@mu2edaq:/home/mu2e/DAQ/rawhisto/run{nrun}/rawhisto_run{nrun}_{n:03d}.root ../rawhisto/run{nrun}/rawhisto_run{nrun}_{n:03d}.root")

    if exit_code != 0:
      print("retrying - file not found")
      continue

    print(f"reco-ing fragment {n}")

    os.system(f"python3 step3.py ../rawhisto/run{nrun}/rawhisto_run{nrun}_{n:03d}.root ../reco/run{nrun}/reco_run{nrun}_{n:03d}.root {label} {n*1000} {fb} --maxevents 100")

    print(f"hadd-ing fragment {n}")
    if n==0: os.system(f"cp ../reco/run{nrun}/reco_run{nrun}_{n:03d}.root ../reco/run{nrun}/reco_run{nrun}_temp.root")
    else:
      if n!=1: os.system(f"mv ../reco/run{nrun}/reco_run{nrun}_cat.root ../reco/run{nrun}/reco_run{nrun}_temp.root")
      os.system(f"hadd ../reco/run{nrun}/reco_run{nrun}_cat.root ../reco/run{nrun}/reco_run{nrun}_{n:03d}.root ../reco/run{nrun}/reco_run{nrun}_temp.root")

    print("\n\n\n")
    n+=1
    if n>=int(sys.argv[4]): break
