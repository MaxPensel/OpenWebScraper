"""
Created on 14.06.2019

Use this as a cheat sheet for setting up the layout of the main widget of a module.
See __init__.py for information on how to setup modules.

@author: Maximilian Pensel
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
