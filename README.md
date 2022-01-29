# ADIF to QSL

## Purpose
Takes an ADIF file as input, outputs QSL card labels. It's neat!

## License
Copyright 2022, Brendan O'Connor, licensed under BSD 2-Clause for everything except `imb.py`.

`imb.py` is also licensed under the BSD 2-clause, but is taken with extreme gratitude from <https://github.com/samrushing/pyimb>. I've made minimal changes to fix a few linting and py2to3 bugs, but all the work is theirs.

## Prerequisites

You need a USPS Mailer ID so that you can create an Intelligent Mail Barcode. See <https://www.usps.com/election-mail/creating-imb-election-mail-kit.pdf> for plenty of details. Set it in `qsl_config.py`.

You need to download the FCC ULS database from <https://www.fcc.gov/uls/transactions/daily-weekly>. You need the weekly dump from the Amateur Radio Service. Take the `EN.dat` file and put it in the local directory. (It's 180MB and changes weekly, so it's not great to check in.)

## How to Use

The force? (Coming)