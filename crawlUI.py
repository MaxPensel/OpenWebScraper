"""
Created on 24.05.2019

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

import importlib
import sys
import os
import json
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTabWidget, QApplication, QMainWindow, QSizePolicy, \
    QTableWidget, QTableWidgetItem, QAction, QFileDialog, QWidget, QLabel, QFrame
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import core
from core.QtExtensions import VerticalContainer
from core.Workspace import WorkspaceManager

VERSION = "0.4.0 <beta>"
COPYRIGHT = "2019 Maximilian Pensel"

LOG = core.simple_logger(file_path=core.MASTER_LOG)


class UIWindow(QMainWindow):

    def __init__(self, settings):
        super().__init__()

        self.main_widget = MainWidget(self)
        self.info_window = None

        self.mod_loader = ModLoader()
        self.mod_loader.load_modules(settings.modules)

        self.main_widget.register_modules(self.mod_loader.modules)

        self.init_menu()

        self.setWindowTitle("OpenWebScraper")

    def init_menu(self):
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        help_menu = main_menu.addMenu("Help")

        # File > Switch Workspace ...
        workspace_button = QAction('Switch Workspace ...', self)
        workspace_button.setStatusTip('Switch the current workspace.')
        workspace_button.triggered.connect(self.switch_workspace)
        file_menu.addAction(workspace_button)

        # File > Exit
        exit_button = QAction('Exit', self)
        exit_button.setShortcut('Ctrl+Q')
        exit_button.setStatusTip('Exit')
        exit_button.triggered.connect(self.close)
        file_menu.addAction(exit_button)

        # Help > Info
        info_button = QAction('About', self)
        info_button.setStatusTip('Show an info window containing license, copyright and version information.')
        info_button.triggered.connect(self.info_button_click)
        help_menu.addAction(info_button)

    def info_button_click(self):
        if self.info_window is None:
            self.info_window = AboutWindow(self)

        if not self.info_window.isVisible():
            self.info_window.show()

    def switch_workspace(self):
        wsm = WorkspaceManager()

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        if wsm.is_workspace_selected():
            dialog.setDirectory(os.path.split(wsm.get_workspace())[0])
        else:
            dialog.setDirectory(os.getcwd())

        if dialog.exec_():
            ws_path = dialog.selectedFiles()[0]
            wsm.set_workspace(ws_path)
        else:
            LOG.error("Something went wrong when switching workspace.")

        self.main_widget.reload_modules(self.mod_loader.modules)


class MainWidget(QTabWidget):

    def __init__(self, parent):
        """" Setup UI structure in reverse """
        super().__init__(parent)
        
        self.main_window = parent
        
        parent.setCentralWidget(self)
        
        parent.setStyleSheet(open("style.css").read())
        # parent.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    def register_modules(self, modules: {}):
        for module in modules:
            self.addTab(getattr(module, "MAIN_WIDGET")(), module.TITLE)

    def reload_modules(self, modules: {}):
        for i in range(self.count()):
            self.removeTab(0)

        for module in modules:
            self.addTab(module.MAIN_WIDGET(), module.TITLE)


