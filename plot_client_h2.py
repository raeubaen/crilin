import subprocess
import argparse
import os

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin')

parser.add_argument('outfolder', type=str, help='outfolder', default="")

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

process = 0

while True:
  if not os.path.exists(f"{outfolder}/plotlock"): continue
  os.system(f"rm {outfolder}/plotlock")
  if process != 0: process.kill()
  process = subprocess.Popen(f"root -x \"plot_client_h2.C(\\\"{outfolder}/out_cat.root\\\")\"", shell = True)
