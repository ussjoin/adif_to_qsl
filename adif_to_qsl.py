#! env python3

import adif_io # https://gitlab.com/andreas_krueger_py/adif_io
# https://docs.wand-py.org/
from wand.image import Image, UNIT_TYPES
from wand.drawing import Drawing
from wand.color import Color

# import brother_ql # https://brother-ql.net/
import json
import subprocess
import secrets
from datetime import datetime
import argparse
import csv
import sqlite3

import imb
import qsl_config

DEBUG = False


def parse_adif(file_object):
    qsos_raw, adif_header = adif_io.read_from_string(file_object.read())
    con = sqlite3.connect('uls.db')
    con.row_factory = sqlite3.Row # Allows use of dictionary lookups on returns, see https://stackoverflow.com/a/3300514
    cur = con.cursor()

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
        if q_p['qth'] == None:
            print(f"The QSO with {q_p['callsign']} does not contain a MY_GRIDSQUARE, quitting.")
            exit(1)

        q_p['frequency'] = qso.get('FREQ')
        q_p['power'] = qso.get('TX_PWR')
        if q_p['power'] and q_p['power'][-1].upper() != "W":
            q_p['power'] = f"{q_p['power']}W"
        q_p['mode'] = qso.get('MODE')
        q_p['signal'] = f"S{qso.get('RST_SENT')} R{qso.get('RST_RCVD')}"
        # If there weren't signal reports, Python handles that by setting it as "SNone RNone".
        # Change that to just a blank.
        if q_p['signal'] == "SNone RNone":
            q_p['signal'] = ""
    
        q_p['notes'] = qso.get('MY_SIG_INFO')
        if q_p['notes']:
            q_p['notes'] = f"POTA Activation\nfrom {q_p['notes']}"
    
        qsos_parsed.append(q_p)

    for qso in qsos_parsed:
        
        # sub = subprocess.run(f"grep '|{qso['callsign']}|' EN.dat | tail -n 1", shell=True, stdout=subprocess.PIPE)
        # subprocess_return = sub.stdout.decode('UTF-8').strip()
        # row = subprocess_return.split('|')
        
        res = cur.execute(f'SELECT * from amateurs where callsign = \"{qso["callsign"]}\" and active = 1;').fetchall()
        if len(res) > 1:
            print("==========ERROR==========")
            print(f"While finding FCC records for {callsign}, I found more than one simultaneous active record.")
            print("Since this really should never, ever happen, I am terminating and letting you figure it out.")
            exit(1)
        elif len(res) == 0:
            print(f"=====\nCan't find a name/address for {qso['callsign']}, printing label without that!\n=====")
            qso['has_address'] = False
        else:
            row = res[0]
            qso['has_address'] = True
            qso['firstname'] = row['firstname'].title()
            qso['lastname'] = row['lastname'].title()
            qso['address'] = row['address'].title()
            qso['city'] = row['city'].title()
            qso['state'] = row['state']
            if len(row['zipcode']) > 5:
                qso['zip'] = f"{row['zipcode'][0:5]}-{row['zipcode'][5:9]}"
            else:
                qso['zip'] = f"{row['zipcode'][0:5]}"
    
            qso['serial'] = f"{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}"
            qso['imbcode'] = imb.encode(int(qsl_config.BARCODE_ID), int(qsl_config.SERVICE_ID), int(qsl_config.MY_MAILER_ID), int(qso['serial']), row['zipcode'])
    return qsos_parsed
    
