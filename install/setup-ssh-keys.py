import pyqrcode

with open("~/.ssh/id_rsa.pub", "r") as f:
  key = f.read()
  qr = pyqrcode.create(key)
  print(qr.terminal())
