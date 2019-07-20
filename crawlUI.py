"""
Created on 24.05.2019

@author: Maximilian Pensel
"""

import importlib
import os
import json
from PyQt5.QtWidgets import QTabWidget, QApplication, QMainWindow, QWidget, QToolBar, QPushButton, QSizePolicy,\
    QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets

VERSION = "1.1.0"


class MainWidget(QTabWidget):

    def __init__(self, parent):
        """" Setup UI structure in reverse """
        super().__init__(parent)
        
        self.main_window = parent
        self.info_window = None
        
        parent.setCentralWidget(self)
        
        parent.setStyleSheet(open("style.css").read())
        
        self.init_toolbar()
    
    def register_modules(self, modules: {}):
        for module in modules:
            self.addTab(module.MAIN_WIDGET(), module.TITLE)
    
    def init_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        toolbar.addWidget(spacer)
        
        info_button = QPushButton()
        info_button.setStyleSheet("""
        QPushButton {
            padding: 3px;
            background: none;
            border: none;
            width: 15px;
            height: 15px;
        }
        """)
        info_button.setIcon(QIcon("resources/info.png"))
        
        
        info_button.clicked.connect(self.info_button_click)
                
        toolbar.addWidget(info_button)
        
        self.main_window.addToolBar(toolbar)
    
    def info_button_click(self):
        if self.info_window is None:
            self.info_window = InfoWindow(self)

        if not self.info_window.isVisible():
            self.info_window.show()


class InfoWindow(QMainWindow):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        global VERSION
        
        self.setWindowTitle("Info")
        self.setWindowIcon(QIcon("resources/info.png"))
        
        versions = {}
        for mod_dir in os.listdir(ModLoader.MOD_DIR):
            if os.path.exists(os.path.join(ModLoader.MOD_DIR, mod_dir, "view.py")):
                try:
                    mod = importlib.import_module(ModLoader.MOD_DIR + "." + mod_dir + ".view",
                                                  ModLoader.MOD_DIR + "." + mod_dir)
                    if hasattr(mod, "VERSION"):
                        versions[mod_dir] = "v{0}".format(mod.VERSION)
                    else:
                        versions[mod_dir] = "- not supported -"
                except Exception as er:
                    print(er)
        
        central = QTableWidget()
        central.setColumnCount(2)
        central.setRowCount(2 + len(versions))
        
        central.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        central.horizontalHeader().hide()
        central.verticalHeader().hide()
        central.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        central.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        
        central.setItem(0, 0, QTableWidgetItem("Version of core module:"))
        central.setItem(0, 1, QTableWidgetItem("v{0}".format(VERSION)))
        
        central.setItem(1, 0, QTableWidgetItem())
        central.setItem(1, 1, QTableWidgetItem())
        
        row = 2        
        for mod, version in versions.items():
            central.setItem(row, 0, QTableWidgetItem("Version of moule {0}:".format(mod)))
            central.setItem(row, 1, QTableWidgetItem(version))
            
            row += 1
        
        for i in range(central.rowCount()):
            for j in range(central.columnCount()):
                central.item(i, j).setFlags(Qt.ItemIsEnabled) 
                # central.item(i, j).setFlags(Qt.ItemIsSelectable)

        self.setCentralWidget(central)


class ModLoader:

    MOD_DIR = "modules"

    def __init__(self):
        self.modules = []

    def load_modules(self, mods: {}):

        for modname in mods:
            try: 
                mod = importlib.import_module(ModLoader.MOD_DIR + "." + modname + ".view",
                                              ModLoader.MOD_DIR + "." + modname)
                
                if not hasattr(mod, "TITLE"):
                    mod.TITLE = modname
                
                if hasattr(mod, "MAIN_WIDGET"):
                    self.modules.append(mod)
                else:
                    raise AttributeError("view.py in {0} is missing MAIN_WIDGET attribute".format(modname))
                
            except Exception as ex:
                print("{0}: {1}".format(type(ex).__name__, ex))
                

class Settings:
    
    def __init__(self, settings_file_path: str):
        # init always relevant settings
        self.modules = []
        
        if not os.path.exists(settings_file_path):
            print("{0} not found, loading defaults.".format(settings_file_path))
        else:
            with open(settings_file_path, "r") as settings_file:
                l_num = 0
                for line in settings_file.readlines():
                    l_num += 1
                    try:
                        self.parse_line(line)
                    except IndexError or TypeError or json.JSONDecodeError:
                        print("Bad format in line {0} in settings file. Format should be 'key=value', where 'key' is "
                              "a string and 'value' a json-string.".format(l_num))

        self.defaults()  # adds the defaults for missing but expected fields
    
    def parse_line(self, line: str):
        line = line.lstrip()
        if not Settings.is_line_comment(line):
            key_value = line.split("=")
            setattr(self, key_value[0], json.loads(key_value[1]))
        
    @staticmethod
    def is_line_empty(line: str) -> bool:
        return len(line) == 0
    
    @staticmethod
    def is_line_comment(line) -> bool:
        return Settings.is_line_empty(line) or line[0] == "#"
    
    def defaults(self):
        if not self.modules:  # has no modules specified
            self.modules = ["template"]


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
    main_window.setWindowTitle("SpiderGUI")
    
    main_window.show()
    sys.exit(app.exec_())