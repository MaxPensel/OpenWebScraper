'''
Created on 27.05.2019

@author: Maximilian Pensel
'''

import os
import sys
import traceback
import subprocess
from crawlUI import ModLoader
#from modules.crawler_view import CrawlerWidget

class CrawlerController():
    
    MOD_PATH     = os.path.join(ModLoader.MOD_DIR, "crawler")
    RUNNING_DIR  = "running"
    RUNNING_PATH = os.path.join(MOD_PATH, RUNNING_DIR)
    
    
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
        self._view._crawl_button.clicked.connect(self.start_crawl)
        #self._view._blacklist_load.clicked.connect(lambda:self.load_file(self._view._blacklist_load.displayText(), self._view._blacklist_area))
    
    def find_running(self):
        if os.path.exists(self.RUNNING_PATH):
            return os.listdir(self.RUNNING_PATH)
        else:
            return []
    
    def add_running(self):
        running_crawl_dirs = self.find_running()
        if len(running_crawl_dirs) == 0:
            nxt = 0
        else:
            nums = list(map(lambda x: int(x.split("_")[1]), running_crawl_dirs))
            nxt = max(nums)+1
        
        nxt = "crawl_{0}".format(nxt)
        
        try:
            if not os.path.exists(self.RUNNING_PATH):
                os.makedirs(self.RUNNING_PATH)
            new_running_dir = os.path.join(self.RUNNING_PATH, nxt)
            os.mkdir(new_running_dir)
            
            return nxt
        except Exception as exc:
            print(traceback.format_exc())
            print(exc)
        
        return None # something went wrong
        
    
    def load_file(self):
        path = self._view._url_input.displayText()
        area = self._view._url_area
        
        try:
            with open(path) as in_file:
                area.setPlainText(in_file.read())
        except IOError as err:
            print(err, file=sys.stderr)
        except Exception as exc:
            print(traceback.format_exc())
            print(exc)
    
    def start_crawl(self):
        run_dir = self.add_running()
        print("Starting {0} ..".format(run_dir))
        try:
            subprocess.Popen(["python", "scrapy_wrapper.py", os.path.join(self.RUNNING_DIR, run_dir)],
                             stdout=subprocess.PIPE,
                             shell=True,
                             start_new_session=True,
                             cwd="modules/crawler/",
                             creationflags=subprocess.DETACHED_PROCESS,
                             close_fds=True)
        except Exception as exc:
            print(traceback.format_exc())
            print(exc)
    
def CrawlerWrapper():
    
    def __init__(self):
        pass