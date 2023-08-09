import json
import sys
import uproot
import cupy as cp
import argparse
import time
import pandas as pd
import gpu_routines

def get_reco_products(waves, signal_start, signal_end, rise_end, charge_thr, sampling_rate, nsamples, cf):
  #waves has shape (nevents, chs, nsamples) - serie e parallelo separati
  pre_signal = waves[:, :, :int(signal_start*signal_rate)]
  pre_signal_bline = pre_signal.mean(axis=2)
  pre_signal_rms = pre_signal.std(axis=2)

  waves = waves - np.repeat(pre_signal_bline[:, :, np.newaxis], nsamples, axis=2)

  signal = waves[:, :, int(signal_start*signal_rate), int(signal_end*signal_rate)]
  charge = signal.sum(axis=2)
  charge[charge<charge_thr] = 0


  rise = signal[:, :, :int((rise_end-signal_start)*sampling_rate)]

  interp_mesh = np.asarray(np.meshgrid(np.arange(rise.shape[0]), np.arange(rise.shape[1]), np.arange(rise.shape[2]*20)/20.)) #10 ps step - se sampling_rate è 5Ghz
  interp_points = np.rollaxis(interp_mesh, 0, 4)
  interp_points = interp_points.reshape((interp_mesh.size // 3, 3))
  rise_interp = scipy.interpolate.interpn((np.arange(rise.shape[0]), np.arange(rise.shape[1]), np.arange(rise.shape[2])), rise, interp_points, method="cubic", bounds_error=False)
  amp_peak = signal.max(axis=2)
  time_peak = signal.argmax(axis=2)/sampling

  pseudo_t = np.argmax(rise_interp > amp_peak*cf, axis=2)
  return {"pre_signal_bline,": pre_signal_bline, "pre_signal_rms": pre_signal_rms, "charge": charge, "ampPeak": ampPeak, "time_peak": time_peak, "pseudo_t": pseudo_t}

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin')

parser.add_argument('infilename', type=str, help='Input file name .root')
parser.add_argument('outfilename', type=str, help='outfile', default="")
parser.add_argument('label', type=str, help='label', default="")
parser.add_argument('frontboard', type=int, help='Board. in front', default=0)
parser.add_argument('offset', type=int, help='Start event number', default=0)
parser.add_argument('maxevents', type=int, help='Number of events', default=100000)
parser.add_argument('--nsamples', type=int, help='Nsamples per waveform', default=1024)
parser.add_argument('--samplingrate', type=int, help='GHz sampling rate', default=5)
parser.add_argument('--chsnum', type=int, help='Number of channels per board', default=21)
parser.add_argument('--seriessignalstart', type=int, help='Series Signal start (ns)', default=20)
parser.add_argument('--seriessignalend', type=int, help='Series Signal end (ns)', default=100)
parser.add_argument('--seriesriseend', type=int, help='Series Peak position + ~10 ns (ns)', default=100)
parser.add_argument('--parallelsignalstart', type=int, help='Parallel Signal start (ns)', default=20)
parser.add_argument('--parallelsignalend', type=int, help='Parallel Signal end (ns)', default=190)
parser.add_argument('--parallelriseend', type=int, help='Parallel Peak position + ~10 ns (ns)', default=190)
parser.add_argument('--cindysignalstart', type=int, help='Cindy Signal start (ns)', default=35)
parser.add_argument('--cindyriseend', type=int, help='Cindy Peak position + ~10 ns (ns)', default=60)
parser.add_argument('--cindysignalend', type=int, help='Cindy Signal end (ns)', default=85)
parser.add_argument('--triggersignalstart', type=int, help='Trigger Signal start (ns)', default=140)
parser.add_argument('--triggersignalend', type=int, help='Trigger Signal end (ns)', default=175)
parser.add_argument('--trigger_thr_start', type=float, help='Fixed threshold for trigger timing (start) mV', default=50)
parser.add_argument('--trigger_thr_end', type=float, help='Fixed threshold for trigger timing (end) mV', default=250)
parser.add_argument('--applysinglepcut', type=int, help='reco only events passing single p. cut (cindy raw charge mean btw 10 and 90 (modifiable)', default=0)
parser.add_argument('--cindylowcutsx', type=float, help='Cindy low cut on chargesx', default=50)
parser.add_argument('--cindyhighcutsx', type=float, help='Cindy high cut on chargesx', default=90)
parser.add_argument('--cindylowcutdx', type=float, help='Cindy low cut on chargedx', default=30)
parser.add_argument('--cindyhighcutdx', type=float, help='Cindy high cut on chargedx', default=70)
parser.add_argument('--charge_thr_for_series', type=float, help='Charge thr on crilin series channels', default=2)
parser.add_argument('--charge_thr_for_parallel', type=float, help='Charge thr on crilin parallel channels', default=5)
parser.add_argument('--charge_thr_for_cindy', type=float, help='Charge thr on cindy channels', default=10)
parser.add_argument('--seriespseudotime_cf', type=float, help='Pseudotime CF', default=0.11)
parser.add_argument('--parallelpseudotime_cf', type=float, help='Pseudotime CF', default=0.11)
parser.add_argument('--cindypseudotime_cf', type=float, help='Pseudotime CF', default=0.05)
parser.add_argument('--centroid_square_cut_thr', type=float, help='Threshold in mm on abs centroid x and y', default=2.5)
parser.add_argument('--rmscut', type=float, help='cut on pre signal rms (mV)', default=1.5)
parser.add_argument('--saveallwave', type=int, help='save all waves', default=0)
parser.add_argument('--ch_cindysx', type=int, help='sx cindy channel n', default=19)
parser.add_argument('--ch_cindydx', type=int, help='dx cindy channel n', default=20)

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

with open("%s"%outfilename.replace('.root', '.json'), 'w') as fp:
    json.dump(vars(args), fp)

intree = uproot.open(f"{infilename}:t")
nevents = min(intree.num_entries, maxevents)

cindy_waves = cp.zeros((nevents, 2, nsamples))
cindy_waves[:, 0, :] = cp.asarray(intree[f"wave{ch_cindysx}"].array(library="np"))
cindy_waves[:, 1, :] = cp.asarray(intree[f"wave{ch_cindydx}"].array(library="np"))

cindy_reco = gpu_routines.get_reco_products(cindy_waves, cindysignalstart, cindysignalend, cindyriseend, charge_thr_for_cindy, nsamples, cindypseudotime_cf)

trigger_waves = cp.zeros((nevents, 4, nsamples)) #veramente 4??
#trigger_reco = gpu_routines.get_trigger_reco(trigger_waves, triggersignalstart, triggersignalend, trigger_thr_start, trigger_thr_end) #zero crossing con pol2 - chiedere a elisa

crilin_waves = cp.zeros((nevents, 2, 18, nsamples))
map = pd.read_csv("h2_crilin_map.csv")
for index, row in map.iterrows():
  crilin_waves[:, row.board, row.ch, :] = cp.asarray(intree[f"wave{row.daqch}"].array(library="np"))

series_board_reco = gpu_routines.get_reco_products(crilin_waves[:, 0, :, :], seriessignalstart, seriessignalend, seriesriseend, charge_thr_for_series, nsamples, seriespseudotime_cf)
parallel_board_reco = gpu_routines.get_reco_products(crilin_waves[:, 1, :, :], parallelsignalstart, parallelsignalend, parallelriseend, charge_thr_for_parallel, nsamples, parallelpseudotime_cf)

if frontboard == 0:
  front_board_reco = series_board_reco
  back_board_reco = parallel_board_reco
else:
  front_board_reco = parallel_board_reco
  back_board_reco = series_board_reco

times = cp.arange(0, 1024)/sampling_rate

outfile = uproot.recreate(outfilename)

reco_sets = ["cindy": cindy_reco, "front": front_board_reco, "back": back_board_reco] #, "trigger", trigger_reco]

reco_dict = {}
for set_key in reco_sets:
  for branch_key in reco_sets[set_key]:
    reco_dict.update(f{}_{}": reco_sets[set_key][branch_key].get())

outfile["tree"] = {reco_dict}
