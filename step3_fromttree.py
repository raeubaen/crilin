# Reconstruction for crilin July (RawHisto output of Padme DAQ)
import json
import sys
import ROOT
import numpy as np
import argparse
import time
from scipy.signal import filtfilt, butter

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

def zero_all_vars(vars):
  for key in vars:
    var = vars[key]
    var *= 0

def tree_var(tree, name, shape, npvartype, rootvartype):
  dtype = npvartype
  var = np.zeros(shape, dtype=dtype)
  shape_str = "".join(["[%i]"%i for i in shape])
  tree.Branch(name, var, "%s%s/%s"%(name,shape_str,rootvartype))
  return var

ROOT.gErrorIgnoreLevel = ROOT.kFatal

parser = argparse.ArgumentParser(description='Online monitor and reconstruction for crilin July')

parser.add_argument('infile', type=str, help='Input file name .root')
parser.add_argument('outfile', type=str, help='outfile', default="")
parser.add_argument('label', type=str, help='label', default="")
parser.add_argument('frontboard', type=int, help='Board. in front', default=0)
parser.add_argument('--offset', type=int, help='Start event number', default=0)
parser.add_argument('--pythonversion', type=int, help='Python 2/3', default=3)
parser.add_argument('--maxevents', type=int, help='Number of events', default=100000)
parser.add_argument('--nsamples', type=int, help='Nsamples per waveform', default=1000)
parser.add_argument('--samplingrate', type=int, help='GHz sampling rate', default=5)
parser.add_argument('--boardsnum', type=int, help='Number of boards', default=2)
parser.add_argument('--chsnum', type=int, help='Number of channels per board', default=21)
parser.add_argument('--signalstart', type=int, help='Signal start (ADC ticks)', default=20)
parser.add_argument('--signalend', type=int, help='Signal end (ADC ticks)', default=190)
parser.add_argument('--debug', type=int, help='Plot zero-crossing check plots', default=0)
parser.add_argument('--chs', type=str, help='reco only ch list es. [1, 2, 3, 4]', default=0)
parser.add_argument('--zerocr_thr', type=float, help='Zerocr threshold', default=2)
parser.add_argument('--zerocr_cf', type=float, help='Zerocr CF', default=0.65)
parser.add_argument('--cindyzerocr_thr', type=float, help='Zerocr threshold', default=40)
parser.add_argument('--cindyzerocr_cf', type=float, help='Zerocr CF', default=0.85)
parser.add_argument('--trigger_thr', type=float, help='Zerocr threshold', default=70)
parser.add_argument('--check_timing', type=int, help='Zerocr Check if fails', default=0)
parser.add_argument('--lpfilter', type=int, help='150 MHz 4-order Butterworth active', default=1)
parser.add_argument('--applysinglepcut', type=int, help='reco only events passing single p. cut (cindy raw charge btw -110 and -40 (modifiable)', default=1)
parser.add_argument('--cindylowcut', type=float, help='Cindy low cut (def. 90 pC) on (Q1+Q2)/2', default=10)
parser.add_argument('--cindyhighcut', type=float, help='Cindy high cut (def. 10 pC) on (Q1+Q2)/2', default=90)
parser.add_argument('--charge_thr_for_crilin', type=float, help='Charge thr on crilin channels', default=6)
parser.add_argument('--random_trg', type=int, help='Random Trigger', default=0)
parser.add_argument('--rise_window_end', type=float, help='End of window where signal rise is accepted', default=60)
parser.add_argument('--rise_window_start', type=float, help='Start of window where signal rise is accepted', default=20)
parser.add_argument('--cindy_rise_window_end', type=float, help='End of window where signal rise is accepted', default=75)
parser.add_argument('--cindy_rise_window_start', type=float, help='Start of window where signal rise is accepted', default=35)
parser.add_argument('--trigger_rise_window_end', type=float, help='End of window where signal rise is accepted', default=170)
parser.add_argument('--trigger_rise_window_start', type=float, help='Start of window where signal rise is accepted', default=150)
parser.add_argument('--rise_min_points', type=int, help='Minimium number of points in the monotonic rise to accept the event', default=8)
parser.add_argument('--timingwithoutfilter', type=float, help='timingwithoutfilter', default=0)
parser.add_argument('--lpfreq', type=float, help='Low pass filter cut frequency (GHz)', default=0.5)
parser.add_argument('--pseudotime_cf', type=float, help='Low pass filter cut frequency (GHz)', default=0.11)
parser.add_argument('--zerocr', type=int, help='Evaluate Zerocrossing time', default=1)

