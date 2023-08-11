import cupy as cp
from cupyx.scipy import ndimage

def get_reco_products(waves, signal_start, signal_end, rise_end, charge_thr, sampling_rate, nsamples, cf, adc_to_mv_factor, save_waves):
  #waves has shape (nevents, chs, nsamples) - serie e parallelo separati
  pre_signal = waves[:, :, :int(signal_start*sampling_rate)]
  pre_signal_bline = pre_signal.mean(axis=2)
  pre_signal_rms = pre_signal.std(axis=2)

  waves = waves - cp.repeat(pre_signal_bline[:, :, cp.newaxis], nsamples, axis=2)

  del pre_signal
  cp.get_default_memory_pool().free_all_blocks()
  cp.get_default_pinned_memory_pool().free_all_blocks()

  signal = waves[:, :, int(signal_start*sampling_rate):int(signal_end*sampling_rate)]

  if not save_waves:
    del waves

  cp.get_default_memory_pool().free_all_blocks()
  cp.get_default_pinned_memory_pool().free_all_blocks()

  charge = signal.sum(axis=2) / (50 * sampling_rate)  * adc_to_mv_factor
  charge[charge<charge_thr] = 0

  rise = signal[:, :, :int((rise_end-signal_start)*sampling_rate)]

  del signal
  cp.get_default_memory_pool().free_all_blocks()
  cp.get_default_pinned_memory_pool().free_all_blocks()

  rise_interp = ndimage.zoom(rise, [1, 1, 20])

  del rise
  cp.get_default_memory_pool().free_all_blocks()
  cp.get_default_pinned_memory_pool().free_all_blocks()

  ampPeak = rise_interp.max(axis=2)
  time_peak = rise_interp.argmax(axis=2)/(sampling_rate*20)

  pseudo_t = cp.argmax(rise_interp > cp.repeat((ampPeak*cf)[:, :, cp.newaxis], rise_interp.shape[2], axis=2), axis=2)/(sampling_rate*20)
  ampPeak *= adc_to_mv_factor
  reco_dict = {"pre_signal_bline,": pre_signal_bline, "pre_signal_rms": pre_signal_rms, "charge": charge, "ampPeak": ampPeak, "time_peak": time_peak, "pseudo_t": pseudo_t}
  if save_waves:  reco_dict.update({"wave": waves})
  return reco_dict
