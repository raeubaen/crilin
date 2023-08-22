import os
import sys
import argparse 
import pandas as pd
import glob
import uproot
import numpy as np
import multiprocessing
import subprocess

def merge(outpath):
  mergeffilename = outpath.split("/")[-1]
  os.system("rm {outpath}/{mergeffilename}_merged.root")
  os.system(F"hadd {outpath}/{mergeffilename}_merged.root {outpath}/{mergeffilename}_*.root")