args = parser.parse_args()
v = vars(args)
print(v)
vars().update(v)

outfile = args.outfile

bline_t_start = 0; bline_t_end = signalstart

outf = ROOT.TFile(outfile, "RECREATE")
outf.cd()
tree = ROOT.TTree("tree", "tree")
tree.SetAutoSave(1000)

with open("%s"%outfile.replace('root', 'json'), 'w') as fp:
    json.dump(vars(args), fp)

std_shape = (boardsnum, chsnum+4)

tree_vars = AttrDict()
tree_vars.update({
  "pre_signal_bline": tree_var(tree, "pre_signal_bline", std_shape, np.float32, "F"),
  "pre_signal_rms": tree_var(tree, "pre_signal_rms", std_shape, np.float32, "F"),
  "pedestal": tree_var(tree, "pedestal", std_shape, np.float32, "F"),
  "evnum": tree_var(tree, "evnum", (1,), np.int32, "I"),
  "charge": tree_var(tree, "charge", std_shape, np.float32, "F"),
  "ampPeak": tree_var(tree, "ampPeak", std_shape, np.float32, "F"),
  "timePeak": tree_var(tree, "timePeak", std_shape, np.float32, "F"),
  "timeAve": tree_var(tree, "timeAve", std_shape, np.float32, "F"),
  "wave": tree_var(tree, "wave", (std_shape[0], std_shape[1], nsamples), np.float32, "F"),
  "unfiltered_wave": tree_var(tree, "unfiltered_wave", (std_shape[0], std_shape[1], nsamples), np.float32, "F"),
  "tWave": tree_var(tree, "tWave", (nsamples,), np.float32, "F"),
  "chi2_zerocr": tree_var(tree, "chi2_zerocr", std_shape, np.float32, "F"),
  "time_zerocr": tree_var(tree, "time_zerocr", std_shape, np.float32, "F"),
  "sumcharge": tree_var(tree, "sumcharge", (boardsnum,), np.float32, "F"),
  "single_e_flag": tree_var(tree, "single_e_flag", (1,), np.int32, "I"),
  "time_pseudotime": tree_var(tree, "time_pseudotime", std_shape, np.float32, "F"),
  "time_pseudotime_corr": tree_var(tree, "time_pseudotime_corr", std_shape, np.float32, "F"),
  "time_trig": tree_var(tree, "time_trig", (boardsnum, 4), np.float32, "F"),
})

B_pb, A_pb = butter(2, [lpfreq/(samplingrate/2.)])

if args.chs != 0:
  chlist = [int(i) for i in args.chs.strip('][').split(', ')]
  if 19 not in chlist: chlist.append(19)
  if 20 not in chlist: chlist.append(20)
  chiter = chlist
else: chiter = list(range(chsnum))
for i in [3, 2, 1, 0]: chiter.insert(0, chsnum+i) #expects ntuple with chsnum+4 channels (last 4 are trigger)

#gestire canali trigger, vanno analizzati prima degli altri per sottrarre timing

f = ROOT.TFile(infile)
intree = f.Get("NTU")

t = np.arange(nsamples)/samplingrate

novalidrise = 0
failed = 0
no_zerocr = 0

