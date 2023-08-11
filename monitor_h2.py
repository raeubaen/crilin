import os
import argparse
import time

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin')

parser.add_argument('infilename', type=str, help='Input file name .root')
parser.add_argument('outfolder', type=str, help='outfolder', default="")
parser.add_argument('label', type=str, help='label', default="")
parser.add_argument('frontboard', type=int, help='Board. in front', default=0)
parser.add_argument('--startn', type=int, help='skip n fragments', default=0)
parser.add_argument('--cat', type=int, help='concatenate last .cat file when startn!=0', default=1)
parser.add_argument('--sleep', type=int, help='sleep between fragments', default=1)

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

procs = []
n = startn

os.system(f"mkdir {outfolder}")

while True:
    print(f"reco-ing fragment {n}")

    os.system(f"python3 recogpu.py {infilename} {outfolder}/out_{n}.root {label} {frontboard} {100*n} 100")

    print(f"hadd-ing fragment {n}")
    if n==startn:
      if cat and startn>0: os.system(f"hadd -f {outfolder}/out_temp.root {outfolder}/out_{n}.root {outfolder}/out_cat.root")
      else: os.system(f"cp {outfolder}/out_{n}.root {outfolder}/out_temp.root")
    else:
      if n!=(1+startn): os.system(f"mv {outfolder}/out_cat.root {outfolder}/out_temp.root")
      os.system(f"hadd {outfolder}/out_cat.root {outfolder}/out_{n}.root {outfolder}/out_temp.root")

    print(f"plot-ing fragment {n}")
    if n==startn: os.system(f"root -x \"plot_monitor_h2.C(\\\"{outfolder}/out_temp.root\\\", \\\"{outfolder}/plot_last\\\")\"")
    else: os.system(f"root -x \"plot_monitor_h2.C(\\\"{outfolder}/out_cat.root\\\", \\\"{outfolder}/plot_last\\\")\"")
    print("\n\n")
    os.system(f"echo ready > {outfolder}/plotlock")
    n+=1
    time.sleep(sleep)
