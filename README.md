# ADIF to QSL

## Purpose
Takes an ADIF file as input, outputs QSL card labels. It's neat!

## License
Copyright 2022, Brendan O'Connor, licensed under BSD 2-Clause for everything except the following exceptions.

`imb.py` is also licensed under the BSD 2-clause, but is taken with extreme gratitude from <https://github.com/samrushing/pyimb>. I've made minimal changes to fix a few linting and py2to3 bugs, but all the work is theirs. Copyright (c) 2012, Sam Rushing.

`Inconsolata-Regular.ttf` and `Inconsolata-Bold.ttf` are released at <https://github.com/googlefonts/inconsolata> under the OFL-1.1 license, included as `inconsolata-license.txt`.

`USPSIMBStandard.ttf` is available as part of the `uspsFontsNonAFP-1.4.0.zip` file from <https://postalpro.usps.com/onecodesolution>. It comes with a license agreement, however (and this isn't legal advice) it's not at all clear to me that it's valid because the US federal government can't copyright things---everything they do is in the public domain by default. (One hilarious exception is stamps, and go ask an IP attorney why. I'm just a country ham radio operator....) So... do as you will.

## Prerequisites

You need a USPS Mailer ID so that you can create an Intelligent Mail Barcode. See <https://www.usps.com/election-mail/creating-imb-election-mail-kit.pdf> for plenty of details. Set it in `qsl_config.py`.

You need to download the FCC ULS database from <https://www.fcc.gov/uls/transactions/daily-weekly>. You need the weekly dump from the Amateur Radio Service. Take the `EN.dat` and `HD.dat` files and put them in the local directory. (The dump changes weekly, so it's not great to check in.)

You need a Brother label printer supported by the <https://brother-ql.net/> project, loaded with 2.4" wide roll labels. If you need a different width, that's fine, but you'll need to change the layout section yourself.

## How to Use

### Initial Setup

`./adif_to_qsl.py --parse-db`

This will read `EN.dat` and `HD.dat` from the current directory and create `uls.db` -- a SQLite DB with callsign-to-address mapping. Nearly every piece of data we need is in `EN.dat`, but `HD.dat` is where one finds "is this license active or not" information---sadly, not something available in the table with address information. Running this once is sufficient; when you want to use a new dump, just delete `uls.db` and run this with new `.dat` files.

### Use

`./adif_to_qsl.py -f <path/to/adif>`

Makes QSL cards and prints them to a locally-attached Brother label printer (e.g., QL-800). If you just want the QSL labels but not to print them, use the `-i` option to output all the labels into the `qsl_cards` folder instead of printing.