class AboutWindow(QMainWindow):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        global VERSION
        
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon("resources/info.png"))

        # collect data from modules
        mod_data = dict()
        for mod_dir in os.listdir(ModLoader.MOD_DIR):
            if os.path.exists(os.path.join(ModLoader.MOD_DIR, mod_dir, "__init__.py")):
                try:
                    mod = importlib.import_module(ModLoader.MOD_DIR + "." + mod_dir,
                                                  ModLoader.MOD_DIR + "." + mod_dir)
                    if hasattr(mod, "VERSION"):
                        version = getattr(mod, "VERSION")
                    else:
                        version = "- not supported -"

                    if hasattr(mod, "COPYRIGHT"):
                        cpright = getattr(mod, "COPYRIGHT")
                    else:
                        cpright = "- not specified -"

                    mod_data[mod_dir] = (version, cpright)
                except Exception as exc:
                    LOG.exception("{0}: {1}".format(type(exc).__name__, exc))
        # also collect core data
        core_data = (VERSION, COPYRIGHT)

        # Info text and license notice
        copyright_label = QLabel("""\
<h1>OpenWebScraper</h1>
<p>This software is free of use, modification and redistribution \
under the terms of the GNU General Public License version 3 as \
published by the Free Software Foundation. \
Either see the COPYING file contained in this repository or \
<a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a> \
for a full version of the GPLv3 license.</p><p>\
The copyright notice and version info for each of the contained modules \
is found in the table below. The core module is considered to comprise all \
source files outside of the <i>modules</i> directory.</p>
""")
        copyright_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        copyright_label.setAlignment(Qt.AlignBottom | Qt.AlignCenter)
        copyright_label.setWordWrap(True)
        copyright_label.setMargin(10)

        # version table
        version_table = QTableWidget()
        version_table.setColumnCount(3)
        version_table.setRowCount(len(mod_data) + 1)
        
        version_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        version_table.setHorizontalHeaderItem(0, QTableWidgetItem("Module"))
        version_table.setHorizontalHeaderItem(1, QTableWidgetItem("Version"))
        version_table.setHorizontalHeaderItem(2, QTableWidgetItem("Copyright"))
        version_table.verticalHeader().hide()
        version_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        version_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        version_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        
        version_table.setItem(0, 0, QTableWidgetItem("core"))
        version_table.setItem(0, 1, QTableWidgetItem(core_data[0]))
        version_table.setItem(0, 2, QTableWidgetItem(core_data[1]))

        row = 1
        for mod_name in mod_data:
            version_table.setItem(row, 0, QTableWidgetItem(mod_name))
            version_table.setItem(row, 1, QTableWidgetItem(mod_data[mod_name][0]))
            version_table.setItem(row, 2, QTableWidgetItem(mod_data[mod_name][1]))
            
            row += 1
        
        for i in range(version_table.rowCount()):
            for j in range(version_table.columnCount()):
                version_table.item(i, j).setFlags(Qt.ItemIsEnabled)
                # version_table.item(i, j).setFlags(Qt.ItemIsSelectable)

        central = VerticalContainer()
        central.addWidget(copyright_label)
        central.addWidget(version_table)

        self.setCentralWidget(central)


class ModLoader:

    MOD_DIR = "modules"

    def __init__(self):
        self.modules = []

    def load_modules(self, mods: {}):
        LOG.info("Loading modules.")
        for modname in mods:
            try:
                mod = importlib.import_module(ModLoader.MOD_DIR + "." + modname,
                                              ModLoader.MOD_DIR + "." + modname)
                
                if not hasattr(mod, "TITLE"):
                    mod.TITLE = modname
                
                if hasattr(mod, "MAIN_WIDGET"):
                    widget_path = getattr(mod, "MAIN_WIDGET")
                    setattr(mod, "MAIN_WIDGET", core.get_class(widget_path))
                    # only load the module if MAIN_WIDGET is a QWidget:
                    if issubclass(getattr(mod, "MAIN_WIDGET"), QWidget):
                        self.modules.append(mod)
                    else:
                        LOG.error("{0} does not reference a class inheriting from QWidget.".format(widget_path))
                else:
                    raise AttributeError("__init__.py in {0} is missing MAIN_WIDGET attribute".format(modname))
                
            except Exception as exc:
                LOG.exception("{0}: {1}".format(type(exc).__name__, exc))
                

class Settings:
    
    def __init__(self, settings_file_path: str = "settings.ini"):
        # init always relevant settings
        self.modules = None
        self.venv = ""
        self.python = ""
        
        if not os.path.exists(settings_file_path):
            LOG.warning("{0} not found, loading defaults.".format(settings_file_path))
        else:
            LOG.info("Loading settings from {0}.".format(settings_file_path))
            with open(settings_file_path, "r") as settings_file:
                l_num = 0
                for line in settings_file.readlines():
                    l_num += 1
                    try:
                        self.parse_line(line)
                    except IndexError or TypeError or json.JSONDecodeError:
                        LOG.error("Bad format in line {0} of settings file. Format should be 'key=value', where 'key' "
                                  "is a string and 'value' a json-string.".format(l_num))

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
        if self.modules is None:  # has no modules specified
            self.modules = ["template"]
            LOG.info("Loading default setting: modules={0}".format(json.dumps(self.modules)))
        if not self.venv:  # has no modules specified
            self.venv = os.path.join(".", "venv")
        if not self.python:  # has no modules specified
            self.python = sys.executable


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = UIWindow(Settings())
    #window = AboutWindow()

    window.show()

    sys.exit(app.exec_())
