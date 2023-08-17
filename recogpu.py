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
parser.add_argument('--seriesriseend', type=int, help='Series Peak position + ~10 ns (ns)', default=60)
parser.add_argument('--parallelsignalstart', type=int, help='Parallel Signal start (ns)', default=15)
parser.add_argument('--parallelsignalend', type=int, help='Parallel Signal end (ns)', default=190)
parser.add_argument('--parallelriseend', type=int, help='Parallel Peak position + ~10 ns (ns)', default=60)
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
parser.add_argument('--charge_thr_for_series', type=float, help='Charge thr on crilin series channels', default=0.1) #2
parser.add_argument('--charge_thr_for_parallel', type=float, help='Charge thr on crilin parallel channels', default=0.1) #5
parser.add_argument('--charge_thr_for_cindy', type=float, help='Charge thr on cindy channels', default=10)
parser.add_argument('--seriespseudotime_cf', type=float, help='Pseudotime CF', default=0.11)
parser.add_argument('--parallelpseudotime_cf', type=float, help='Pseudotime CF', default=0.11)
parser.add_argument('--cindypseudotime_cf', type=float, help='Pseudotime CF', default=0.05)
parser.add_argument('--centroid_square_cut_thr', type=float, help='Threshold in mm on abs centroid x and y', default=2.5)
parser.add_argument('--rmscut', type=float, help='cut on pre signal rms (mV)', default=1.5)
parser.add_argument('--save_waves', type=int, help='save all waves', default=0)
parser.add_argument('--ch_cindysx', type=int, help='sx cindy channel n', default=2)
parser.add_argument('--ch_cindydx', type=int, help='dx cindy channel n', default=3)
parser.add_argument('--ch_cindycopy', type=int, help='copy cindy channel n', default=50)
parser.add_argument('--seriesadc_to_mv_factor', type=float, help='adc->mV factor', default=0.488) #2V = 4096 counts
parser.add_argument('--paralleladc_to_mv_factor', type=float, help='adc->mV factor', default=0.244) #1V = 4096 counts
parser.add_argument('--cindyadc_to_mv_factor', type=float, help='adc->mV factor', default=0.488) #2V = 4096 counts

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

with open("%s"%outfilename.replace('.root', '.json'), 'w') as fp:
    json.dump(vars(args), fp)

intree = uproot.open(f"{infilename}:t")
nevents = min(intree.num_entries, maxevents)

cindy_waves = cp.zeros((nevents, 3, nsamples))
cindy_waves[:, 0, :] = cp.asarray(intree[f"wave{ch_cindysx}"].array(library="np")[offset:offset+nevents, :])
cindy_waves[:, 1, :] = cp.asarray(intree[f"wave{ch_cindydx}"].array(library="np")[offset:offset+nevents, :])
cindy_waves[:, 2, :] = cp.asarray(intree[f"wave{ch_cindycopy}"].array(library="np")[offset:offset+nevents, :])/2 #sta sull'altro digitizer

cindy_reco = gpu_routines.get_reco_products(cindy_waves, cindysignalstart, cindysignalend, cindyriseend, charge_thr_for_cindy, nsamples, cindypseudotime_cf, cindyadc_to_mv_factor, save_waves)

'''
trigger_waves = cp.zeros((nevents, 4, nsamples)) #veramente 4??
trigger_reco = gpu_routines.get_trigger_reco(trigger_waves, triggersignalstart, triggersignalend, trigger_thr_start, trigger_thr_end, adc_to_mv_factor, save_waves) #zero crossing con pol2 - chiedere a elisa
'''

series_waves = cp.zeros((nevents, 18, nsamples))
parallel_waves = cp.zeros((nevents, 18, nsamples))
map = pd.read_csv("h2_crilin_map.csv")
for index, row in map.iterrows():
  if row.board==0:
    series_waves[:, row.ch, :] = cp.asarray(intree[f"wave{row.daqch}"].array(library="np")[offset:offset+nevents, :])
  else:
    parallel_waves[:, row.ch, :] = cp.asarray(intree[f"wave{row.daqch}"].array(library="np")[offset:offset+nevents, :])

series_board_reco = gpu_routines.get_reco_products(series_waves, seriessignalstart, seriessignalend, seriesriseend, charge_thr_for_series, samplingrate, nsamples, seriespseudotime_cf, seriesadc_to_mv_factor, save_waves)
del series_waves
cp.get_default_memory_pool().free_all_blocks()
cp.get_default_pinned_memory_pool().free_all_blocks()

parallel_board_reco = gpu_routines.get_reco_products(parallel_waves, parallelsignalstart, parallelsignalend, parallelriseend, charge_thr_for_parallel, samplingrate, nsamples, parallelpseudotime_cf, paralleladc_to_mv_factor, save_waves)
del parallel_waves
cp.get_default_memory_pool().free_all_blocks()
cp.get_default_pinned_memory_pool().free_all_blocks()

if frontboard == 0:
  front_board_reco = series_board_reco
  back_board_reco = parallel_board_reco
else:
  front_board_reco = parallel_board_reco
  back_board_reco = series_board_reco

reco_sets = {"front": front_board_reco, "back": back_board_reco} #, "trigger", trigger_reco, "cindy": cindy_reco]
reco_dict = {}
for set_key in reco_sets:
  for branch_key in reco_sets[set_key]:
    reco_dict.update({f"{set_key}_{branch_key}": reco_sets[set_key][branch_key].get()})

if save_waves:
  times = cp.arange(0, 1024, 1/float(samplingrate))
  times = cp.repeat(times[cp.newaxis, :], nevents, axis=0)
  reco_dict.update({"tWave": times})

#evnum = cp.arange(offset, offset+nevents)

#reco_dict.update({"evnum": evnum})

outfile = uproot.recreate(outfilename)
outfile["tree"] = reco_dict

outfile.close()
