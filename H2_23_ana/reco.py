from ROOT import *
from WaveReco import WaveReco
import argparse
import uproot

# arguments #################################################################################################################################################################

parser = argparse.ArgumentParser(description='reco wave')

parser.add_argument('procid',     type=int,   default=-1)
parser.add_argument('type',       type=str,   default="")
parser.add_argument('input',      type=str,   default="") #placeholder si valuta con numer spill
parser.add_argument('output',     type=str,   default="")
parser.add_argument('list',       type=str,   default="") #placeholder si valuta con procid

parser.add_argument('--opts',     type=str,   default="")
parser.add_argument('--tag',      type=str,   default="")
parser.add_argument('--dry',      type=bool,  default=0)
parser.add_argument('--nspecs',   type=int,   default=10)
parser.add_argument('--evtp',     type=int,   default=-1)

args = parser.parse_args()

# parameters #################################################################################################################################################################

wr = WaveReco()

wr.inFileName =     None
wr.outFileName =    f"{args.output}_{args.procid}.root"
wr.anaFileName =    wr.outFileName.replace(".root", "_specs.root")

wr.inTree = uproot.concatenate([args.input%int(spill) for spill in open(args.list%args.procid).read().split(",")], library="np")

wr.inTreeName =     "t"

wr.dryRun =         args.dry
wr.evStart =        args.procid * args.evtp
wr.maxEvents =      args.evtp
wr.specsToSave =    args.nspecs
wr.lowPassOrder =   2

# digitizer configuration #################################################################################################################################################################

V1742_5gsps    =   wr.Digi_t(name = "digi5",  wAmpFs = 2000.0)
V1742_5gsps_1V =   wr.Digi_t(name = "digi51", wAmpFs = 1000.0)

# detector configuration #################################################################################################################################################################

leadg = wr.WaveBox_t(   
        digi=V1742_5gsps, outNam="leadg", inWvs=["wave1"],
        pkRng=[50/205,85/205], bRng=[-33.0,-16], qRng=[-16.0,42.0], spRng=[-14,3.0], pkCut=[5.0, 1900.0], pedRng=None,
        saveW=True, gain=-1.0, cf=0.12
    )

cindy = wr.WaveBox_t(   
        digi=V1742_5gsps, outNam="cindy", inWvs=[F"wave{ii}" for ii in [2,3]],  
        pkRng=[40/205,80/205], bRng=[-15,-9], qRng=[-8,15], spRng=[-8,10], pkCut=[25.0, 1900.0], 
        saveW=True, gain=-1.0, cf=0.045, lowPass=350.0, cfScan=[4, 6, 8, 10, 12, 14],
        nToBook=3, outChans=[0,1]
    )

cindy2 = wr.WaveBox_t(   
        digi=V1742_5gsps_1V, outNam="cindy_2digi", inWvs=["wave50"],  
        pkRng=cindy.pkRng, bRng=cindy.bRng, qRng=cindy.qRng, spRng=cindy.spRng, pkCut=[cindy.pkRng[0], 950.0], 
        saveW=cindy.saveW, gain=cindy.gain, cf=cindy.cf, lowPass=cindy.lowPass, cfScan=cindy.cfScan,
        nToBook=0, outChans=[2], writeTo=cindy
    )

crils = wr.WaveBox_t(   
        digi=V1742_5gsps, outNam="crils", inWvs=[F"wave{ii}" for ii in range(4,4+18)],
        pkRng=[15/205,80/205], bRng=[-30.0,-12.5], qRng=[-12.0,40.0], spRng=[-11.5,6.0], pkCut=[5.0, 1680.0],
        saveW=True, gain=1.0, cf=0.12, lowPass=450.0, cfScan=None#[0.10,0.12,0.14,0.16,0.18,0.20]
    )

crilp = wr.WaveBox_t(   
        digi=V1742_5gsps, outNam="crilp", inWvs=[F"wave{ii}" for ii in range(22,31+1)],
        pkRng=[15/205,80/205], bRng=[-36.0,-14.5], qRng=[-14.0,105.0], spRng=[-13.5,6.0], pkCut=[5.0, 1680.0],
        saveW=True, gain=1.0, cf=0.12, lowPass=225.0, cfScan=None,
        nToBook=18, outChans=[2,3,6,7,8,9,10,11,14,15]
    )

crilp2 = wr.WaveBox_t(   
        digi=V1742_5gsps_1V, outNam="crilp_2digi", inWvs=[F"wave{ii}" for ii in [32,33,36,37,44,45,48,49]],
        pkRng=crilp.pkRng, bRng=crilp.bRng, qRng=crilp.qRng, spRng=crilp.spRng, pkCut=[crilp.pkCut[0], 950.0],
        saveW=crilp.saveW, gain=crilp.gain, cf=crilp.cf, lowPass=crilp.lowPass, cfScan=crilp.cfScan,
        nToBook=0, outChans=[0,1,4,5,12,13,16,17], writeTo=crilp
    )

fast = wr.WaveBox_t(   
        digi=V1742_5gsps, outNam="fast", inWvs=[F"wavefast{ii}" for ii in range(8)], opts="",
        pkRng=185/205, bRng=[-105.0,-55.0], qRng=[-5,5], spRng=[-50,0.0], pkCut=[100.0, None], 
        saveW=True, gain=-1.0, cf=0.20, thr=22.0, thrScan=None
    )

# user function #################################################################################################################################################################

def userbegin():
   
   wr.b_posCri = wr.MkBranch(wr.outTree, "posCri", "f", [2])
    
#    if not args.notracker: return
   wr.in_poss = wr.inTree["xRaw"]
   
def userloop(ientry):
   
#    if not args.notracker: return True

   poss = wr.in_poss[ientry]
   zztelescope = (0.95+15.48)/15.48
   
   wr.b_posCri[0] = poss[0] + (poss[2] - poss[0]) * zztelescope
   wr.b_posCri[1] = poss[1] + (poss[3] - poss[1]) * zztelescope
   
   return True

wr.UserBegin = userbegin
wr.UserLoop = userloop

# configurator #################################################################################################################################################################

wr.wboxes = [cindy, cindy2, crils, crilp, crilp2, fast, leadg]

if args.type == "ele":
    pass

if args.type == "mips":
    pass

if args.type == "pede":
    for ii in wr.wboxes: 
        ii.pkRng = 0.2
        ii.pkRng = None
        
if args.opts == "onlycindy": wr.wboxes = [cindy]
    
# launch #################################################################################################################################################################

wr.Launch()
