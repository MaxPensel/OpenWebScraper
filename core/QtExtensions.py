'''
Created on 27.05.2019

@author: Maximilian Pensel
'''

from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QFileDialog
from PyQt5.QtWidgets import QLayout, QVBoxLayout, QHBoxLayout

class ArrangedContainer(QWidget):
    
    def __init__(self, layout=QVBoxLayout()):
        super().__init__()
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)
    
    def addWidget(self, widget : QWidget):
        self.layout().addWidget(widget)
        
    def addLayout(self, layout :QLayout):
        self.layout().addLayout(layout)

class HorizontalContainer(ArrangedContainer):
    
    def __init__(self):
        super().__init__(QHBoxLayout())

class VerticalContainer(ArrangedContainer):
    
    def __init__(self):
        super().__init__(QVBoxLayout())

class FileOpenPushButton(QPushButton):
    
    def __init__(self, 
                 hook_field : QLineEdit = None,
                 hook = None,
                 title : str = "Open",
                 type  : str = "any"):
        super().__init__(title)
        self._hook_field = hook_field
        if not callable(hook) and not hook_field == None:
            self._hook = self.fill_field
        
        self.clicked.connect(self.on_click)
    
    def on_click(self):
        fileInput = QFileDialog.getOpenFileName(parent=self, caption="Open Image", directory=".", filter="", options=QFileDialog.ReadOnly);
        fileName = fileInput[0]
        if callable(self._hook):
            self._hook(fileName)
    
    def fill_field(self, path):
        ''' Fill the hook_field (if given and of type QLineEdit) with the selected file/path '''
        self._hook_field.setText(path)