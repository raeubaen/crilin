#!/bin/bash
python3 /afs/cern.ch/work/r/rgargiul/code_reco/step3_fromttree.py $7/$3.root $8/$3/$3_out_$2.root $4 $5 $9 --maxevents $6 --offset $(($2*$6))
