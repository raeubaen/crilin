import uproot
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin')

parser.add_argument('infilename', type=str, help='Input file name .root')
parser.add_argument('outfilename', type=str, help='outfile', default="")

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

intree = uproot.open(f"{infilename}:tree")

front_charge = intree["front_charge"].array(library="np")
back_charge = intree["back_charge"].array(library="np")

front_sum = front_charge.sum(axis=1)
back_sum = back_charge.sum(axis=1)

_x = np.asarray([int(i/2)%3-1 for i in range(18)])
x = np.repeat(_x[:, :, np.newaxis], front_charge.shape[0], axis=0)
_y = np.asarray([int(int(i/2)/3)-1 for i in range(18)])
y = np.repeat(_y[:, :, np.newaxis], front_charge.shape[0], axis=0)

front_centroid_x = (x*front_charge).sum(axis=1)/front_sum
front_centroid_y = (y*back_charge).sum(axis=1)/back_sum
