""""
Created on 27.08.2019

Use this as a cheat sheet for setting up new modules.
Modules are contained in the 'modules' directory, one folder per module, consisting of at least the __init__.py file.

Required fields:
 - MAIN_WIDGET must be assigned a class extending the QWidget class

Optional fields:
 - TITLE:str will be the title of the tab in the core UI, defaults to module descriptor (i.e. directory name)

@author: Maximilian Pensel
"""

from modules.template.view import TemplateWidget

TITLE = "Template"
MAIN_WIDGET = TemplateWidget
VERSION = "1.1.0"