for ev in range(maxevents):
  intree.GetEntry(ev+offset)
  if ev%int(maxevents/10)==0:
    print("Event: %i"%ev)

  to_discard = 1
  zero_all_vars(tree_vars)
  tree_vars.evnum[0] = ev+offset

  for board in range(boardsnum):
    for ch in chiter:

      if ch==18: continue
      if board == 0 and ch in [18, 19, 20]: mult = -1

      if ch>=chsnum:
        amp = np.asarray(intree.WavesTrig)[nsamples*4*board + (ch-chsnum)*nsamples : nsamples*4*board + (ch-chsnum+1)*nsamples]
      else:
        amp = np.asarray(intree.Waves)[nsamples*chsnum*board + ch*nsamples:nsamples*chsnum*board + (ch+1)*nsamples]

      #if sui canali trigger (ultimi 4 come numeri ma primi 4 del loop)
        #calcola le variabili per-chip che poi salva nell'albero e usa dopo per tutti gli altri canali

      virgin_amp = amp.copy()

      if lpfilter:
        amp = filtfilt(B_pb, A_pb, amp)

      pre_signal_index = np.logical_and(t > bline_t_start, t < bline_t_end)
      if np.sum(pre_signal_index) == 0:
        continue
      pre_signal_amp = amp[pre_signal_index]
      temp_pre_signal_bline = 0
      temp_pre_signal_rms = pre_signal_amp.std()
      temp_pedestal = pre_signal_amp[:-1].sum()  / (50 * samplingrate) / (signalstart-1) * (signalend - signalstart)

      signal_index = np.logical_and(t > signalstart, t < signalend)
      signal_amp = amp[signal_index]
      signal_t = t[signal_index]

      temp_charge = signal_amp.sum()  / (50 * samplingrate) # V * ns * 1e3 / ohm = pC

      if temp_charge < charge_thr_for_crilin:
        continue
      else:
        to_discard = 0

      if ch in [19, 20]:
        rise_ind = np.logical_and(t>cindy_rise_window_start, t<cindy_rise_window_end)
        thr, cf = cindyzerocr_thr, cindyzerocr_cf
      elif ch >= chsnum:
        rise_ind = np.logical_and(t>trigger_rise_window_start, t<trigger_rise_window_end)
        thr = trigger_thr
      else:
        rise_ind = np.logical_and(t>rise_window_start, t<rise_window_end)
        thr, cf = zerocr_thr, zerocr_cf

      rise_t = t[rise_ind]
      rise_amp = amp[rise_ind]
      overthr_ind = rise_amp > thr
      rise_t = rise_t[overthr_ind]
      rise_amp = rise_amp[overthr_ind]

      tree_vars.pre_signal_bline[board][ch] = temp_pre_signal_bline
      tree_vars.pre_signal_rms[board][ch] = temp_pre_signal_rms
      tree_vars.pedestal[board][ch] = temp_pedestal
      tree_vars.charge[board][ch] = temp_charge

      tree_vars.timeAve[board][ch] = (signal_amp*signal_t).sum() / signal_amp.sum()
      tree_vars.wave[board, ch, :] = amp
      tree_vars.tWave[:] = t

      if lpfilter: tree_vars.unfiltered_wave[board, ch, :] = virgin_amp

      novalidrise = 0

      monotone_rise_ind_groups = np.split(np.arange(len(rise_amp)), np.where(np.diff(rise_amp) < 0)[0]+1)
      monotone_rise_ind = []
      for group in monotone_rise_ind_groups:
        if len(group) > rise_min_points:
          monotone_rise_ind = group
          break

      if len(monotone_rise_ind)==0:
        novalidrise = 1
        tree_vars.ampPeak[board][ch] = -99
        tree_vars.timePeak[board][ch] = -99
        tree_vars.time_zerocr[board][ch] = -99
        tree_vars.time_pseudotime[board][ch] = -99
      else:
        firstind = monotone_rise_ind[0]
        lastind = monotone_rise_ind[-1]
        monotone_rise_t = rise_t[firstind:lastind+4]
        monotone_rise_amp = rise_amp[firstind:lastind+4]
        tree_vars.ampPeak[board][ch] = monotone_rise_amp.max()
        tree_vars.timePeak[board][ch] = monotone_rise_t[monotone_rise_amp.argmax()]

        no_zerocr = 0;
        failed = 0

        try:
          tstart_zerocr = monotone_rise_t[0]
          if ch >= chsnum: tend_zerocr = monotone_rise_t[0] + 20
          else: tend_zerocr = monotone_rise_t[monotone_rise_amp>cf*tree_vars.ampPeak[board][ch]][0]
        except IndexError:
          if check_timing: no_zerocr = 1
        else:
          if not args.timingwithoutfilter:
            g = ROOT.TGraphErrors(nsamples, t.astype(np.float64), amp.astype(np.float64), np.zeros(nsamples,), np.ones(nsamples,)*temp_pre_signal_rms)
          else:
            g = ROOT.TGraphErrors(nsamples, t.astype(np.float64), virgin_amp.astype(np.float64), np.zeros(nsamples,), np.ones(nsamples,)*temp_pre_signal_rms)

          if zerocr:
            func = ROOT.TF1("func", "pol1", tstart_zerocr, tend_zerocr)
            g.Fit(func, "RQ")
            tree_vars.chi2_zerocr[board][ch] = func.GetChisquare()
            f_recovery = ROOT.TF1("f_recovery", "pol1", tstart_zerocr-50, tend_zerocr)
            f_recovery.SetParameters(func.GetParameters())
            x_zerocr = f_recovery.GetX(0)
            if ROOT.TMath.IsNaN(x_zerocr):
              x_zerocr = -99
              if check_timing: failed = 1
            tree_vars.time_zerocr[board][ch] = x_zerocr

          wsp = ROOT.TSpline5("wsp", g);

          if pythonversion==3:
            spf = lambda x, par: wsp.Eval(x[0])
          else:
            spf = lambda x: wsp.Eval(x[0])
          sptf1 = ROOT.TF1("spf", spf, tstart_zerocr-20, tend_zerocr);

          try:
            if ch >= chsnum: x_pseudot = sptf1.GetX(thr)
            else: x_pseudot = sptf1.GetX(pseudotime_cf*tree_vars.ampPeak[board][ch])

            if ROOT.TMath.IsNaN(x_pseudot):
              x_pseudot = -99
              if check_timing: failed = 1
          except:
              x_pseudot = -99
              if check_timing: failed = 1

          tree_vars.time_pseudotime[board][ch] = x_pseudot
          if ch >= chsnum: tree_vars.time_trig[board][ch-chsnum] = x_pseudot
          else: tree_vars.time_pseudotime_corr[board][ch] = x_pseudot - tree_vars.time_trig[board][int(ch/8)]

      if debug or (check_timing and (failed or no_zerocr or novalidrise)):
        print(
          "Event: ", ev,
          ", Board: ", board,
          ", Channel: ", ch,
          ", Tstart: ", 0 if novalidrise else tstart_zerocr,
          ", Tend: ", 0 if novalidrise else tend_zerocr,
          ", Timepeak: ", tree_vars.timePeak[board][ch],
          ", Amppeak: ", tree_vars.ampPeak[board][ch],
          ", ZerocrTime: ", tree_vars.time_zerocr[board][ch],
          ", ZerocrChi2: ", tree_vars.chi2_zerocr[board][ch],
          ", Charge: ", tree_vars.charge[board][ch],
          ", Failed GetX: ", failed,
          ", No_zerocr: ", no_zerocr,
          ", Novalidrise: ", novalidrise
        )
        c = ROOT.TCanvas("c")
        if novalidrise or no_zerocr:
          g = ROOT.TGraphErrors(nsamples, t.astype(np.float64), amp.astype(np.float64), np.zeros(nsamples,), np.ones(nsamples,)*temp_pre_signal_rms)
          g.SetMarkerStyle(20)
          g.SetMarkerSize(.7)
          g.Draw("AP")
        else:
          g.SetMarkerStyle(20)
          g.SetMarkerSize(.7)
          g.Draw("AP")
          if not no_zerocr:
            wsp.Draw("same")
            sptf1.Draw("same")
            sptf1.SetLineColor(ROOT.kGreen)

        input()

    cindymeancharge = (tree_vars.charge[0][19] + tree_vars.charge[0][20])/2
    tree_vars.single_e_flag[0] = (cindymeancharge < cindyhighcut) and (cindymeancharge > cindylowcut)

    crilin_charges = tree_vars.charge[board][0:18]
    crilin_charges = crilin_charges[crilin_charges > charge_thr_for_crilin]
    tree_vars.sumcharge[board] = crilin_charges.sum()

  if not (applysinglepcut and tree_vars.single_e_flag[0]==0):
    if not to_discard:
      tree.Fill()

outf.cd()
tree.Write()
outf.Close()
f.Close()
