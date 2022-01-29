import adif_io # https://gitlab.com/andreas_krueger_py/adif_io
import json
import subprocess
import secrets

import imb
import qsl_config


#qsos_raw, adif_header = adif_io.read_from_file("/Users/ussjoin/Desktop/Dropbox/LotW/Uploaded Logs/Smol/2022-01-28 WSJTX-Smol.adif")

qsos_raw, adif_header = adif_io.read_from_file("/Users/ussjoin/Desktop/Dropbox/LotW/Uploaded Logs/Smol/POTA/K3QB@K-3270-20220116.adif")

# What we need for a QSL Card:
## Date
## Time (UTC)
## Their Callsign
## My QTH
## Frequency
## Power
## Mode
## Signal Reports

# Optionally add:
## My POTA Location

# From their callsign, look up:
## Their name [8] [10]
## Their Address [15]
## Their City [16]
## Their State [17]
## Their Zip [18]

qsos_parsed = []

for qso in qsos_raw:
    q_p = {}
    q_p['callsign'] = qso.get('CALL')
    q_p['date'] = qso.get('QSO_DATE')
    q_p['date'] = f"{q_p['date'][0:4]}-{q_p['date'][4:6]}-{q_p['date'][6:8]}"
    
    q_p['time'] = qso.get('TIME_ON')
    q_p['time'] = f"{q_p['time'][0:2]}:{q_p['time'][2:4]}:{q_p['time'][4:6]}Z"
    
    q_p['qth'] = qso.get('MY_GRIDSQUARE')
    q_p['frequency'] = qso.get('FREQ')
    q_p['power'] = qso.get('TX_PWR')
    if q_p['power'] and q_p['power'][-1].upper() != "W":
        q_p['power'] = f"{q_p['power']}W"
    q_p['mode'] = qso.get('MODE')
    q_p['signal'] = f"S{qso.get('RST_SENT')} R{qso.get('RST_RCVD')}"
    
    q_p['notes'] = qso.get('MY_SIG_INFO')
    if q_p['notes']:
        q_p['notes'] = f"POTA Activation: {q_p['notes']}"
    
    qsos_parsed.append(q_p)

for qso in qsos_parsed:
    sub = subprocess.run(f"grep '|{qso['callsign']}|' EN.dat | tail -n 1", shell=True, stdout=subprocess.PIPE)
    subprocess_return = sub.stdout.decode('UTF-8').strip()
    row = subprocess_return.split('|')
    qso['firstname'] = row[8].title()
    qso['lastname'] = row[10].title()
    qso['address'] = row[15].title()
    qso['city'] = row[16].title()
    qso['state'] = row[17]
    if len(row[18]) > 5:
        qso['zip'] = f"{row[18][0:5]}-{row[18][5:9]}"
    else:
        qso['zip'] = f"{row[18][0:5]}"
    qso['serial'] = f"{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}"
    qso['imbcode'] = imb.encode(int(qsl_config.BARCODE_ID), int(qsl_config.SERVICE_ID), int(qsl_config.MY_MAILER_ID), int(qso['serial']), row[18])
    print(json.dumps(qso,indent=4))
    


#print(json.dumps(qsos_parsed,indent=4))