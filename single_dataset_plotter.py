#python3

#questo fa un dataset solo (anche molti file) ma una sola tchain

#va chiamato da un'altro programma lasciando plot.conf costante e variando data.conf per fare tutti i dataset in batch con gli stessi plot e gli stessi tagli

import ROOT
import sys
import pandas as pd
import os
import argparse

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin July')

parser.add_argument('plotconffile', type=str, help='plotconffile')
parser.add_argument('dataconffile', type=str, help='dataconffile')
parser.add_argument('outputfolder', type=str, help='outfolder')
parser.add_argument('--applysingleecut', type=int, help='Single particle cut', default=1)

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)


macro = [] #x elisa: root logon

def plot(row, chain, outputfolder):
  name = row['name']
  print(f"{outputfolder}/{name}.root")
  f = ROOT.TFile(f"{outputfolder}/{name}.root", "recreate")
  f.cd()
  c = ROOT.TCanvas(f"{name}_canvas")
  c.cd()
  if str(row.cuts) == "": cut = "1"
  else: cut = str(row.cuts)
  cut = cut + " && single_e_flag==1"
  if str(row.y).strip()=="0":
    h = ROOT.TH1F(f"{name}", f"{row.title}", int(row.binsnx), float(row.binsminx), float(row.binsmaxx))
    chain.Draw(f"{row.x}>>{name}", f"{cut}")
    h.SetLineColor(eval(f"ROOT.{row.color}"))
  else:
    h = ROOT.TH2F(f"{name}", f"{row.title}", int(row.binsnx), float(row.binsminx), float(row.binsmaxx), int(row.binsny), float(row.binsminy), float(row.binsmaxy))
    chain.Draw(f"{row.y}:{row.x}>>{name}", f"{cut}", "zcol")
  h.GetYaxis().SetTitle(f"{row.ylabel}")
  h.GetXaxis().SetTitle(f"{row.xlabel}")
  c.SaveAs(f"{outputfolder}/{name}.png")
  c.Write()
  h.Write()
  f.Close()

def add(chain, row):
  lst = os.popen(f"/bin/bash -c 'ls -1 {row.filename.strip()}'").read().split("\n")
  for file in lst:
    chain.Add(f"{file}/{row.treename.strip()}")

dataconf_df = pd.read_csv(dataconffile)

for m in macro: ROOT.gROOT.LoadMacro(m)

chain = ROOT.TChain()

dataconf_df.apply(lambda row: add(chain, row), axis=1)

plotconf_df = pd.read_csv(plotconffile)
plotconf_df.apply(lambda row: plot(row, chain, outputfolder), axis=1)
