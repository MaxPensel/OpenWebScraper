'''
Created on 27.05.2019

@author: Maximilian Pensel
'''

from core.QtExtensions import VerticalContainer, FileOpenPushButton
from PyQt5.QtWidgets import QLabel, QLineEdit
from PyQt5.QtWidgets import QHBoxLayout

class FilterWidget(VerticalContainer):
    
    def __init__(self):
        super().__init__()
        
        self._dir_input_label = QLabel("Input directory:")
        self._dir_input       = QLineEdit()
        self._dir_input_open  = FileOpenPushButton(hook_field=self._dir_input)
        
        dir_input_layout = QHBoxLayout()
        dir_input_layout.addWidget(self._dir_input_label)
        dir_input_layout.addWidget(self._dir_input)
        dir_input_layout.addWidget(self._dir_input_open)
        
        self.addLayout(dir_input_layout)
