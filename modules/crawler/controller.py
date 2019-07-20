"""
Created on 27.05.2019

@author: Maximilian Pensel
"""

import os
import sys
import json
import traceback
import subprocess

from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter, QErrorMessage, QMessageBox

from core.Workspace import WorkspaceManager
from crawlUI import ModLoader
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

    def setup_behaviour(self):
        """ Setup the behaviour of elements
        
        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        self.setup_completion()

        self._view.url_load.clicked.connect(self.load_url_file)
        self._view.url_save.clicked.connect(self.save_url_file)

        self._view.blacklist_load.clicked.connect(self.load_blacklist_file)
        self._view.blacklist_save.clicked.connect(self.save_blacklist_file)

        self._view.crawl_button.clicked.connect(self.start_crawl)
        # self._view.blacklist_load.clicked.connect(self.load_blacklist_file)  # load_url_file must be made more generic

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

    def reload(self):
        self.setup_completion()
        
    def load_url_file(self):
        filename = self._view.url_input.displayText()

        content = filemanager.get_url_content(filename)
        self._view.url_area.setPlainText(content)

    def save_url_file(self):
        filename = self._view.url_input.displayText()

        content = self._view.url_area.toPlainText()
        filemanager.save_url_content(content, filename)

        self.reload()

    def load_blacklist_file(self):
        filename = self._view.blacklist_input.displayText()

        content = filemanager.get_blacklist_content(filename)
        self._view.blacklist_area.setPlainText(content)

    def save_blacklist_file(self):
        filename = self._view.blacklist_input.displayText()

        content = self._view.blacklist_area.toPlainText()
        filemanager.save_blacklist_content(content, filename)

        self.reload()

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
        
        print("Starting new crawl with settings in file {0} ..".format(settings_path))
        try:
            if os.name == "nt":  # include the creation flag DETACHED_PROCESS for calls in windows
                subprocess.Popen("python scrapy_wrapper.py \"" + settings_path + "\"",
                                 stdout=sys.stdout,
                                 shell=True,
                                 start_new_session=True,
                                 cwd="modules/crawler/",
                                 creationflags=subprocess.DETACHED_PROCESS,
                                 close_fds=True)
            else:
                subprocess.Popen("python scrapy_wrapper.py \"" + settings_path + "\"",
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
