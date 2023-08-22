import ROOT, uproot
import awkward as ak
import scipy.fft
import scipy.signal
import numpy as np
import types
from tqdm import tqdm

class WaveReco:
    
    inTreeName,outTreeName,inFileName,outFileName,anaFileName= None, None, None, None, None
    inTree,outTree,outFile,anaFile,inFile = None, None, None, None, None
    UserBegin, UserLoop, UserWave, UserTerminate = None, None, None, None
    spline_t = ROOT.TSpline3
    maxEvents = -1
    specsToSave = 10
    dryRun = False
    saveEventNumber=None
    waveF = ""
    wboxes = []       
    lowPassOrder = 2
    gignoreLevel = ROOT.kFatal
    lowPassFilter_t = scipy.signal.butter
    
    @staticmethod 
    def ttqdm(vv, col="green"): return tqdm(vv, colour=col, bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:45}{r_bar:10}')
    
    @staticmethod 
    def MkBranch(tree, varName, varType = 'd', varDims=None):
        var = np.zeros(varDims if varDims != None else 1, dtype=varType)
        tree.Branch(varName, var, F"{varName}{str.join('', [F'[{ii}]' for ii in varDims]) if varDims != None else ''}/{varType.capitalize()}")
        return var      

    def Msg(self, msg, err=False):
        print(F"      WaveReco: {'ERROR:' if err else ''}{msg}")   
    
    class Digi_t():
        def __init__(self, wSz = 1024, wFs = 4096, wAmpFs = 1000, tBin = 0.2, aErr = 0.15, tErr = 0.0, name = "digi", inZ = 50.0, varTyp=np.ushort):
            self.name,self.wSz,self.wFs,self.wAmpFs,self.tBin,self.tErr,self.aErr,self.inZ,self.varTyp=name,wSz,wFs,wAmpFs,tBin,tErr,aErr,inZ,varTyp
            self.compute()
            self.wTimeBooked = False
            self.wtime = self.tBin * np.arange(0,self.wSz,1)
        def compute(self):
            self.wTimSz = float(self.wSz)*self.tBin
            self.aBin = float(self.wAmpFs)/float(self.wFs)
        def BookOutput(self, tout):
            if self.wTimeBooked: return
            self.wTimeBooked = True
            bname = self.name + "_wtim"
            self.b_wtime = WaveReco.MkBranch(tout, bname, "f", [self.wSz])
            self.b_wtime[:] = self.wtime

    class WaveBox_t():

        def __init__(self, digi, inWvs, bRng, qRng, spRng, outNam, pkRng=None, pkCut=None, pedRng=None,
                           saveW=True, filters=None,
                           lowPass=None, cfScan=None, cf=0.1, gain=1.0, opts=None, thr=None, thrScan=None,
                           tmplFit=None, tmplGen=None, doFFT=None,
                           nToBook=None, outChans=None, writeTo=None
                    ):

            self.digi,self.inWvs,self.qRng,self.bRng,self.spRng,self.outNam,self.pkRng,self.pkCut,self.pedRng,\
            self.saveW,self.filters,\
            self.lowPass,self.cfScan,self.cf,self.gain,self.opts,self.thr,self.thrScan,\
            self.tmplFit,self.tmplGen,self.doFFT,\
            self.nToBook,self.outChans,self.writeTo=\
            digi,inWvs,qRng,bRng,spRng,outNam,pkRng,pkCut,pedRng,\
            saveW,filters,\
            lowPass,cfScan,cf,gain,opts,thr,thrScan,\
            tmplFit,tmplGen,doFFT,\
            nToBook,outChans,writeTo

            self.init()

        def init(self):
            
            self.nChan = len(self.inWvs)
            self.sign = float(self.gain<0)
            self.waveIn = []
            self.addbase = - self.digi.wFs if self.sign < 0 else 0.0
            self.bRngSam = np.array(np.array(self.bRng, dtype=float) / self.digi.tBin, dtype=int)
            self.qRngSam = np.array(np.array(self.qRng, dtype=float) / self.digi.tBin, dtype=int)
            self.spRngSam = np.array(np.array(self.spRng, dtype=float) / self.digi.tBin, dtype=int)
            if self.pedRng != None: self.pedRngSam = np.array(np.array(self.pedRng, dtype=float) / self.digi.tBin, dtype=int)
            self.fixPk = 1 if type(self.pkRng) == float else 0
            if self.pkRng == None: self.pkRng = [0,1]
            if self.fixPk: 
                self.pkRngSam = np.array( (self.digi.wSz-1) * self.pkRng * np.ones(2,dtype=float), dtype=int) 
            else:
                self.pkRngSam = np.array(np.array(self.pkRng, dtype=float) * (self.digi.wSz-1), dtype=int) 
            self.specSaved = 0
             
        def BookOutput(self, tout):
            
            if self.saveW: self.digi.BookOutput(tout)
            
            nChanToBook = self.nToBook if self.nToBook != None else self.nChan
            self.nChanToBook = nChanToBook

            if self.nToBook == 0: return
            if self.writeTo != None: return
            
            self.b_ped =    WaveReco.MkBranch(tout, self.outNam+"_ped", "f", [nChanToBook])
            self.b_bline =  WaveReco.MkBranch(tout, self.outNam+"_bline", "f", [nChanToBook])
            self.b_brms =   WaveReco.MkBranch(tout, self.outNam+"_brms", "f", [nChanToBook])
            self.b_peak =   WaveReco.MkBranch(tout, self.outNam+"_peak", "f", [nChanToBook])
            self.b_charge = WaveReco.MkBranch(tout, self.outNam+"_charge", "f", [nChanToBook])
            self.b_timcf =  WaveReco.MkBranch(tout, self.outNam+"_timcf", "f", [nChanToBook])
            self.b_timtr =  WaveReco.MkBranch(tout, self.outNam+"_timtr", "f", [nChanToBook])
            self.b_timpk =  WaveReco.MkBranch(tout, self.outNam+"_timpk", "f", [nChanToBook])
            self.b_riset =  WaveReco.MkBranch(tout, self.outNam+"_riset", "f", [nChanToBook])
            self.b_wok   =  WaveReco.MkBranch(tout, self.outNam+"_wok", "i", [nChanToBook])
            
            if self.saveW:
                self.b_wave = WaveReco.MkBranch(tout, self.outNam+"_wav", "f", [nChanToBook, self.digi.wSz])
            
            if self.cfScan != None:
                self.b_cfscan = WaveReco.MkBranch(tout, self.outNam+"_cfscan", "f", [nChanToBook, len(self.cfScan)])
            
            if self.thrScan != None:
                self.b_trscan = WaveReco.MkBranch(tout, self.outNam+"_trscan", "f", [nChanToBook, len(self.thrScan)])
                            
        def BookInput(self, tin, evfrom=0, maxev=-1):
            self.waveIn = []
            # for ii in (self.inWvs):
            for ii in WaveReco.ttqdm(self.inWvs, "blue"):
                # end = evfrom + maxev if maxev > 0 else -1
                # self.waveIn.append(tin[ii][evfrom:end, :])
                self.waveIn.append(tin[ii])
                        
    def Begin(self):
        
        if self.inTree == None:
            if self.inFile == None: self.inFile = uproot.open(self.inFileName)
            self.inTree = self.inFile[self.inTreeName]
            
        if self.outTreeName == "" or self.outTreeName == None : self.outTreeName = self.inTreeName

        if self.outFile == None: self.outFile = ROOT.TFile(self.outFileName, "recreate")
        self.outFile.cd()

        if self.outTree == None: self.outTree = ROOT.TTree(self.outTreeName, self.outTreeName) 
 
        if self.anaFileName == "" : self.anaFileName = None
        self.anaFile = ROOT.TFile(self.anaFileName, "recreate") if self.anaFileName != None else self.outFile
        
    def Terminate(self):
        
        self.outFile.cd()
        self.outTree.Write()
        self.outFile.Close()
        if self.anaFileName != None : self.anaFile.Close()
    
    def Book(self):
        self.b_evt = WaveReco.MkBranch(self.outTree, "evt", "i")
        
        # for ii in (self.wboxes):
        for ii in WaveReco.ttqdm(self.wboxes, "magenta"):
            ii.BookInput(self.inTree)
            ii.BookOutput(self.outTree)
  
    def Launch(self):
        
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("---------------------------- Universal Wave Reco -----------------------------")
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("------------------------ daniele.paesani@lnf.infn.it -------------------------")
        self.Msg("------------------------------------------------------------------------------")       
        self.Msg("------------------------------------------------------------------------------")       
        self.Msg(F"                           --- channel map ---")
        ii: self.WaveBox_t
        for iii, ii in enumerate(self.wboxes): 
            mmsg = F"  {iii}{' '*(3-len(str(iii)))}   {ii.digi.name} {' '*(12-len(ii.digi.name))}[{ii.inWvs[0]} ... {ii.inWvs[-1]}] {' '*(25-len(ii.inWvs[-1])-len(ii.inWvs[0]))}   {ii.outNam}[{ii.nChan}]"
            if ii.writeTo != None: mmsg+= F"     writeTo:{ii.writeTo.outNam}[{ii.outChans[0]} ... {ii.outChans[-1]}]"
            self.Msg(mmsg)
        self.Msg(F"                         --- channel map end ---")
        self.Msg(F"input:   {self.inFileName}")
        self.Msg(F"output:  {self.outFileName}")
        self.Msg(F"ana:     {self.anaFileName}")
        if (self.dryRun) : 
            self.Msg(F"end of dry run")
            self.Msg("------------------------------------------------------------------------------")
            return
        self.Msg("starting...")
        self.Begin()
        if self.UserBegin != None: self.UserBegin() 
        self.Msg("booking io...") 
        self.Book()
        print(self.inTree)
        self.entries = len(self.inTree["eventNumber"])
        self.Msg(F"entries: {self.entries}")
        self.etp = min(self.entries, self.maxEvents) if self.maxEvents > 0  else self.entries
        self.Msg(F"to process: {self.etp}")
        self.Msg("starting loop...") 
        prev = ROOT.gErrorIgnoreLevel
        gErrorIgnoreLevel = self.gignoreLevel
        self.LoopEntries()
        gErrorIgnoreLevel = prev
        self.Msg("terminating...") 
        self.Terminate()
        if self.UserTerminate != None: self.UserTerminate() 
        self.Msg("processing done")
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("---------------------------- Universal Wave Reco -----------------------------")
        self.Msg("------------------------------------------------------------------------------\n\n")
        
    def LoopEntries(self):
            
        for bbb in self.wboxes:
            for www in range(bbb.nChanToBook):
                bbb.b_wok[www] = 0
        
        print(f"\n\nETP: {self.etp}\n\n")

        for ientry in (WaveReco.ttqdm(range(self.etp))): 
            
            self.b_evt[0] = ientry
            for ibox, box in enumerate(self.wboxes):
                        
                gain = box.gain
                sign = box.sign
                wsize = box.digi.wSz
                addbase = box.addbase
                digi = box.digi
                digi: WaveReco.Digi_t
                box: WaveReco.WaveBox_t

                wzeros, wones = np.zeros(wsize), np.ones(wsize)
    
                if box.lowPass != None: 
                    lopanum, lopaden = scipy.signal.butter(N=self.lowPassOrder, Wn=0.002*box.lowPass*digi.tBin, btype="low", analog=0)
                
                pkstart, pkstop = box.pkRngSam[0], box.pkRngSam[1]
                
                print(f"\n\nbox.waveIn.shape: {box.waveIn[0].shape}\n\n")
                    
                for iwave, win in enumerate(box.waveIn):
                    
                    iwaveout = iwave if box.outChans == None else box.outChans[iwave]
                    boxout = box if box.writeTo == None else box.writeTo
                                        
                    for ii in [boxout.b_ped, boxout.b_bline, boxout.b_brms, boxout.b_charge,\
                        boxout.b_peak, boxout.b_timpk, boxout.b_timcf, boxout.b_timtr, boxout.b_riset]:
                        ii[iwaveout] = -9999.99
                    
                    boxout.b_wok[iwaveout] = 0
                    wave = win[ientry]
                    wave = np.multiply(np.add(wave, addbase), gain * digi.aBin)
                    ipeak = pkstart if box.fixPk else pkstart + np.argmax(wave[pkstart:pkstop])
                    peak = wave[ipeak]
                    
                    if box.lowPass != None: 
                        wave_raw = wave.copy()
                        wave = scipy.signal.filtfilt(lopanum, lopaden, wave)
                        # wave = scipy.signal.lfilter(lopanum, lopaden, wave)
                        
                    wbline = wave[ max(int(ipeak+box.bRngSam[0]),0) : min(int(ipeak+box.bRngSam[1]),wsize) ]
                    if len(wbline) == 0: continue
                    bline, brms = wbline.mean(),wbline.std()
                    peak = peak - bline
                    if box.pkCut != None:
                        if (box.pkCut[0]!=None and peak<box.pkCut[0]): continue
                        if (box.pkCut[1]!=None and peak>box.pkCut[1]): continue
                    wave = np.add(wave, -bline)
                    wcharge = wave[ max(int(ipeak+box.qRngSam[0]),0) : min(int(ipeak+box.qRngSam[1]),wsize) ]
                    if len(wcharge) == 0: continue
                    charge = np.sum(wcharge)*digi.tBin/digi.inZ
                    gra = ROOT.TGraphErrors(wsize, digi.wtime, wave, wzeros, np.multiply(wones, brms))
                    tpeak = ipeak*digi.tBin      
                    ped = -9999.99  
                    if box.pedRng != None: 
                        wped = wave[ max(int(ipeak+box.pedRngSam[0]),0) : min(int(ipeak+box.pedRngSam[1]),wsize) ]
                        if len(wped) > 0:
                            ped = np.sum(wped)*digi.tBin/digi.inZ

                    spfrom, spto = tpeak+box.spRng[0], tpeak+box.spRng[1]
                    wspline = self.spline_t("wspline", gra)
                    def ffwspline(x, p): return wspline.Eval(x[0])
                    fwspline = ROOT.TF1("fwspline", ffwspline, spfrom, spto, 0)
                    peak = fwspline.GetMaximum(spfrom, spto)
                    tpeak = fwspline.GetMaximumX(spfrom, spto)
                    tcf = fwspline.GetX(peak*box.cf)
                    ttr = fwspline.GetX(box.thr) if box.thr != None else -9999.99
                    riset = fwspline.GetX(0.9*peak) - fwspline.GetX(0.1*peak)

                    boxout.b_ped[iwaveout] = ped
                    boxout.b_bline[iwaveout] = bline
                    boxout.b_brms[iwaveout] = brms
                    boxout.b_charge[iwaveout] = charge
                    boxout.b_peak[iwaveout] = peak
                    boxout.b_timpk[iwaveout] = tpeak
                    boxout.b_timcf[iwaveout] = tcf
                    boxout.b_timtr[iwaveout] = ttr
                    boxout.b_riset[iwaveout] = riset
                    boxout.b_wok[iwaveout] = 1
                    
                    if (box.saveW): boxout.b_wave[iwaveout,:] = wave
                    if (box.cfScan != None):  boxout.b_cfscan[iwaveout,:] = np.array([fwspline.GetX(peak*icf) for icf in box.cfScan])       
                    if (box.thrScan != None): boxout.b_trscan[iwaveout,:] = np.array([fwspline.GetX(itr) for itr in box.thrScan])      

                    if box.specSaved < self.specsToSave and self.anaFileName != None:
                        
                        # outname = box.outNam if box.writeTo == None else box.writeTo.outNam
                        outname = box.outNam
                        
                        box.specSaved +=1
                        self.anaFile.mkdir("specimens", "", 1).mkdir(outname,"", 1).cd()
                        title = F"ev{ientry}_{outname}{iwaveout}"
                        cc = ROOT.TCanvas(title)
                        
                        if box.lowPass != None: 
                            cc.Divide(1,2)
                            cc.cd(2)
                            graraw = ROOT.TGraphErrors(wsize, digi.wtime, (np.add(wave_raw, -bline)), wzeros, np.multiply(wones, brms))
                            graraw.SetTitle(F"unfiltered waveform;tim [ns]; amp [mV]")
                            graraw.SetLineWidth(1); graraw.SetMarkerStyle(20); graraw.SetMarkerSize(0.25); graraw.SetMarkerColor(ROOT.kBlue); graraw.Draw("AP"); 
                            cc.cd(1)
                            
                        gra.SetTitle(F"event: {ientry}   chan: {outname}{iwaveout};tim [ns]; amp [mV]")
                        gra.SetLineWidth(1); gra.SetMarkerStyle(20); gra.SetMarkerSize(0.25); gra.SetMarkerColor(ROOT.kBlack); gra.Draw("AP"); 
                        fwspline.SetLineColor(ROOT.kViolet); fwspline.Draw("same")
                        
                        for ii, iic in zip([tpeak, tcf], [ROOT.kRed, ROOT.kRed]):
                            tp = ROOT.TMarker(ii, fwspline.Eval(ii), 2)
                            tp.SetMarkerSize(3); tp.SetMarkerColor(iic); tp.DrawClone("same")
                        
                        if box.thr != None: 
                            tp = ROOT.TMarker(ttr, fwspline.Eval(ttr), 2)
                            tp.SetMarkerSize(3); tp.SetMarkerColor(ROOT.kOrange+2); tp.DrawClone("same")
                            
                        pkrnguse = [-tpeak+box.pkRng[jj]*digi.wTimSz for jj in range(2)] if not box.fixPk else [-tpeak+box.pkRng*digi.wTimSz]*2
                        for ii, iic, iia in zip([box.bRng,box.qRng,box.spRng,box.pedRng,pkrnguse], [ROOT.kOrange+2,ROOT.kBlue,ROOT.kGreen,ROOT.kYellow,ROOT.kYellow+2], [0.25*peak, 0.5*peak, 0.6*peak, 0.5*peak, 0.8*peak]):
                            if ii == None: continue
                            for iii in range(2):
                                vv = max(0.0, min(tpeak+ii[iii], digi.wTimSz))
                                tt = ROOT.TLine(vv,-0.05*peak,vv,iia)
                                tt.SetLineWidth(1); tt.SetLineStyle(1); tt.SetLineColor(iic); tt.DrawClone("same")
                            vv1, vv2 = max(0.0, tpeak+ii[0]), min(tpeak+ii[1], digi.wTimSz)
                            aa = ROOT.TArrow(vv1, iia, vv2, iia, 0.01, "<>")
                            aa.SetLineStyle(1); aa.SetLineWidth(1); aa.SetLineColor(iic); aa.DrawClone("same")
                            
                        pt = ROOT.TPaveText(0.7,0.65,0.95,0.97, "NB NDC ARC") 
                        pt.SetFillColor(0)
                        pt.SetLineColor(0)
                        ptnams = ["bline [mV]", "brms [mV]", "peak [mV]", "charge [pC]", "ped [ns]", "timpk [ns]", "timcf [ns]", "timtr [ns]", "riset [ns]"]
                        ptvars = [bline, brms, peak, charge, tpeak, tcf, ttr, riset]
                        for ii, iii in zip(ptnams, ptvars):
                            pt.AddText(F"{ii}:   {iii:.2f}")
                        pt.SetAllWith("]", "align", 22)
                        pt.SetAllWith("]", "size", 25)
                        pt.Draw("same")
                        
                        cc.Write()
                        self.outFile.cd()
                        
                        
                        
                                                        
            if self.UserLoop != None and not self.UserLoop(ientry): continue
            self.outTree.Fill()

                    
        

