'''
Created on 27.05.2019

@author: Maximilian Pensel
'''

import os
#from modules.crawler_view import CrawlerWidget

class CrawlerController():
    
    def __init__(self, view):
        self._view = view
        
        self.init_elements()
        
        self.setup_behaviour()
    
    def init_elements(self):
        ''' sets up the initial state of the elements
        
        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        
        '''
        
        self._view._blacklist_save.setEnabled(False)
        self._view._url_save.setEnabled(False)

    def setup_behaviour(self):
        ''' Setup the behaviour of elements
        
        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        '''
        
        self._view._url_load.clicked.connect(self.load_file)
        #self._view._blacklist_load.clicked.connect(lambda:self.load_file(self._view._blacklist_load.displayText(), self._view._blacklist_area))
    
    def load_file(self):
        path = self._view._url_load.displayText()
        area = self._view._url_area
        #path = input.displayText()
        #if os.path.exists(self._view._url_input.displayText()):
        try:
            with open(path) as in_file:
                area.setPlainText(in_file.read())
        except IOError as err:
            print(err)
        #else:
        #    print("File not found.")

def CrawlerWrapper():
    
    def __init__(self):
        pass