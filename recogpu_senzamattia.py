import json
import uproot
import cupy as cp
import argparse
import pandas as pd
import gpu_routines

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
parser.add_argument('--seriesriseend', type=int, help='Series max Peak position + ~20 ns (ns)', default=60)
parser.add_argument('--parallelsignalstart', type=int, help='Parallel Signal start (ns)', default=15)
parser.add_argument('--parallelsignalend', type=int, help='Parallel Signal end (ns)', default=190)
parser.add_argument('--parallelriseend', type=int, help='Parallel max Peak position + ~20 ns (ns)', default=60)
parser.add_argument('--cindysignalstart', type=int, help='Cindy Signal start (ns)', default=35)
parser.add_argument('--cindyriseend', type=int, help='Cindy max Peak position + ~20 ns (ns)', default=60)
parser.add_argument('--cindysignalend', type=int, help='Cindy Signal end (ns)', default=85)
parser.add_argument('--triggersignalstart', type=int, help='Trigger Si gnal start (ns)', default=140)
parser.add_argument('--triggersignalend', type=int, help='Trigger Signal end (ns)', default=175)
parser.add_argument('--trigger_thr_start', type=float, help='Fixed threshold for trigger timing (start) mV', default=50)
parser.add_argument('--trigger_thr_end', type=float, help='Fixed threshold for trigger timing (end) mV', default=250)
parser.add_argument('--charge_thr_for_series', type=float, help='Charge thr on crilin series channels', default=0.1) #2
parser.add_argument('--charge_thr_for_parallel', type=float, help='Charge thr on crilin parallel channels', default=0.1) #5
parser.add_argument('--charge_thr_for_cindy', type=float, help='Charge thr on cindy channels', default=0.1)
parser.add_argument('--seriespseudotime_cf', type=float, help='Pseudotime CF', default=0.11)
parser.add_argument('--parallelpseudotime_cf', type=float, help='Pseudotime CF', default=0.11)
parser.add_argument('--cindypseudotime_cf', type=float, help='Pseudotime CF', default=0.05)
parser.add_argument('--save_waves', type=int, help='save all waves', default=0)
parser.add_argument('--ch_cindysx', type=int, help='sx cindy channel n', default=2)
parser.add_argument('--ch_cindydx', type=int, help='dx cindy channel n', default=3)
parser.add_argument('--ch_cindycopy', type=int, help='copy cindy channel n', default=50)

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

with open("%s"%outfilename.replace('.root', '.json'), 'w') as fp:
    json.dump(vars(args), fp)

digi0 = uproot.open(f"{infilename}:h3")
digi1 = uproot.open(f"{infilename}:h4")

nevents = min(digi0.num_entries, maxevents)

digi0_waves = cp.asarray(digi0["Idigi_742a"].array(library="np")[offset:offset+nevents, :]).astype(cp.float64)*2000/4096
digi1_waves = cp.asarray(digi1["Idigi_742b"].array(library="np")[offset:offset+nevents, :]).astype(cp.float64)*1000/4096

cindy_waves = cp.zeros((nevents, 2, nsamples))
cindy_waves[:, 0, :] = digi0_waves[:, (nsamples+7)*ch_cindysx + 5 : (nsamples+7)*(ch_cindysx+1) - 2]*(-1)
cindy_waves[:, 1, :] = digi0_waves[:, (nsamples+7)*ch_cindydx + 5 :(nsamples+7)*(ch_cindydx+1) -2 ]*(-1)

cindy_reco = gpu_routines.get_reco_products(cindy_waves, cindysignalstart, cindysignalend, cindyriseend, charge_thr_for_cindy, samplingrate, nsamples, cindypseudotime_cf, save_waves)

'''
trigger_waves = cp.zeros((nevents, 4, nsamples)) #veramente 4??
trigger_reco = gpu_routines.get_trigger_reco(trigger_waves, triggersignalstart, triggersignalend, trigger_thr_start, trigger_thr_end, adc_to_mv_factor, save_waves) #zero crossing con pol2 - chiedere a elisa
'''

series_waves = cp.zeros((nevents, 18, nsamples))
parallel_waves = cp.zeros((nevents, 18, nsamples))
map = pd.read_csv("h2_crilin_map.csv")
_front_digirange = (2-(map[map.board==frontboard].daqch > 31).astype("int").to_numpy())*1000
_back_digirange = (2-(map[map.board==1-frontboard].daqch > 31).astype("int").to_numpy())*1000
front_digirange = cp.repeat(_front_digirange[cp.newaxis, :], nevents, axis=0)
back_digirange = cp.repeat(_back_digirange[cp.newaxis, :], nevents, axis=0)

for index, row in map.iterrows():
  if row.board==0:
    if row.daqch<32:
      series_waves[:, row.ch, :] = digi0_waves[:, (nsamples+7)*row.daqch+5:(nsamples+7)*(row.daqch+1)-2]
    else:
      series_waves[:, row.ch, :] = digi1_waves[:, (nsamples+7)*(row.daqch-32)+5:(nsamples+7)*(row.daqch+1-32)-2]
  else:
    if row.daqch<32:
      parallel_waves[:, row.ch, :] = digi0_waves[:, (nsamples+7)*row.daqch+5:(nsamples+7)*(row.daqch+1)-2]
    else:
      parallel_waves[:, row.ch, :] = digi1_waves[:, (nsamples+7)*(row.daqch-32)+5:(nsamples+7)*(row.daqch+1-32)-2]

series_board_reco = gpu_routines.get_reco_products(series_waves, seriessignalstart, seriessignalend, seriesriseend, charge_thr_for_series, samplingrate, nsamples, seriespseudotime_cf, save_waves)
del series_waves
cp.get_default_memory_pool().free_all_blocks()
cp.get_default_pinned_memory_pool().free_all_blocks()

parallel_board_reco = gpu_routines.get_reco_products(parallel_waves, parallelsignalstart, parallelsignalend, parallelriseend, charge_thr_for_parallel, samplingrate, nsamples, parallelpseudotime_cf, save_waves)
del parallel_waves
cp.get_default_memory_pool().free_all_blocks()
cp.get_default_pinned_memory_pool().free_all_blocks()

if frontboard == 0:
  front_board_reco = series_board_reco
  back_board_reco = parallel_board_reco
else:
  front_board_reco = parallel_board_reco
  back_board_reco = series_board_reco

reco_sets = {"front": front_board_reco, "back": back_board_reco, "cindy": cindy_reco}
reco_dict = {}
for set_key in reco_sets:
  for branch_key in reco_sets[set_key]:
    reco_dict.update({f"{set_key}_{branch_key}": reco_sets[set_key][branch_key].get()})

if save_waves:
  times = cp.arange(0, 1024, 1/float(samplingrate))
  times = cp.repeat(times[cp.newaxis, :], nevents, axis=0)
  reco_dict.update({"tWave": times})

#evnum = cp.arange(offset, offset+nevents)

reco_dict.update({"front_digirange": front_digirange, "back_digirange": back_digirange})

outfile = uproot.recreate(outfilename)
outfile["tree"] = reco_dict

outfile.close()
