#! env python3
"""
This program takes an ADIF file and turns it into QSL card labels or images thereof.

"""


import argparse
import csv
from datetime import datetime
import json
import os
import subprocess
import secrets
import sqlite3
import sys

import adif_io # https://gitlab.com/andreas_krueger_py/adif_io
from wand.image import Image # https://docs.wand-py.org/
from wand.drawing import Drawing
from wand.color import Color

# https://brother-ql.net/ - this program calls the command-line utilities,
#   but doesn't use them pythonically

import imb
import qsl_config

MAKE_IMAGES = False

QSL_CARD_PATH = 'qsl_cards/'


def parse_adif(file_object):
    """parse_adif(file_object):

    Given a file-like object (on which it can call read()), generate an array full of QSOs.

    Returns: an array of dicts, where each dict is a single QSO, augmented with FCC data if available.

    """
    # [0] because the read_from_string() returns a tuple of qsos_raw, adif_header
    # (We don't need the headers for this, so just dropping them on the floor)
    qsos_raw = adif_io.read_from_string(file_object.read())[0]
    con = sqlite3.connect('uls.db')
    # Allows use of dictionary lookups on returns, see https://stackoverflow.com/a/3300514
    con.row_factory = sqlite3.Row
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
        if q_p['qth'] is None:
            print(f"The QSO with {q_p['callsign']} does not contain a MY_GRIDSQUARE, quitting.")
            sys.exit(1)

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

        res = cur.execute(f'SELECT * from amateurs where callsign = \"{q_p["callsign"]}\" and active = 1;').fetchall()
        if len(res) > 1:
            print("==========ERROR==========")
            print(f"While finding FCC records for {q_p['callsign']}, I found more than one " +
            "simultaneous active record. Since this really should never, ever happen, I am " +
            "terminating and letting you figure it out.")
            sys.exit(1)
        elif len(res) == 0:
            print(f"=====\nCan't find a name/address for {q_p['callsign']}, printing label without that!\n=====")
            q_p['has_address'] = False
        else:
            row = res[0]
            q_p['has_address'] = True
            q_p['firstname'] = row['firstname'].title()
            q_p['lastname'] = row['lastname'].title()
            q_p['address'] = row['address'].title()
            q_p['city'] = row['city'].title()
            q_p['state'] = row['state']
            if len(row['zipcode']) > 5:
                q_p['zip'] = f"{row['zipcode'][0:5]}-{row['zipcode'][5:9]}"
            else:
                q_p['zip'] = f"{row['zipcode'][0:5]}"

            q_p['serial'] = f"{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.randbelow(10)}"
            q_p['imbcode'] = imb.encode(int(qsl_config.BARCODE_ID),
                                        int(qsl_config.SERVICE_ID),
                                        int(qsl_config.MY_MAILER_ID),
                                        int(q_p['serial']),
                                        row['zipcode'])
        
        qsos_parsed.append(q_p)
    return qsos_parsed

