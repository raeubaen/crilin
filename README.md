# crilin
per runnare

ssh su lxplus-gpu.cern.ch
andare nella folder prima dell repo
virtualenv -p python3 gpuenv
source gpuenv/bin/activate
pip3 install cupy uproot numpy pandas argparse

rientrare nella repo

mettere una mappa giusta in h2_crilin_map.csv
i canali cindy vanno cambiati dai default in recogpu.py o con argomenti da terminale quando si runna

su singoli file:
runnare con python3 recogpu.py --help e poi seguire istruzioni

sul monitor:
chiedere a me
