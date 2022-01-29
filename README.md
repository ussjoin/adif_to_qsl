# ADIF to QSL

## Purpose
Takes an ADIF file as input, outputs QSL card labels. It's neat!

## License
Copyright 2022, Brendan O'Connor, licensed under BSD 2-Clause for everything except `imb.py` and `USPSIMBStandard.ttf`.

`imb.py` is also licensed under the BSD 2-clause, but is taken with extreme gratitude from <https://github.com/samrushing/pyimb>. I've made minimal changes to fix a few linting and py2to3 bugs, but all the work is theirs.

`USPSIMBStandard.ttf` is available as part of the `uspsFontsNonAFP-1.4.0.zip` file from <https://postalpro.usps.com/onecodesolution>. It comes with a license agreement, however (and this isn't legal advice) it's not at all clear to me that it's valid because the US federal government can't copyright things---everything they do is in the public domain by default. (One hilarious exception is stamps, and go ask an IP attorney why. I'm just a country ham radio operator....) So... do as you will.

## Prerequisites

You need a USPS Mailer ID so that you can create an Intelligent Mail Barcode. See <https://www.usps.com/election-mail/creating-imb-election-mail-kit.pdf> for plenty of details. Set it in `qsl_config.py`.

You need to download the FCC ULS database from <https://www.fcc.gov/uls/transactions/daily-weekly>. You need the weekly dump from the Amateur Radio Service. Take the `EN.dat` file and put it in the local directory. (It's 180MB and changes weekly, so it's not great to check in.)

## How to Use

The force? (Coming)