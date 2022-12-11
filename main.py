from biotext import BioText, TextStyle

from PyQt5.QtWidgets import QApplication
from sys import argv

style = TextStyle()
style.fontsize = 100
style.xPos = 99
style.yPos = 50

app = QApplication(argv)
win = BioText(style)

win.textEdit.setText('''ACDCDC
DC
CD CDCD

CDADCA

CAD CAD
CAD CAD
CAD CAD
CAD
CAD CAD
CAD CAD
CAD
CAD CAD 

CAD CAD
CAD CAD
CAD CAD
CAD''')
win.open_image(path = 'test-image.png')
win.show()
app.exec_()