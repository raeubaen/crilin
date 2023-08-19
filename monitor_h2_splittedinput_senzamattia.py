import os
import argparse
import time
import uproot

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin')

parser.add_argument('infilename', type=str, help='Input file name before underscore (.root)')
parser.add_argument('outfolder', type=str, help='outfolder', default="")
parser.add_argument('label', type=str, help='label', default="")
parser.add_argument('frontboard', type=int, help='Board. in front', default=0)
parser.add_argument('--startn', type=int, help='skip n fragments', default=0)
parser.add_argument('--cat', type=int, help='concatenate last .cat file when startn!=0', default=0)
parser.add_argument('--sleep', type=int, help='sleep between fragments', default=0)
parser.add_argument('--fragsize', type=int, help='events per fragment', default=1000) #fino a 10k ci entra

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

procs = []
n = startn

os.system(f"mkdir {outfolder}")

while True:
    print(f"reco-ing fragment {n+1}")
    try:
      du_out = os.popen(f"du -B k {infilename}_{n+1:05d}.root")
      du_size_kb = float(du_out.read().split("K")[0])
      if du_size_kb < 8:
        raise ValueError("du wrong")
      ret = os.system(f"python3 recogpu_senzamattia.py {infilename}_{n+1:05d}.root {outfolder}/out_{n+1}.root {label} {frontboard} 0 {fragsize}")
      if ret!=0: raise ValueError("no reco")
    except:
      print(f"fragment {n+1} under 8 kB - retrying")
      #os.system(f"cp gpu_empty_reco_tree.root {outfolder}/out_{n+1}.root")
      continue

    print(f"hadd-ing fragment {n+1}")
    if n==startn:
      if cat and startn>0: os.system(f"hadd -f {outfolder}/out_temp.root {outfolder}/out_{n+1}.root {outfolder}/out_cat.root")
      else: os.system(f"cp {outfolder}/out_{n+1}.root {outfolder}/out_temp.root")
    else:
      if n!=(1+startn): os.system(f"mv {outfolder}/out_cat.root {outfolder}/out_temp.root")
      os.system(f"hadd {outfolder}/out_cat.root {outfolder}/out_{n+1}.root {outfolder}/out_temp.root")

    print(f"plot-ing fragment {n+1}")
    if n==startn: os.system(f"root -x \"plot_monitor_h2.C(\\\"{outfolder}/out_temp.root\\\", \\\"{outfolder}/plot_last\\\")\"")
    else: os.system(f"root -x \"plot_monitor_h2.C(\\\"{outfolder}/out_cat.root\\\", \\\"{outfolder}/plot_last\\\")\"")
    print("\n\n")
    os.system(f"echo ready > {outfolder}/plotlock")
    n+=1
    time.sleep(sleep)
