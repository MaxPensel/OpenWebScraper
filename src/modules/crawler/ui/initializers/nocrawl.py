"""
Created on 28.11.2019

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
import os

from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QFileDialog, QPushButton

import core
from core.QtExtensions import SimpleYesNoMessage
from crawlUI import APP_SETTINGS
from modules.crawler import detect_valid_urls, compile_invalid_html

LOG = core.simple_logger(modname="crawler", file_path=APP_SETTINGS["general"]["master_log"])


class NoCrawlView(QVBoxLayout):

    def __init__(self):
        super().__init__()

        # TODO allow to select and configure the "normally" implicit values, such as logs, output, finalizers, etc.

        # save crawl specification
        self.save_button = QPushButton("Save")

        self.addWidget(self.save_button)

        self.cnt = NoCrawlController(self)


class NoCrawlController(core.ViewController):

    def __init__(self, view):
        super().__init__(view)

        self.dialog = QFileDialog(view.save_button)

        self.master_cnt = None

        self.init_elements()
        self.setup_behaviour()

    def register_master_cnt(self, master_controller: core.ViewController):
        self.master_cnt = master_controller

    def init_elements(self):
        self.dialog.setFileMode(QFileDialog.AnyFile)
        self.dialog.setAcceptMode(QFileDialog.AcceptSave)
        self.dialog.setDefaultSuffix("json")
        self.dialog.setDirectory(".")

    def setup_behaviour(self):
        self._view.save_button.clicked.connect(self.save_specification)

    def save_specification(self):
        self.master_cnt.update_model()

        lines, invalid, urls = detect_valid_urls(self.master_cnt.crawl_specification.urls)
        if invalid:
            invalid_html = compile_invalid_html(invalid)
            msg = SimpleYesNoMessage("Warning", "<b>{0} out of {1} non-empty lines contain invalid urls.</b>"
                                     .format(len(invalid), lines),
                                     details="{0}"
                                             "<b>Do you wish to save the crawl specification with the remaining "
                                             "{1} valid urls?</b>".format(invalid_html, lines - len(invalid)))

            if not msg.is_confirmed():
                return

        if self.dialog.exec_():
            file_name = self.dialog.selectedFiles()[0]
            crawlname = os.path.splitext(os.path.basename(file_name))[0]

            # save specification using only valid urls
            view_urls = self.master_cnt.crawl_specification.urls
            self.master_cnt.crawl_specification.update(urls=urls, name=crawlname)

            with open(file_name, "w") as file:
                file.write(self.master_cnt.crawl_specification.serialize())
                LOG.info("Saved specification to {0}".format(file_name))

            self.master_cnt.crawl_specification.update(urls=view_urls)
