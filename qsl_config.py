# Yes, I should use YAML or something.
# No, I'm not going to.

# Specified in https://www.usps.com/election-mail/creating-imb-election-mail-kit.pdf
BARCODE_ID = "00"

# Assigned to a specific mailer
MY_MAILER_ID = "000000000"

# https://postalpro.usps.com/node/461
# This means, roughly, first class, don't bother sending address correction
SERVICE_ID = "270"

# For the label printer (I use a Brother QL-800)
# Should be "usb://<vendorid>:<productid>", like "usb://0x04f9:0x209b"
PRINTER_IDENTIFIER = "usb://0x04f9:0x209b"
