'''
Created on 14.06.2019

Use this as a cheat sheet for setting up new modules.
Modules are contained in the 'modules' directory, one folder per module, consisting of at least the view.py file.

Required fields:
 - MAIN_WIDGET must be assigned a class extending the QWidget class
 
Optional fields:
 - TITLE:str will be the title of the tab in the core UI, defaults to module descriptor (i.e. directory name)

@author: Maximilian Pensel
'''
from core.QtExtensions import VerticalContainer, HorizontalContainer, FileOpenPushButton

from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit

'''
The main widget.
Sets up the layout and components of this widget. Not required to be VerticalContainer.
'''
class TemplateWidget(VerticalContainer):
    
    def __init__(self):
        ''' Initialises the components of this widget with their layout '''
        super().__init__()
        
        ## setup gui elements
        label = QLabel("Setup your GUI elements here ...")
        
        file_input_label = QLabel("Such as a file input: ")
        file_input = QLineEdit()
        file_input_button = FileOpenPushButton(hook_field=file_input)
        
        file_input_horizontal = HorizontalContainer()
        file_input_horizontal.addWidget(file_input_label)
        file_input_horizontal.addWidget(file_input)
        file_input_horizontal.addWidget(file_input_button)
               
        text_area = QPlainTextEdit(
"""\
- Define and setup your layout
- Import more python modules from your own modules directory
- Check out the core extensions of the Qt-Framework, e.g. VerticalContainer, HorizontalContainer, FileOpenPushButton
- It is recommended to use MVC pattern
- Don't forget to activate your module in settings.ini
""")
        
        self.addWidget(label)
        self.addWidget(file_input_horizontal)
        self.addWidget(text_area)
        


TITLE       = "Template"
MAIN_WIDGET = TemplateWidget
VERSION     = "1.0.0"