def print_qsos(qsos_parsed):
    """print_qsos(qsos_parsed):

    Given an array full of QSOs, generate images of QSO cards and/or print them to a label printer.

    Returns: nothing.

    """
    for qso in qsos_parsed:
        # 4.75" wide, 2.4" tall, and brother_ql expects 290 dpi for this.
        res = 290
        with Image(width=int(res*4.75), height=int(res*2.4), background = Color('white')) as img:
            # Build the QSL bits, then the address and IMb
            # 2.5" wide left half, 2.25" wide right half ("half")
            qso_text = f"{qso['date']}\n{qso['time']}\n\n{qso['qth']}\n{qso['frequency']}\n{qso['power']}\n{qso['mode']}\n{qso['signal']}"
            if qso['notes']:
                qso_text += f"\n\n{qso['notes']}"
            draw_qso = Drawing()
            draw_qso.font = './Inconsolata-Regular.ttf'
            draw_qso.font_size = 60
            draw_qso.text(int(res * 0.1), int(res * 0.15), qso_text)
            draw_qso(img)

            if qso['has_address']: # They're in the FCC DB
                name_text = f"{qso['firstname']} {qso['lastname']}, {qso['callsign']}"
                draw_name = Drawing()
                draw_name.font = './Inconsolata-Bold.ttf'
                draw_name.font_size = 55
                draw_name.text(int(res * 2.0), int(res * 1.0), name_text)
                draw_name(img)

                address_text = f"{qso['address']}\n{qso['city']}, {qso['state']} {qso['zip']}"
                draw_address = Drawing()
                draw_address.font = './Inconsolata-Regular.ttf'
                draw_address.font_size = 50
                draw_address.text(int(res * 2.0), int(res * 1.2), address_text)
                draw_address(img)

                draw_imb = Drawing()
                draw_imb.font = './USPSIMBStandard.ttf'
                draw_imb.font_size = 54
                draw_imb.text(int(res * 2.0), int(res * 1.5), qso['imbcode'])
                draw_imb(img)
            else: # Just draw a callsign and the rest of the label, nothing else
                name_text = f"{qso['callsign']}"
                draw_name = Drawing()
                draw_name.font = './Inconsolata-Bold.ttf'
                draw_name.font_size = 55
                draw_name.text(int(res * 2.0), int(res * 1.0), name_text)
                draw_name(img)

            if MAKE_IMAGES:
                if not os.path.isdir(QSL_CARD_PATH):
                    os.mkdir(QSL_CARD_PATH)
                filepath = f"{QSL_CARD_PATH}{qso['callsign']}-{qso['date']}.png"
                img.save(filename=filepath)
            else:
                img.rotate(90)
                img.save(filename='temp.png')
                subprocess.run(
                    ["brother_ql_create --model QL-800 --label-size 62 ./temp.png > labelout.bin"],
                    shell=True)
                subprocess.run([f"brother_ql_print labelout.bin {qsl_config.PRINTER_IDENTIFIER}"],
                    shell=True)
                os.remove('temp.png')
                os.remove('labelout.bin')

def dump_qsos(qsos_parsed):
    """dump_qsos(qsos_parsed):

    Given an array full of QSOs, dump them as JSON to a file.
    File is named mailing-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json .

    Returns: nothing.

    """
    with open(f"mailing-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json", "w", encoding="latin-1") as json_file:
        json_file.write(json.dumps(qsos_parsed, indent=4))

def parse_db():
    """parse_db():

    Parse EN.dat and HD.dat, in the current working directory, into a SQLite DB named uls.json.
    Only pull out fields relevant to this program.

    Returns: nothing.

    """
    with open('EN.dat', 'r', encoding="latin-1") as enfile:
        with open('HD.dat', 'r', encoding="latin-1") as hdfile:
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
            cur.execute("CREATE TABLE IF NOT EXISTS amateurs" +
                "(identifier text, callsign text, firstname text, lastname text, address text, " +
                "city text, state text, zipcode text, active integer DEFAULT 0)")
            con.commit()

            for record in records.values():
                cur.execute(" INSERT INTO amateurs " +
                    "(identifier, callsign, firstname, lastname, address, city, state, zipcode, active) " +
                    f"VALUES (\"{record['identifier']}\", \"{record['callsign']}\", " +
                    f"\"{record['firstname']}\", \"{record['lastname']}\", \"{record['address']}\", " +
                    f"\"{record['city']}\", \"{record['state']}\", \"{record['zipcode']}\", "+
                    f"{record['active']});")

            con.commit()
            con.close()
    print("Parsing FCC databases to SQLite complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Turn an ADIF into QSL card labels.')
    parser.add_argument('-f', '--file', metavar="filename",
        help='the path to the ADIF file', type=open)
    parser.add_argument('-p', '--parse_db', action='store_true',
        help='parse an FCC EN.dat and HD.dat database into a local SQLite db called uls.db')
    parser.add_argument('-i', '--output_images', action='store_true',
        help=f'Create images and store them in a {QSL_CARD_PATH} directory. Do not print')

    args = parser.parse_args()
    MAKE_IMAGES = args.output_images

    if args.parse_db:
        parse_db()
    elif args.file:
        qsos = parse_adif(args.file)
        print_qsos(qsos)
        dump_qsos(qsos)
    else:
        print("You need to either use the -f option or the -p option. Use -h for help.")
        sys.exit(1)
