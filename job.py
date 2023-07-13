import sys
import pandas as pd
import os

# args: 1=file, 2=nframmenti

def reco(row):
  os.system(f"python3 reco.py {row.nrun} {row.label} {row.board} {row.fragment}")

df = pd.read_csv(sys.argv[1], sep=" ", header=None)
df.columns = ["nrun", "label", "board", "fragment"]

print(df)

df.apply(lambda row: reco(row), axis=1)
