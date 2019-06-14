'''
Created on 27.05.2019

@author: Maximilian Pensel
'''

from core.QtExtensions import VerticalContainer

class ConverterWidget(VerticalContainer):
    
    def __init__(self):
        super().__init__()


TITLE = "Converter"
MAIN_WIDGET = ConverterWidget