import cupy as cp

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
