import os
import sys
import argparse 


inpath = "/eos/user/d/dpaesani/data/H2_23/merged/run700252.root"
outpath = "/eos/user/d/dpaesani/data/H2_23/reco/deleteme"


os.system(F"python3 reco.py 0 1000 ele {inpath} {outpath}")




