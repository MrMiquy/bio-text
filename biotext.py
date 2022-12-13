from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtGui import QPixmap
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import QBuffer
from window import Ui_MainWindow
import io

from PIL import Image, ImageDraw, ImageFilter
from PIL.ImageQt import ImageQt
from random import randint
import math
import functools

from style import TextStyle
from letterset import letter_set

def ave(p1: tuple, p2: tuple):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    
class TextDraw():
    def __init__(self, style: TextStyle):
        self.im = None
        self.canvas = None
        self.last_pos = []
        self.x_margin, self.y_margin = 0, 0
        if style:
            self.style = style
        else:
            self.style = TextStyle()

    def func(self, cords: list, t):
        new_cords = []
        for cord in cords:
            new_cords.append(((cord[0] * self.style.get_size()) / 100 + self.x_margin, (cord[1] * self.style.get_size()) / 100))

        cords = new_cords
        return (
            math.pow((1 - t), 3) * cords[0][0] + 3* math.pow((1-t), 2) * t * cords[1][0] + 3 * (1-t)*math.pow(t, 2) * cords[2][0] + math.pow(t, 3) * cords[3][0],
            math.pow((1 - t), 3) * cords[0][1] + 3* math.pow((1-t), 2) * t * cords[1][1] + 3 * (1-t)*math.pow(t, 2) * cords[2][1] + math.pow(t, 3) * cords[3][1]
        )
    
    def bezier(self, cords: list):
        for cord in cords:
            curve = []
            t = 0
            while (t < 1):
                curve.append(self.func(cord, t))
                t += 0.01

            while (t > 0):
                bezier = self.func(cord, t)
                curve.append((bezier[0] + self.style.get_thickness(), bezier[1] + math.pow(self.style.get_thickness(), math.cos(t))))
                t -= 0.01

            self.last_pos = [curve[-1][0], curve[-1][1]]
            self.canvas.polygon(curve, self.style.color)

    def divide_func(self, xy0, xym, xy: tuple, xy2: tuple):
        return (ave(xy0, xym, xy[0], xy[1]), ave(xy0, xym, xy2[0], xy2[1]))

    def divide(self, cords: list, divides):
        new_cords = []
        if divides > 0:
            for cord in cords:
                cords_list = []
                cords_list.append((cord[0][0]+self.style.get_curl(), cord[0][1]+self.style.get_curl()))
                cords_list.append(ave(cord[0], cord[1]))
                cords_list.append((cord[1][0]+self.style.get_curl(), cord[1][1]+self.style.get_curl()))
                cords_list.append(ave(cord[1], cord[2]))
                new_cords.append(cords_list)

                cords_list = []
                cords_list.append(ave(cord[1], cord[2]))
                cords_list.append((cord[2][0]+self.style.get_curl(), cord[2][1]+self.style.get_curl()))
                cords_list.append(ave(cord[2], cord[3]))
                cords_list.append((cord[3][0]+self.style.get_curl(), cord[3][1]+self.style.get_curl()))
                new_cords.append(cords_list)
                
            return self.divide(new_cords, divides-1)
        return cords

    def curve(self, cords: list, divide = 0):
        self.bezier(self.divide(cords, divide))

    def continue_(self, cords: list, divide = 0):
        cords[0][0] = (self.last_pos[0] - self.style.get_size(), self.last_pos[1])
        self.curve(cords, divide)

    def draw(self, string: str, divides: int = 0, is_export = False):
        self.style.set_export(is_export)
    
        w = len(string) * self.style.get_size()
        h = self.style.get_size() + self.style.get_curl()
        self.x_margin, self.y_margin = 0, 0

        self.im = Image.new("RGBA", (w, h), color=(0,0,0,0))
        self.canvas = ImageDraw.Draw(self.im, "RGBA")
        self.canvas.rectangle((0,0,w,h), (70, 0, 0, 60))

        for char in string:
            if char in letter_set.keys():
                try:
                    self.curve(letter_set[char]["curve"], letter_set[char]["divide"] + divides)
                except:
                    try:
                        self.continue_(letter_set[char]["curve1"], letter_set[char]["divide"] + divides)
                    except:
                        pass
                self.x_margin += self.style.get_size() / 2

        if is_export:
            blur = self.im.filter(ImageFilter.GaussianBlur(2))
            print("export")
            self.im.paste(blur)
            self.im = self.im.resize((w // self.style.is_export, h // self.style.is_export), Image.BICUBIC)
        else:
            self.im = self.im.filter(ImageFilter.SMOOTH_MORE)

        self.style.set_export(False)
        return self.im

class BioText(Ui_MainWindow, QMainWindow):
    def __init__(self, text_style: TextStyle = None):
        super(Ui_MainWindow, self).__init__()
        self.ui = self.setupUi(self)
        self.source = None
        self.draw = TextDraw(text_style)                 # TextDraw Class   // text render class
        self.image_fullsize = True
        
        if text_style:
            self.sSize.setValue(text_style.fontsize)
            self.sCursive.setValue(text_style.cursive)
            self.sThickness.setValue(text_style.thickness)
            self.sCurl.setValue(text_style.curl)

            self.sXPos.setValue(text_style.xPos)
            self.sYPos.setValue(text_style.yPos)

        # connections / signals
        self.textEdit.textChanged.connect(self.text_changed)
        # source image (AKA user image)
        self.lImage.mousePressEvent = self.open_image
        self.lImage.resizeEvent = self.resize_source_image
        # actions
        self.actionExport.triggered.connect(self.export)
        self.actionQuit.triggered.connect(self.quit)
        self.actionText.triggered.connect(self.save_text)
        self.actionFullsize_Image.triggered.connect(self.open_image)

        # spinboxes -- Style
        self.sSize.valueChanged.connect(self.fontsize_changed)
        self.sCursive.valueChanged.connect(self.spinbox_changed)
        self.sThickness.valueChanged.connect(self.thickness_changed)
        self.sCurl.valueChanged.connect(self.curl_changed)

        self.sSizeMin.valueChanged.connect(self.random_fontsize_changed)
        self.sSizeMax.valueChanged.connect(self.random_fontsize_changed)
        self.sCursiveMin.valueChanged.connect(self.random_cursive_changed)
        self.sCursiveMax.valueChanged.connect(self.random_cursive_changed)
        self.sThicknessMin.valueChanged.connect(self.random_thickness_changed)
        self.sThicknessMax.valueChanged.connect(self.random_thickness_changed)
        self.sCurlMin.valueChanged.connect(self.random_curl_changed)
        self.sCurlMax.valueChanged.connect(self.random_curl_changed)
        self.sDivide.valueChanged.connect(self.spinbox_changed)
        
        # spinboxes -- Text
        self.sXPos.valueChanged.connect(self.xPos_changed)
        self.sYPos.valueChanged.connect(self.yPos_changed)
        self.sWidth.valueChanged.connect(self.spinbox_changed)
        self.sHeight.valueChanged.connect(self.spinbox_changed)
        self.ax1.valueChanged.connect(self.spinbox_changed)

    def redraw_overlay(self):
        if self.source:
            if self.textEdit.toPlainText():
                y_margin = 0
                source = self.source.copy()
                for string in self.textEdit.toPlainText().split('\n'):
                    overlay = self.draw.draw(string, self.sDivide.value())
                    source.paste(overlay, (self.sXPos.value(), self.sYPos.value() + y_margin), overlay)
                    y_margin += self.draw.style.fontsize
                source = ImageQt(source)

                pixmap = QPixmap.fromImage(source)
                if not self.image_fullsize:
                    pixmap = pixmap.scaled(self.frame_2.width() - 20, self.frame_2.height() - 30, QtCore.Qt.KeepAspectRatio)
                self.lImage.setPixmap(pixmap)

    def open_image(self, event = None, path = None):
        if not self.source:
            if not path:
                imagePath, _ = QFileDialog.getOpenFileName()
            else:
                imagePath = path
            if imagePath:
                source_image = QPixmap(imagePath)
                if not source_image.isNull():
                    self.actionFullsize_Image.setEnabled(True)
                    self.source = QPixmap.toImage(source_image)
                    buffer = QBuffer()
                    buffer.open(QBuffer.ReadWrite)
                    self.source.save(buffer, 'PNG')
                    self.source = Image.open(io.BytesIO(buffer.data()))
                    if self.draw.style.fontsize == 0:
                        self.draw.style.fontsize = self.source.height // 20
                        self.sSize.setValue(self.draw.style.fontsize)
                    self.resize_source_image()
        else:
            self.image_fullsize = not self.image_fullsize
            self.resize_source_image()
    
    def resize_source_image(self, event = None):
        if self.source:
            self.redraw_overlay()

    def export(self):
        if self.source and self.textEdit.toPlainText():
            imagePath, _ = QFileDialog.getSaveFileName(self,"Export to...","","png;;jpg;;gif;;bpm;;jpeg;;webp")

            if imagePath:
                y_margin = 0
                source = self.source.copy()
                for string in self.textEdit.toPlainText().split('\n'):
                    overlay = self.draw.draw(string, self.sDivide.value(), is_export=True)
                    source.paste(overlay, (self.sXPos.value(), self.sYPos.value() + y_margin), overlay)
                    y_margin += self.draw.style.fontsize

                _ = _.strip()
                if _ in ['jpg', 'jpeg', 'bmp']:
                    source = source.convert('RGB')
                source.save(imagePath + "." + _)

    def save_text(self):
        if self.textEdit.toPlainText():
            f = open("text.txt", "w")
            f.write(self.textEdit.toPlainText())
            f.close()

    def quit(self):
        self.close()

    def text_changed(self):
        self.redraw_overlay()

    def value_changed(method):
        @functools.wraps(method)
        def wrapper(self):
            try: 
                method(self)
                self.redraw_overlay()
            except:
                pass
        return wrapper

    @value_changed
    def spinbox_changed(self):
        pass

    @value_changed
    def fontsize_changed(self):
        self.draw.style.fontsize = self.sSize.value()

    @value_changed
    def cursive_changed(self):
        self.draw.style.cursive = self.sCursive.value()

    @value_changed
    def thickness_changed(self):
        self.draw.style.thickness = self.sThickness.value()

    @value_changed
    def curl_changed(self):
        self.draw.style.curl = self.sCurl.value()

    @value_changed
    def xPos_changed(self):
        self.draw.style.xPos = self.sXPos.value()

    @value_changed
    def yPos_changed(self):
        self.draw.style.yPos = self.sYPos.value()

    @value_changed
    def random_fontsize_changed(self):
        self.draw.style.random.fontsize = [self.sSizeMin.value(), self.sSizeMax.value()]

    @value_changed
    def random_cursive_changed(self):
        self.draw.style.random.cursive = [self.sCursiveMin.value(), self.sCursiveMax.value()]

    @value_changed
    def random_thickness_changed(self):
        self.draw.style.random.thickness = [self.sThicknessMin.value(), self.sThicknessMax.value()]

    @value_changed
    def random_curl_changed(self):
        self.draw.style.random.curl = [self.sCurlMin.value(), self.sCurlMax.value()]