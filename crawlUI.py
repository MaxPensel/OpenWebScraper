'''
Created on 24.05.2019

@author: Maximilian Pensel
'''

import importlib
import os
import json
from PyQt5.QtWidgets import QTabWidget, QApplication, QMainWindow


class MainWidget(QTabWidget):
        
    def __init__(self, parent):
        ''' Setup UI structure in reverse '''
        super().__init__(parent)
        
        parent.setCentralWidget(self)
        
        parent.setStyleSheet(open("style.css").read())
    
    def register_modules(self, modules:{}):
        for module in modules:
            self.addTab(module.MAIN_WIDGET(), module.TITLE)

class ModLoader():

    def __init__(self):
        self.mod_dir = "modules"
        
    def load_modules(self, mods:{}):
        self.modules = []
        for modname in mods:
            try: 
                mod = importlib.import_module(self.mod_dir + "." + modname + ".view", self.mod_dir + "." + modname)
                
                if not hasattr(mod, "TITLE"):
                    mod.TITLE = modname
                
                if hasattr(mod, "MAIN_WIDGET"):
                    self.modules.append(mod)
                else:
                    raise AttributeError("view.py in {0} is missing MAIN_WIDGET attribute".format(modname))
                
            except Exception as ex:
                print("{0}: {1}".format(type(ex).__name__, ex))
                

class Settings():
    
    def __init__(self, settings_file:str):
        if not os.path.exists(settings_file):
            print("{0} not found, loading defaults.".format(settings_file))
        else:
            with open(settings_file, "r") as settings:
                l_num = 0
                for line in settings.readlines():
                    l_num += 1
                    try:
                        self.parse_line(line)
                    except:
                        print("Bad format in line {0} in settings file. Format should be 'key=value', where 'key' is a string and 'value' a json-string.".format(l_num))
                    
        
        self.defaults() # adds the defaults for missing but expected fields
    
    def parse_line(self, line:str):
        line = line.lstrip()
        if not self.is_line_comment(line):
            key_value = line.split("=")
            setattr(self, key_value[0], json.loads(key_value[1]))
        
    def is_line_empty(self, line:str) -> bool:
        return len(line) == 0
    
    def is_line_comment(self, line) -> bool:
        return self.is_line_empty(line) or line[0] == "#"
    
    def defaults(self):
        if not hasattr(self, "modules"):
            self.modules = ["crawler"]


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    settings = Settings("settings.ini")
    
    main_window = QMainWindow()
    ui = MainWidget(main_window)
    
    mod_loader = ModLoader()
    mod_loader.load_modules(settings.modules)
    
    ui.register_modules(mod_loader.modules)
    
    
    main_window.setGeometry(200, 200, 800, 500)
    main_window.setWindowTitle("Spider Crawler Manager")
    main_window.show()
    sys.exit(app.exec_())