def print_qsos(qsos_parsed):
    for qso in qsos_parsed:
        # 4.75" wide, 2.4" tall, and brother_ql expects 290 dpi for this.
        DRAW_RESOLUTION = 290
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
            draw_qso(img)
        
            if qso['has_address']: # They're in the FCC DB        
                name_text = f"{qso['firstname']} {qso['lastname']}, {qso['callsign']}"
                draw_name = Drawing()
                draw_name.font = './Inconsolata-Bold.ttf'
                draw_name.font_size = 55
                draw_name.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.0), name_text)
                draw_name(img)

                address_text = f"{qso['address']}\n{qso['city']}, {qso['state']} {qso['zip']}"
                draw_address = Drawing()
                draw_address.font = './Inconsolata-Regular.ttf'
                draw_address.font_size = 50
                draw_address.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.2), address_text)
                draw_address(img)

                draw_imb = Drawing()
                draw_imb.font = './USPSIMBStandard.ttf'
                draw_imb.font_size = 54
                draw_imb.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.5), qso['imbcode'])
                draw_imb(img)
            else: # Just draw a callsign and the rest of the label, nothing else
                name_text = f"{qso['callsign']}"
                draw_name = Drawing()
                draw_name.font = './Inconsolata-Bold.ttf'
                draw_name.font_size = 55
                draw_name.text(int(DRAW_RESOLUTION * 2.0), int(DRAW_RESOLUTION * 1.0), name_text)
                draw_name(img)
        
            if not DEBUG:
                img.rotate(90)
            img.save(filename='temp.png')
            if DEBUG:
                exit()
    
        if not DEBUG:
            subprocess.run(["brother_ql_create --model QL-800 --label-size 62 ./temp.png > labelout.bin"], shell=True)
            subprocess.run([f"brother_ql_print labelout.bin {qsl_config.PRINTER_IDENTIFIER}"], shell=True)

def dump_qsos(qsos_parsed):
    with open(f"mailing-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json", "w") as f:
        f.write(json.dumps(qsos_parsed, indent=4))

def parse_db():
    enfile = open('EN.dat', 'r')
    hdfile = open('HD.dat', 'r')
    records = {}
    
    print("Reading EN.dat")
    reader = csv.reader(enfile, delimiter='|')
    for row in reader:
        record = {}
        record['identifier'] = row[1]
        record['callsign'] = row[4]
        record['firstname'] = row[8].title().replace('"', '')
        record['lastname'] = row[10].title().replace('"', '')
        record['address'] = row[15].title().replace('"', '')
        record['city'] = row[16].title().replace('"', '')
        record['state'] = row[17].replace('"', '')
        record['zipcode'] = row[18]
        
        # PO boxes are, hilariously, stored in a weird way; see, e.g., W7WIL, who has PO Box 1651.
        if len(record['address']) < 5 and len(row) > 19 and len(row[19]) >= 1:
            pobox = row[19].replace('"', '')
            record['address'] = f"PO Box {pobox}"
        
        #print(f"I found Operator {firstname} {lastname}, {callsign}, at {address}, {city}, {state} {zipcode}.")
        records[record['identifier']] = record
    
    print("Reading HD.dat")
    reader = csv.reader(hdfile, delimiter='|')
    for row in reader:
        identifier = row[1]
        active = row[5]
        if active == 'A':
            records[identifier]['active'] = 1
        else:
            records[identifier]['active'] = 0
        
    
    print("Opening DB")
    con = sqlite3.connect('uls.db')
    cur = con.cursor()
    # Create table
    cur.execute('''CREATE TABLE IF NOT EXISTS amateurs (identifier text, callsign text, firstname text, lastname text, address text, city text, state text, zipcode text, active integer DEFAULT 0)''')
    con.commit()
    
    for record in records.values():
        sqlstring = f"INSERT INTO amateurs (identifier, callsign, firstname, lastname, address, city, state, zipcode, active) VALUES (\"{record['identifier']}\", \"{record['callsign']}\", \"{record['firstname']}\", \"{record['lastname']}\", \"{record['address']}\", \"{record['city']}\", \"{record['state']}\", \"{record['zipcode']}\", {record['active']});"
        #print(sqlstring)
        cur.execute(sqlstring)

    con.commit()
    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Turn an ADIF into QSL card labels.')
    parser.add_argument('-f', '--file', metavar="filename", help='the path to the ADIF file', type=open)
    parser.add_argument('-d', '--debug', action='store_true', help='run in debug mode (do not print, exit after one label)')
    parser.add_argument('-p', '--parse_db', action='store_true', help='parse an FCC EN.dat and HD.dat database into a local SQLite db called uls.db')

    args = parser.parse_args()
    DEBUG = args.debug
    
    if args.parse_db:
        parse_db()
    elif args.file:
        qsos = parse_adif(args.file)
        #print_qsos(qsos)
        dump_qsos(qsos)
    else:
        exit(1)
