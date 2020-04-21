"""
Created on 02.10.2019

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
import json
import os
import subprocess
import sys
import threading

from PyQt5.QtWidgets import QComboBox, QPushButton, QVBoxLayout, QGroupBox, QLineEdit, QHBoxLayout, QMessageBox

import core
from core.QtExtensions import saturate_combobox, SimpleErrorInfo, SimpleYesNoMessage, SimpleMessageBox
from modules.crawler import filemanager, WindowsCreationFlags, detect_valid_urls, SETTINGS
from modules.crawler.controller import CrawlerController
from modules.crawler.model import CrawlSpecification

from crawlUI import APP_SETTINGS

LOG = core.simple_logger(modname="crawler", file_path=APP_SETTINGS["general"]["master_log"])


class LocalCrawlView(QHBoxLayout):

    def __init__(self):
        super().__init__()
        # ### Different options for initiating a crawl

        # reload previous crawl
        self.prev_crawl_combobox = QComboBox()
        self.prev_crawl_load = QPushButton("Load Crawl Settings")

        prev_crawl_layout = QVBoxLayout()
        prev_crawl_layout.addWidget(self.prev_crawl_combobox)
        prev_crawl_layout.addWidget(self.prev_crawl_load)

        self.prev_crawl_groupbox = QGroupBox("Load Previous Crawl")
        self.prev_crawl_groupbox.setLayout(prev_crawl_layout)

        # new crawl
        self.crawl_name_input = QLineEdit()
        self.crawl_name_input.setPlaceholderText("Crawl name")

        self.crawl_button = QPushButton("Start New Crawl")

        new_crawl_layout = QVBoxLayout()
        new_crawl_layout.addWidget(self.crawl_name_input)
        new_crawl_layout.addWidget(self.crawl_button)

        new_crawl_input_group = QGroupBox("New Crawl")
        new_crawl_input_group.setLayout(new_crawl_layout)

        # put together crawl starting options
        self.addWidget(self.prev_crawl_groupbox)
        self.addWidget(new_crawl_input_group)

        self.cnt = LocalCrawlController(self)


class LocalCrawlController(core.ViewController):

    def __init__(self, view: LocalCrawlView):
        super().__init__(view)
        self.master_cnt = None
        self.resettables.extend([view.prev_crawl_combobox,
                                view.crawl_name_input])

        self.init_elements()

        # self.setup_behaviour()  # behavior must be setup after master controller is registered

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller
        # re-setup behaviour
        self.setup_behaviour()

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """

        self._view.prev_crawl_groupbox.setDisabled(True)

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """
        self._view.crawl_button.clicked.connect(self.start_crawl)

        # trigger model updates
        if self.master_cnt:
            self._view.crawl_name_input.textChanged.connect(self.master_cnt.update_model)
        else:
            self._view.crawl_name_input.textChanged.connect(self.update_model)

        # test connection to scrapy wrapper and produce feedback
        def set_info(info):
            if "version" in info:
                self.master_cnt.set_initializer_info(f"Connected to OWS-scrapy-wrapper version {info['version']}")
            else:
                self.master_cnt.set_initializer_info(info['message'], color="red")
        thread = threading.Thread(target=check_scrapy_connection, args=[set_info])
        thread.start()

    def update_model(self):
        if self.master_cnt:
            crawl_name = self._view.crawl_name_input.displayText()
            self.master_cnt.crawl_specification.update(name=crawl_name,
                                                       output=filemanager._get_crawl_raw_path(crawl_name),
                                                       logs=filemanager.get_crawl_log_path(crawl_name)
                                                       )

    def update_view(self):
        if self.master_cnt:
            self._view.crawl_name_input.setText(self.master_cnt.crawl_specification.name)

    def continue_crawl(self):
        spec = self.master_cnt.crawl_specification  # type: CrawlSpecification

        if self._view.continue_crawl_combobox.currentIndex() == 0:
            msg = SimpleErrorInfo("Error", "No crawl selected for continuation.")
            msg.exec()
            LOG.error("No crawl selected for continuation.")
            return
        msg = SimpleMessageBox("Attention",
                               "Are you sure that the crawl '{0}' is not running anymore?"
                               .format(spec.name),
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

            LOG.info("Determining incomplete urls in crawl {0}".format(spec.name))
            incomplete = filemanager.get_incomplete_urls(spec.name, spec.urls)
            LOG.info("Found {0} out of {1} incomplete urls: {2}".format(len(incomplete), len(spec.urls), incomplete))
            spec.update(urls=incomplete)

            filemanager.save_crawl_settings(spec.name, spec)

            settings_path = filemanager.get_running_specification_path(spec.name)

            LOG.info("Starting new crawl with settings in file {0}".format(settings_path))
            start_scrapy(settings_path)
            self._view.continue_crawl_combobox.removeItem(self._view.continue_crawl_combobox.currentIndex())
            self.update_view()

    def start_crawl(self):
        LOG.info("Pre-flight checks for starting a new crawl ...")
        self.master_cnt.update_model()
        if not self.master_cnt.crawl_specification.name:
            msg = SimpleErrorInfo("Error", "Your crawl must have a name.")
            msg.exec()
            return

        # TODO Determine if a crawl has incomplete datafiles
        if False:
            msg = SimpleMessageBox("Warning",
                                   "There is still an unfinished crawl by the name '{0}'."
                                   .format(self.master_cnt.crawl_specification.name),
                                   details="It is recommended to use a different name. If you are sure that this "
                                           "crawl is not running anymore you can also fully restart it with its "
                                           "original settings or use the continue crawl feature.",
                                   icon=QMessageBox.Warning)
            restart = msg.addButton("Restart Crawl", QMessageBox.ActionRole)
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec()
            pressed = msg.clickedButton()
            if pressed == restart:
                settings_path = self.setup_crawl(continue_crawl=True)
            else:
                return
        else:
            lines, invalid, urls = detect_valid_urls(self.master_cnt.crawl_specification.urls)
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
            self.master_cnt.crawl_specification.update(urls=urls)

            settings_path = self.setup_crawl()

        if not settings_path:
            msg = SimpleErrorInfo("Error", "Crawl setup encountered an error. Not starting crawl.")
            msg.exec()
            return
        if settings_path is not None:
            LOG.info("Starting new crawl with settings in file {0}".format(settings_path))
            start_scrapy(settings_path)
        else:
            LOG.error("Something went wrong it crawl specification setup. Not starting scrapy!")

    def setup_crawl(self, continue_crawl=False):
        spec = self.master_cnt.crawl_specification

        if continue_crawl:
            # check if running specification exists, if so, return its path
            return filemanager.get_crawl_specification(spec.name)
        else:
            # setup empty finalizers list; local crawl does not rely on finalizers yet
            spec.update(finalizers={})
            if spec.name in filemanager.get_crawlnames():
                msg = SimpleYesNoMessage("Continue?",
                                         "There is already data for a crawl by the name '{0}'. Continue anyway?"
                                         .format(spec.name))
                if not msg.is_confirmed():
                    return None

            return filemanager.save_crawl_settings(spec.name, spec)


def start_scrapy(settings_path):
    scrapy_script = SETTINGS["general"]["scrapy_wrapper_exec"]
    command = scrapy_script + " \"" + settings_path + "\""
    LOG.info("Running {0}".format(command))
    try:
        if os.name == "nt":  # include the creation flag DETACHED_PROCESS for calls in windows
            subprocess.Popen(command,
                             stdout=sys.stdout,
                             shell=True,
                             start_new_session=True,
                             cwd=".",
                             creationflags=WindowsCreationFlags.DETACHED_PROCESS)
        else:
            subprocess.Popen(command,
                             stdout=sys.stdout,
                             shell=True,
                             start_new_session=True,
                             cwd=".",
                             close_fds=True)
    except Exception as exc:
        LOG.exception("{0}: {1}".format(type(exc).__name__, exc))


def check_scrapy_connection(callback):
    scrapy_script = SETTINGS["general"]["scrapy_wrapper_exec"]
    command = scrapy_script + " INFO"
    LOG.info("Running {0}".format(command))
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=False)

        info_json, _ = proc.communicate()

        info = json.loads(info_json.splitlines()[-1])
        LOG.info("Connected to OWS-scrapy-wrapper version {0}".format(info["version"]))
    except Exception as exc:
        LOG.exception("{0}: {1}".format(type(exc).__name__, exc))
        info = dict(message="Could not connect to OWS-scrapy-wrapper. Check your config.")

    callback(info)
