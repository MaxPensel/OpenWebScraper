"""
Use this as a cheat sheet for setting up the layout of the main widget of a module.
See __init__.py for information on how to setup modules.

Created on 14.06.2019

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
from core.QtExtensions import VerticalContainer, HorizontalContainer, FileOpenPushButton

from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit
import core

LOG = core.simple_logger(modname="template", file_path=core.MASTER_LOG)


class TemplateWidget(VerticalContainer):
    """
    The main widget.
    Sets up the layout and components of this widget. Not required to be VerticalContainer.
    """

    def __init__(self):
        """ Initialises the components of this widget with their layout """
        super().__init__()
        LOG.info("Initialising template module (and showing off simple logging).")
        
        # setup gui elements
        label = QLabel("Setup your GUI elements here ...")
        
        file_input_label = QLabel("Such as a file input: ")
        file_input = QLineEdit()
        file_input_button = FileOpenPushButton(hook_field=file_input)
        
        file_input_horizontal = HorizontalContainer()
        file_input_horizontal.addWidget(file_input_label)
        file_input_horizontal.addWidget(file_input)
        file_input_horizontal.addWidget(file_input_button)
               
        text_area = QPlainTextEdit("""\
- Define and setup your layout
- Import more python modules from your own modules directory
- Check out the core extensions of the Qt-Framework, e.g. VerticalContainer, HorizontalContainer, FileOpenPushButton
- It is recommended to use MVC pattern
- Don't forget to activate your module in settings.ini\
""")
        
        self.addWidget(label)
        self.addWidget(file_input_horizontal)
        self.addWidget(text_area)
