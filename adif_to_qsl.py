import adif_io # https://gitlab.com/andreas_krueger_py/adif_io
# https://docs.wand-py.org/
from wand.image import Image, UNIT_TYPES
from wand.drawing import Drawing
from wand.color import Color

import brother_ql # https://brother-ql.net/
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

qsos_skipped = []

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
        q_p['notes'] = f"POTA Activation\nfrom {q_p['notes']}"
    
    qsos_parsed.append(q_p)

for qso in qsos_parsed:
    sub = subprocess.run(f"grep '|{qso['callsign']}|' EN.dat | tail -n 1", shell=True, stdout=subprocess.PIPE)
    subprocess_return = sub.stdout.decode('UTF-8').strip()
    row = subprocess_return.split('|')
    if len(row) < 20:
        print(f"=====\nCan't find a name/address for {qso['callsign']}, skipping!\n=====")
        qsos_skipped.append(qso['callsign'])
        continue
    qso['firstname'] = row[8].title()
    qso['lastname'] = row[10].title()
    qso['address'] = row[15].title()
    qso['city'] = row[16].title()
    qso['state'] = row[17]
    if len(row[18]) > 5:
        qso['zip'] = f"{row[18][0:5]}-{row[18][5:9]}"
    else:
        qso['zip'] = f"{row[18][0:5]}"
    
    # PO boxes are, hilariously, stored in a weird way; see, e.g., W7WIL, who has PO Box 1651.
    if len(qso['address']) < 5 and len(row[19]) >= 1:
        qso['address'] = f"PO Box {row[19]}"
    
    qso['serial'] = f"{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}"
    qso['imbcode'] = imb.encode(int(qsl_config.BARCODE_ID), int(qsl_config.SERVICE_ID), int(qsl_config.MY_MAILER_ID), int(qso['serial']), row[18])
    # print(json.dumps(qso,indent=4))
    
    # 4.75" wide, 2.4" tall @ 300dpi would be 1425x720. However, Wand seems to ignore my please for resolution = 300.
    # Hence trying it at 72 so I don't lose my mind.
    DRAW_RESOLUTION = 290
    START_RESOLUTION = 72
    with Image(width=int(DRAW_RESOLUTION * 4.75), height=int(DRAW_RESOLUTION * 2.4), background = Color('white')) as img:
        # Build the QSL bits, then the address and IMb
        # 2.5" wide left half, 2.25" wide right half ("half")
        qso_text = f"{qso['date']}\n{qso['time']}\n\n{qso['qth']}\n{qso['frequency']}\n{qso['power']}\n{qso['mode']}\n{qso['signal']}"
        if qso['notes']:
            qso_text += f"\n\n{qso['notes']}"
        draw_qso = Drawing()
        draw_qso.font = './Inconsolata-Regular.ttf'
        draw_qso.font_size = 60
        draw_qso.text(int(DRAW_RESOLUTION * 0.1), int(DRAW_RESOLUTION * 0.15), qso_text)
        
        name_text = f"{qso['firstname']} {qso['lastname']}, {qso['callsign']}"
        draw_name = Drawing()
        draw_name.font = './Inconsolata-Bold.ttf'
        draw_name.font_size = 55
        draw_name.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.0), name_text)
        
        
        address_text = f"{qso['address']}\n{qso['city']}, {qso['state']} {qso['zip']}"
        draw_address = Drawing()
        draw_address.font = './Inconsolata-Regular.ttf'
        draw_address.font_size = 50
        draw_address.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.2), address_text)
        
        draw_imb = Drawing()
        draw_imb.font = './USPSIMBStandard.ttf'
        draw_imb.font_size = 54
        draw_imb.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.5), qso['imbcode'])
        
        
        draw_qso(img)
        draw_name(img)
        draw_address(img)
        draw_imb(img)
        img.rotate(90)
        img.save(filename='temp.png')
    
    subprocess.run(["brother_ql_create --model QL-800 --label-size 62 ./temp.png > labelout.bin"], shell=True)
    subprocess.run([f"brother_ql_print labelout.bin {qsl_config.PRINTER_IDENTIFIER}"], shell=True)
    
# Finally, re-print the list of skipped QSOs
print("====================================================")
print("Remember, I was unable to print QSOs for:")
for n in qsos_skipped:
    print(n)
print("====================================================")

#print(json.dumps(qsos_parsed,indent=4))