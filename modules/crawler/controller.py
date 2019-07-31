"""
Created on 27.05.2019

@author: Maximilian Pensel
"""

import os
import sys
import json
import traceback
import subprocess

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter, QErrorMessage, QMessageBox, QComboBox

from core.Workspace import WorkspaceManager
from crawlUI import ModLoader, Settings
from modules.crawler import filemanager


class CrawlerController:
    
    MOD_PATH = os.path.join(ModLoader.MOD_DIR, "crawler")
    RUNNING_DIR = "running"
    RUNNING_PATH = os.path.join(MOD_PATH, RUNNING_DIR)

    def __init__(self, view):
        self._view = view
        
        self.init_elements()
        
        self.setup_behaviour()
    
    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """
        
        # self._view.blacklist_save.setEnabled(False)
        # self._view.url_save.setEnabled(False)
        self._view.url_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        CrawlerController.saturate_combobox(self._view.url_select, filemanager.get_url_filenames())

        self._view.blacklist_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        CrawlerController.saturate_combobox(self._view.blacklist_select, filemanager.get_blacklist_filenames())

    def setup_behaviour(self):
        """ Setup the behaviour of elements
        
        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        self._view.url_select.currentIndexChanged.connect(
            self.load_file_to_editor(self._view.url_select,
                                     filemanager.get_url_content,
                                     self._view.url_area,
                                     self._view.url_input))
        self._view.url_save.clicked.connect(
            self.build_save_file_connector(self._view.url_input,
                                           self._view.url_select,
                                           self._view.url_area,
                                           filemanager.save_url_content,
                                           filemanager.get_url_filenames))

        self._view.blacklist_select.currentIndexChanged.connect(
            self.load_file_to_editor(self._view.blacklist_select,
                                     filemanager.get_blacklist_content,
                                     self._view.blacklist_area,
                                     self._view.blacklist_input))
        self._view.blacklist_save.clicked.connect(
            self.build_save_file_connector(self._view.blacklist_input,
                                           self._view.blacklist_select,
                                           self._view.blacklist_area,
                                           filemanager.save_blacklist_content,
                                           filemanager.get_blacklist_filenames))

        self._view.crawl_button.clicked.connect(self.start_crawl)

    def setup_completion(self):
        url_model = QStringListModel()
        url_model.setStringList(filemanager.get_url_filenames())
        url_completer = QCompleter()
        url_completer.setModel(url_model)
        url_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._view.url_input.setCompleter(url_completer)

        blacklist_model = QStringListModel()
        blacklist_model.setStringList(filemanager.get_blacklist_filenames())
        blacklist_completer = QCompleter()
        blacklist_completer.setModel(blacklist_model)
        blacklist_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._view.blacklist_input.setCompleter(blacklist_completer)

    @staticmethod
    def saturate_combobox(combobox: QComboBox, items, include_empty=True):
        for i in range(combobox.count()):
            combobox.removeItem(0)
        if include_empty:
            combobox.addItem("")
        combobox.addItems(items)
        
    @staticmethod
    def load_file_to_editor(combobox, content_loader, text_area, input_field):
        def combobox_connector(index):
            if index:
                filename = combobox.itemText(index)

                content = content_loader(filename)
                text_area.setPlainText(content)
                input_field.setText(filename)
        return combobox_connector

    @staticmethod
    def build_save_file_connector(input_field, combobox, text_area, content_saver, content_loader):
        def save_button_connector():
            filename = input_field.displayText()

            if not filename:
                print("Kill the save, nothing is set.")
                return

            print("Filename given, save to that!")
            idx = combobox.findText(filename, flags=Qt.MatchExactly)
            if idx >= 0 and idx is not combobox.currentIndex():
                print("Attention you would be overwriting another existing urls file. Continue?")
            content = text_area.toPlainText()
            content_saver(content, filename)
            CrawlerController.saturate_combobox(combobox, content_loader())
            combobox.setCurrentIndex(combobox.findText(filename, flags=Qt.MatchExactly))
        return save_button_connector

    def start_crawl(self):
        crawl_name = self._view.crawl_name_input.displayText()
        if crawl_name in filemanager.get_running_crawls():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText("There is still an unfinished crawl by the name '{0}'. Pick a different name!"
                                   .format(crawl_name))
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        settings_path = self.setup_crawl()
        if not settings_path:
            print("Crawl setup encountered an error. Not starting crawl.", file=sys.stderr)
            return
        
        print("Starting new crawl with settings in file {0}".format(settings_path))
        python_exe = os.path.abspath(Settings().python)
        print("Running scrapy_wrapper.py with {0}".format(python_exe))
        try:
            if os.name == "nt":  # include the creation flag DETACHED_PROCESS for calls in windows
                p = subprocess.Popen(python_exe + " scrapy_wrapper.py \"" + settings_path + "\"",
                                     stdout=sys.stdout,
                                     shell=True,
                                     start_new_session=True,
                                     cwd="modules/crawler/",
                                     creationflags=subprocess.DETACHED_PROCESS,
                                     close_fds=True)
            else:
                subprocess.Popen(python_exe + " scrapy_wrapper.py \"" + settings_path + "\"",
                                 stdout=sys.stdout,
                                 shell=True,
                                 start_new_session=True,
                                 cwd="modules/crawler/",
                                 close_fds=True)
        except Exception as exc:
            print(traceback.format_exc())
            print(exc)
    
    def setup_crawl(self):
        crawl_name = self._view.crawl_name_input.displayText()
        if crawl_name in filemanager.get_crawlnames():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText("Continue?")
            msg.setInformativeText("There is already data for a crawl by the name '{0}'. Continue anyway?"
                                   .format(crawl_name))
            msg.setWindowTitle("Continue?")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            answer = msg.exec_()
            if answer == QMessageBox.Cancel:
                return None

        settings = {"workspace": WorkspaceManager().get_workspace(),
                    "name": self._view.crawl_name_input.displayText(),
                    "urls_file": self._view.url_input.displayText(),
                    "blacklist_file": self._view.blacklist_input.displayText(),
                    "finished_urls": []
                    }

        return filemanager.save_crawl_settings(self._view.crawl_name_input.displayText(), settings)
