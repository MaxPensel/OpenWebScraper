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

import toml
APP_SETTINGS = toml.load("settings.toml")

import importlib
import sys
import os

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTabWidget, QApplication, QMainWindow, QSizePolicy, \
    QTableWidget, QTableWidgetItem, QAction, QFileDialog, QWidget, QLabel, QFrame
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import core
from core.QtExtensions import VerticalContainer
from core.Workspace import WorkspaceManager


class UIWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.main_widget = MainWidget(self)
        self.info_window = None

        self.init_menu()

        self.mod_loader = ModLoader(self)

        self.mod_loader.load_modules(APP_SETTINGS["general"]["modules"])

        self.main_widget.register_modules(self.mod_loader.modules)

        self.setWindowTitle("OpenWebScraper")

    def init_menu(self):
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        self.settings_menu = main_menu.addMenu("Settings")
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

        # Settings > Core
        self.register_settings("Core App", "settings.toml")
        self.settings_menu.addSeparator()

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
            core.MASTER_LOGGER.error("Something went wrong when switching workspace.")

        self.main_widget.reload_modules(self.mod_loader.modules)

    def register_settings(self, title, file):
        main_settings_button = QAction(title, self)
        main_settings_button.triggered.connect(
            lambda:
            core.QtExtensions.TomlConfigWindow.open_window.activateWindow() if core.QtExtensions.TomlConfigWindow.open_window
            else core.QtExtensions.TomlConfigWindow.create_window(file, parent=self)
        )
        self.settings_menu.addAction(main_settings_button)


class MainWidget(QTabWidget):

    def __init__(self, parent):
        """" Setup UI structure in reverse """
        super().__init__(parent)
        
        self.main_window = parent
        
        parent.setCentralWidget(self)
        
        parent.setStyleSheet(open("style.css").read())
        # parent.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        self.currentChanged.connect(lambda x: self.currentWidget().cnt.update_view())
    
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
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon("resources/info.png"))

        # collect data from modules
        mod_data = dict()
        for mod_dir in os.listdir(APP_SETTINGS["modloader"]["mod_dir"]):
            if os.path.exists(os.path.join(APP_SETTINGS["modloader"]["mod_dir"], mod_dir, "__init__.py")):
                try:
                    mod = importlib.import_module(APP_SETTINGS["modloader"]["mod_dir"] + "." + mod_dir,
                                                  APP_SETTINGS["modloader"]["mod_dir"] + "." + mod_dir)
                    if not hasattr(mod, "SETTINGS") or "general" not in mod.SETTINGS:
                        core.MASTER_LOGGER.warning("Your mod_dir contains modules that are "
                                                   "probably not set up correctly. ({0})"
                                                   .format(mod_dir))
                        continue

                    if "version" in mod.SETTINGS.general:
                        version = mod.SETTINGS["general"]["version"]
                    else:
                        version = "- not supported -"

                    if "copyright" in mod.SETTINGS.general:
                        cpright = mod.SETTINGS["general"]["copyright"]
                    else:
                        cpright = "- not specified -"

                    mod_data[mod_dir] = (version, cpright)
                except Exception as exc:
                    core.MASTER_LOGGER.exception("{0}: {1}".format(type(exc).__name__, exc))
        # also collect core data
        core_data = (APP_SETTINGS["general"]["version"], APP_SETTINGS["general"]["copyright"])

        # Info text and license notice
        copyright_label = QLabel("""\
                    <h1>OpenWebScraper</h1>\
                    <p>This software is free of use, modification and redistribution \
                    under the terms of the GNU General Public License version 3 as \
                    published by the Free Software Foundation. \
                    Either see the COPYING file contained in this repository or \
                    <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a> \
                    for a full version of the GPLv3 license.</p><p>\
                    The copyright notice and version info for each of the contained modules \
                    is found in the table below. The core module is considered to comprise all \
                    source files outside of the <i>modules</i> directory.</p>\
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

    def __init__(self, main_window):
        self.modules = []
        self.main_window = main_window

    def load_modules(self, mods: {}):
        core.MASTER_LOGGER.info("Loading modules.")
        for modname in mods:
            try:
                mod = importlib.import_module(APP_SETTINGS["modloader"]["mod_dir"] + "." + modname,
                                              APP_SETTINGS["modloader"]["mod_dir"] + "." + modname)

                # Check for and load the mod settings:
                if not hasattr(mod, "SETTINGS"):
                    core.MASTER_LOGGER.error("Invalid module {0}. No settings specified.".format(modname))
                    continue

                mod_settings = mod.SETTINGS

                if "general" not in mod_settings:
                    core.MASTER_LOGGER.error("Settings for module {0} invalid. [general] block expected, not given."
                                             .format(modname))
                    continue

                if "main_widget" in mod_settings["general"]:
                    widget_path = mod_settings["general"]["main_widget"]
                    setattr(mod, "MAIN_WIDGET", core.get_class(widget_path))
                    # only load the module if MAIN_WIDGET is a QWidget:
                    if issubclass(mod.MAIN_WIDGET, QWidget):
                        self.modules.append(mod)
                    else:
                        core.MASTER_LOGGER.error("{0} does not reference a class inheriting from QWidget."
                                                 .format(widget_path))
                else:
                    raise AttributeError("Settings of module {0} are missing main_widget attribute".format(modname))

                if "title" not in mod_settings["general"]:
                    core.MASTER_LOGGER.warning("Title of module {0} not specified in settings. Using '{0}'."
                                               .format(modname))
                    setattr(mod, "TITLE", modname)
                else:
                    setattr(mod, "TITLE", mod_settings["general"]["title"])

                # Check for and invoke initialization hook:
                if hasattr(mod, "init"):
                    mod.init(self.main_window)

            except Exception as exc:
                core.MASTER_LOGGER.exception("{0}: {1}".format(type(exc).__name__, exc))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    MAIN_WINDOW = UIWindow()

    MAIN_WINDOW.show()

    sys.exit(app.exec_())
