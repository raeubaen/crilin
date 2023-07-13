import ROOT
import scipy.signal
import matplotlib.pyplot as plt
from tqdm import tqdm
import sys
import numpy as np
from scipy.signal import iirnotch, filtfilt, butter

infile = ROOT.TFile(sys.argv[1])
tree = infile.Get("tree")

triter = iter(tree)

entry = next(triter)

arr = np.asarray(entry.wave)

fnoise, Snoise = scipy.signal.welch(arr[3*1024:4*1024], 5, nperseg=1024)
fsignal, Ssignal = scipy.signal.welch(arr[33*1024:34*1024], 5, nperseg=1024)

B_pb, A_pb = butter(4, [0.15], fs=5)

for entry in tqdm(tree):

  arr = np.asarray(entry.wave)

  noise = arr[3*1024:4*1024]
  signal = arr[33*1024:34*1024]

  #noise = filtfilt(B_pb, A_pb, noise)
  #signal = filtfilt(B_pb, A_pb, signal)

  ftemp, Stemp = scipy.signal.welch(noise, 5, nperseg=1024)
  Snoise+= Stemp
  ftemp, Stemp = scipy.signal.welch(signal, 5, nperseg=1024)
  Ssignal+=Stemp

plt.plot(fnoise, Snoise)
plt.plot(fsignal, Ssignal)
plt.yscale("log")
plt.show()

