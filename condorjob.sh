#!/bin/bash
python3 /afs/cern.ch/work/r/rgargiul/code_reco/step3_fromttree.py /afs/cern.ch/work/r/rgargiul/crilin_input/$3.root /afs/cern.ch/work/r/rgargiul/reco_data/$3/tree_and_json/$3_out_$2.root $4 --frontboard $5 --maxevents $6 --offset $(($2*$6))
