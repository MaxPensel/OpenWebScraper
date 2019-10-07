"""
Created on 27.05.2019

@author: Maximilian Pensel

Copyright 2019 Maximilian Pensel <maximilian.pensel@gmx.de>

This file is part of OpenWebScraper.

OpenWebScraper is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenWebScraper is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenWebScraper.  If not, see <https://www.gnu.org/licenses/>.
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QFileDialog, QBoxLayout, QMessageBox
from PyQt5.QtWidgets import QLayout, QVBoxLayout, QHBoxLayout


class ArrangedContainer(QWidget):
    
    def __init__(self, layout: QBoxLayout = QVBoxLayout()):
        super().__init__()
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
    
    def addWidget(self, widget: QWidget):
        self.layout().addWidget(widget)
        
    def addLayout(self, layout: QLayout):
        self.layout().addLayout(layout)


class HorizontalContainer(ArrangedContainer):
    
    def __init__(self):
        super().__init__(QHBoxLayout())


class VerticalContainer(ArrangedContainer):
    
    def __init__(self):
        super().__init__(QVBoxLayout())


class FileOpenPushButton(QPushButton):
    
    def __init__(self,
                 hook_field: QLineEdit = None,
                 hook=None,
                 title: str = "Open",
                 mode: QFileDialog.FileMode = QFileDialog.AnyFile):
        super().__init__(title)
        self._hook_field = hook_field
        if not callable(hook) and hook_field is not None:
            self._hook = self.fill_field
        
        self.clicked.connect(self.on_click)
        
        self._dialog = QFileDialog(self)
        self._dialog.setFileMode(mode)
        self._dialog.setDirectory(".")
        if mode == QFileDialog.Directory:
            self._dialog.setOption(QFileDialog.ShowDirsOnly)
    
    def on_click(self):
        if self._dialog.exec_():
            file_name = self._dialog.selectedFiles()[0]
            if callable(self._hook):
                self._hook(file_name)
    
    def fill_field(self, path):
        """ Fill the hook_field (if given and of type QLineEdit) with the selected file/path """
        self._hook_field.setText(path)


class SimpleMessageBox(QMessageBox):

    def __init__(self, title, text, details="", icon=None):
        super().__init__()
        self.setIcon(icon)
        self.setText(text)
        self.setInformativeText(details)
        self.setWindowTitle(title)


class SimpleYesNoMessage(SimpleMessageBox):

    def __init__(self, title, text, details=""):
        super().__init__(title, text, details, QMessageBox.Question)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    def is_confirmed(self) -> bool:
        return self.exec_() == QMessageBox.Ok


class SimpleErrorInfo(SimpleMessageBox):

    def __init__(self, title, text, details=""):
        super().__init__(title, text, details, QMessageBox.Critical)
        self.setStandardButtons(QMessageBox.Ok)
