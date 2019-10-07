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
