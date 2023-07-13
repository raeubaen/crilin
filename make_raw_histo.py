import os
import sys
import signal
import subprocess
import time

daq_root_folder = "/home/mu2e/DAQ/rawdata/"
nrun = int(sys.argv[1])
header = ""
for item in os.listdir(daq_root_folder):
    if os.path.isdir(f"{daq_root_folder}") and f"{nrun:07d}" in item:
        header = f"{daq_root_folder}" + item + "/" + item + "_lvl1_00_"

os.system(f"mkdir /home/mu2e/DAQ/rawhisto/run{nrun}")

procs = []
n = 0

while True:
  if os.path.isfile(header+f"{n:03d}.root"):

    print(f"found {header}{n:03d}'.root")

    exit_code = os.system(f"/home/mu2e/DAQ/RawHisto.exe -n 1000 -i {header+f'{n:03d}.root'} -o /home/mu2e/DAQ/rawhisto/run{nrun}/rawhisto_run{nrun}_{n:03d}_temp.root")

    if exit_code != 0:
      print("exiting - file not closed - rawhisto failed")
      continue

    os.system(f"mv /home/mu2e/DAQ/rawhisto/run{nrun}/rawhisto_run{nrun}_{n:03d}_temp.root /home/mu2e/DAQ/rawhisto/run{nrun}/rawhisto_run{nrun}_{n:03d}.root")

    n+=1
