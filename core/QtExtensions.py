"""
Created on 27.05.2019

@author: Maximilian Pensel
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QFileDialog, QBoxLayout, QMessageBox, QAbstractButton
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

    def __init__(self, title, text, icon):
        super().__init__()
        self.setIcon(icon)
        self.setText(title)
        self.setInformativeText(text)
        self.setWindowTitle(title)


class SimpleYesNoMessage(SimpleMessageBox):

    def __init__(self, title, text):
        super().__init__(title, text, QMessageBox.Question)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    def is_confirmed(self) -> bool:
        return self.exec_() == QMessageBox.Ok


class SimpleErrorInfo(SimpleMessageBox):

    def __init__(self, title, text):
        super().__init__(title, text, QMessageBox.Critical)
        self.setStandardButtons(QMessageBox.Ok)
