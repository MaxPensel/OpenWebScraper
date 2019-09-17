"""
Created on 27.05.2019

@author: Maximilian Pensel
"""

import os
import sys
import json
import traceback
import subprocess

import validators
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter, QErrorMessage, QMessageBox, QComboBox

import core
from core.QtExtensions import SimpleYesNoMessage, SimpleErrorInfo, SimpleMessageBox
from core.Workspace import WorkspaceManager
from crawlUI import ModLoader, Settings
from modules.crawler import filemanager
from modules.crawler.model import CrawlSpecification, CrawlMode

LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)


class WindowsCreationFlags:
    DETACHED_PROCESS = 0x00000008


class CrawlerController:

    MOD_PATH = os.path.join(ModLoader.MOD_DIR, "crawler")
    RUNNING_DIR = "running"
    RUNNING_PATH = os.path.join(MOD_PATH, RUNNING_DIR)

    def __init__(self, view):
        self._view = view
        self.crawl_specification = CrawlSpecification()

        self.init_elements()

        self.setup_behaviour()

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """

        # self._view.blacklist_save.setEnabled(False)
        # self._view.url_save.setEnabled(False)
        self._view.crawl_specification_view.url_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        CrawlerController.saturate_combobox(self._view.crawl_specification_view.url_select,
                                            filemanager.get_url_filenames())

        self._view.crawl_specification_view.blacklist_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        CrawlerController.saturate_combobox(self._view.crawl_specification_view.blacklist_select,
                                            filemanager.get_blacklist_filenames())

        self._view.crawl_specification_view.url_delete.setDisabled(True)
        self._view.crawl_specification_view.blacklist_delete.setDisabled(True)

        self._view.continue_crawl_combobox.setInsertPolicy(QComboBox.InsertAlphabetically)
        CrawlerController.saturate_combobox(self._view.continue_crawl_combobox, filemanager.get_running_crawls())

        self._view.prev_crawl_groupbox.setDisabled(True)

    def setup_behaviour(self):
        """ Setup the behaviour of elements
        
        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        self._view.crawl_specification_view.url_select.currentIndexChanged.connect(
            self.load_file_to_editor(self._view.crawl_specification_view.url_select,
                                     filemanager.get_url_content,
                                     self._view.crawl_specification_view.url_area,
                                     self._view.crawl_specification_view.url_input))
        self._view.crawl_specification_view.url_save.clicked.connect(
            self.build_save_file_connector(self._view.crawl_specification_view.url_input,
                                           self._view.crawl_specification_view.url_select,
                                           self._view.crawl_specification_view.url_area,
                                           filemanager.save_url_content,
                                           filemanager.get_url_filenames))

        self._view.crawl_specification_view.blacklist_select.currentIndexChanged.connect(
            self.load_file_to_editor(self._view.crawl_specification_view.blacklist_select,
                                     filemanager.get_blacklist_content,
                                     self._view.crawl_specification_view.blacklist_area,
                                     self._view.crawl_specification_view.blacklist_input))
        self._view.crawl_specification_view.blacklist_save.clicked.connect(
            self.build_save_file_connector(self._view.crawl_specification_view.blacklist_input,
                                           self._view.crawl_specification_view.blacklist_select,
                                           self._view.crawl_specification_view.blacklist_area,
                                           filemanager.save_blacklist_content,
                                           filemanager.get_blacklist_filenames))

        self._view.continue_crawl_button.clicked.connect(self.continue_crawl)
        self._view.crawl_button.clicked.connect(self.start_crawl)

        # trigger model updates
        self._view.crawl_specification_view.url_area.textChanged.connect(self.update_model)
        self._view.crawl_specification_view.blacklist_area.textChanged.connect(self.update_model)
        self._view.crawl_name_input.textChanged.connect(self.update_model)

        self._view.continue_crawl_combobox.currentIndexChanged.connect(self.select_unfinished_crawl)

    def setup_completion(self):
        url_model = QStringListModel()
        url_model.setStringList(filemanager.get_url_filenames())
        url_completer = QCompleter()
        url_completer.setModel(url_model)
        url_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._view.crawl_specification_view.url_input.setCompleter(url_completer)

        blacklist_model = QStringListModel()
        blacklist_model.setStringList(filemanager.get_blacklist_filenames())
        blacklist_completer = QCompleter()
        blacklist_completer.setModel(blacklist_model)
        blacklist_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._view.crawl_specification_view.blacklist_input.setCompleter(blacklist_completer)

    @staticmethod
    def reset_combobox(combobox: QComboBox):
        combobox.setCurrentIndex(0)

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
            if index > 0:  # index 0 should always be empty option, do not load content for that (or index < 0)
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
                msg = SimpleErrorInfo("Error", "You have to specify a name to be associated with your data.")
                msg.exec()
                return

            idx = combobox.findText(filename, flags=Qt.MatchExactly)
            if idx >= 0 and idx is not combobox.currentIndex():
                msg = SimpleYesNoMessage("Continue?",
                                         "There is already data associated with '{0}'. Continue and overwrite?"
                                         .format(filename))
                if not msg.is_confirmed():
                    return None

            LOG.info("Saving data as {0}".format(filename))
            content = text_area.toPlainText()
            content_saver(content, filename)
            CrawlerController.saturate_combobox(combobox, content_loader())
            combobox.setCurrentIndex(combobox.findText(filename, flags=Qt.MatchExactly))
        return save_button_connector

    def update_view(self, skip=[]):
        self._view.crawl_name_input.setText(self.crawl_specification.name)
        self._view.crawl_specification_view.url_area.setPlainText("\n".join(self.crawl_specification.urls))
        self._view.crawl_specification_view.blacklist_area.setPlainText("\n".join(self.crawl_specification.blacklist))

        if self._view.crawl_specification_view.url_select not in skip:
            CrawlerController.reset_combobox(self._view.crawl_specification_view.url_select)
        if self._view.crawl_specification_view.blacklist_select not in skip:
            CrawlerController.reset_combobox(self._view.crawl_specification_view.blacklist_select)
        if self._view.continue_crawl_combobox not in skip:
            CrawlerController.reset_combobox(self._view.continue_crawl_combobox)

    def update_model(self):
        # eventually we could enforce urls and blacklist to be sets instead of lists here
        self.crawl_specification\
            .update(name=self._view.crawl_name_input.displayText(),
                    workspace=WorkspaceManager().get_workspace(),
                    urls=self._view.crawl_specification_view.url_area.toPlainText().splitlines(),
                    blacklist=self._view.crawl_specification_view.blacklist_area.toPlainText().splitlines(),
                    xpaths=["//p", "//td"])
        LOG.debug("Crawl specification model updated.")  # this message is triggered very often

    def select_unfinished_crawl(self):
        # load crawl
        settings_filename = self._view.continue_crawl_combobox.currentText()
        if settings_filename:
            self.crawl_specification = filemanager.load_running_crawl_settings(settings_filename)
            self.update_view(skip=[self._view.continue_crawl_combobox])

    def continue_crawl(self):
        if self._view.continue_crawl_combobox.currentIndex() == 0:
            LOG.error("No crawl to be continued is selected.")
            return
        msg = SimpleMessageBox("Attention",
                               "Are you sure that the crawl '{0}' is not running anymore?"
                               .format(self.crawl_specification.name),
                               details="Check your task manager (or Alt+Tab) for any console-type windows, perhaps "
                                       "your crawl is still being executed. If you are sure that the process has "
                                       "stopped, you can continue it now.",
                               icon=QMessageBox.Warning)
        cont = msg.addButton("Continue Crawl", QMessageBox.ActionRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()
        pressed = msg.clickedButton()
        if pressed == cont:
            LOG.info("Setting up to continue an unfinished crawl ...")
            self.crawl_specification.mode = CrawlMode.CONTINUE
            filemanager.save_crawl_settings(self.crawl_specification.name, self.crawl_specification)

            settings_path = filemanager.get_running_specification_path(self.crawl_specification.name)

            LOG.info("Starting new crawl with settings in file {0}".format(settings_path))
            start_scrapy(settings_path)
            self._view.continue_crawl_combobox.removeItem(self._view.continue_crawl_combobox.currentIndex())
            self.update_view()

    def start_crawl(self):
        LOG.info("Pre-flight checks for starting a new crawl ...")
        if not self.crawl_specification.name:
            msg = SimpleErrorInfo("Error", "Your crawl must have a name.")
            msg.exec()
            return

        if self.crawl_specification.name in filemanager.get_running_crawls():
            msg = SimpleMessageBox("Warning",
                                   "There is still an unfinished crawl by the name '{0}'."
                                   .format(self.crawl_specification.name),
                                   details="It is recommended to use a different name. If you are sure that this "
                                           "crawl is not running anymore you can also fully restart it with its "
                                           "original settings or use the continue crawl feature.",
                                   icon=QMessageBox.Warning)
            restart = msg.addButton("Restart Crawl", QMessageBox.ActionRole)
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec()
            pressed = msg.clickedButton()
            if pressed == restart:
                settings_path = self.setup_crawl(restart_crawl=True)
            else:
                return
        else:
            lines, invalid, urls = self.detect_valid_urls()
            if invalid:
                invalid_html = "The following is a list of lines that have not been recognized as a valid url " \
                               "by the url validator. This could be because they syntactically do not form a valid " \
                               "url-string or they are not responding to an http-request or the http-request is " \
                               "being redirected to another url (other reasons might be possible).<br />" \
                               "Consider opening the following urls in your browser to verify the problems yourself." \
                               "<ul>"
                for inv in invalid:
                    invalid_html += "<li><a href='{0}'>{0}</a></li>".format(inv)
                invalid_html += "</ul>"
                if lines == len(invalid) or len(urls) == 0:
                    msg = SimpleErrorInfo("Error", "<b>No valid urls given.</b>", details=invalid_html)
                    msg.exec()
                    return

                msg = SimpleYesNoMessage("Warning", "<b>{0} out of {1} non-empty lines contain invalid urls.</b>"
                                                    .format(len(invalid), lines),
                                                    "{0}"
                                                    "<b>Do you wish to start the crawl with the remaining "
                                                    "{1} valid urls?</b>"
                                                    .format(invalid_html, lines-len(invalid)))

                if not msg.is_confirmed():
                    return
                # else: update specification to use only valid urls and start the crawl
                self.crawl_specification.update(urls=urls)

            settings_path = self.setup_crawl()

        if not settings_path:
            msg = SimpleErrorInfo("Error", "Crawl setup encountered an error. Not starting crawl.")
            msg.exec()
            return
        if settings_path != "Cancelled":
            LOG.info("Starting new crawl with settings in file {0}".format(settings_path))
            start_scrapy(settings_path)

    def setup_crawl(self, restart_crawl=False):
        if not restart_crawl:
            if self.crawl_specification.name in filemanager.get_crawlnames():
                msg = SimpleYesNoMessage("Continue?",
                                         "There is already data for a crawl by the name '{0}'. Continue anyway?"
                                         .format(self.crawl_specification.name))
                if not msg.is_confirmed():
                    return "Cancelled"

            return filemanager.save_crawl_settings(self.crawl_specification.name, self.crawl_specification)
        else:
            return filemanager.get_running_specification_path(self.crawl_specification.name)

    def detect_valid_urls(self):
        lines = 0
        invalid = list()
        urls = list()
        for line in self.crawl_specification.urls:
            if line:
                lines += 1
                validator_result = validators.url(line)
                if not validator_result:
                    invalid.append(line)
                else:
                    urls.append(line)
        return lines, invalid, urls


def start_scrapy(settings_path):
    python_exe = os.path.abspath(Settings().python)
    LOG.info("Running scrapy_wrapper.py with {0}".format(python_exe))
    try:
        if os.name == "nt":  # include the creation flag DETACHED_PROCESS for calls in windows
            subprocess.Popen(python_exe + " scrapy_wrapper.py \"" + settings_path + "\"",
                             stdout=sys.stdout,
                             shell=True,
                             start_new_session=True,
                             cwd="modules/crawler/",
                             creationflags=WindowsCreationFlags.DETACHED_PROCESS)
        else:
            subprocess.Popen(python_exe + " scrapy_wrapper.py \"" + settings_path + "\"",
                             stdout=sys.stdout,
                             shell=True,
                             start_new_session=True,
                             cwd="modules/crawler/",
                             close_fds=True)
    except Exception as exc:
        LOG.exception("{0}: {1}".format(type(exc).__name__, exc))