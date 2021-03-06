"""
Created on 03.10.2019

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

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGroupBox
import core
from core.QtExtensions import HorizontalContainer, SimpleErrorInfo
from modules.crawler import filemanager
from modules.crawler.controller import CrawlerController


class HttpRemoteCrawlView(QHBoxLayout):

    def __init__(self):
        super().__init__()

        # setup queue
        queue_label = QLabel("Set the message queue location:")

        self.queue_input = QLineEdit()
        self.queue_input.setPlaceholderText("e.g. http://example.com/crawler_queue")

        queue_layout = QVBoxLayout()
        queue_layout.addWidget(queue_label)
        queue_layout.addWidget(self.queue_input)

        queue_input_group = QGroupBox("Message Queue Setup")
        queue_input_group.setLayout(queue_layout)

        # new crawl
        self.crawl_name_input = QLineEdit()
        self.crawl_name_input.setPlaceholderText("Crawl name")

        self.crawl_button = QPushButton("Send to specified URI")

        new_crawl_layout = QVBoxLayout()
        new_crawl_layout.addWidget(self.crawl_name_input)
        new_crawl_layout.addWidget(self.crawl_button)

        new_crawl_input_group = QGroupBox("New Crawl")
        new_crawl_input_group.setLayout(new_crawl_layout)

        # put together crawl starting options
        self.addWidget(queue_input_group)
        self.addWidget(new_crawl_input_group)

        self.cnt = HttpRemoteQueueController(self)


class HttpRemoteQueueController(core.ViewController):

    def __init__(self, view: HttpRemoteCrawlView):
        super().__init__(view)

        self.master_cnt = None
        self.resettables.extend([self._view.crawl_name_input])

        self.init_elements()

        self.setup_behaviour()

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """
        # TODO: perhaps initialize self._view.queue_input to some default message queue location
        #  e.g. self._view.queue_input.setText("DEFAULT_URI")
        pass

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        self._view.crawl_button.clicked.connect(self.send_to_queue)

        # trigger model updates
        if self.master_cnt:
            self._view.crawl_name_input.textChanged.connect(self.master_cnt.update_model)
        else:
            self._view.crawl_name_input.textChanged.connect(self.update_model)

    def update_model(self):
        if self.master_cnt:
            crawl_name = self._view.crawl_name_input.displayText()
            self.master_cnt.crawl_specification.update(name=crawl_name,
                                                       output=filemanager._get_crawl_raw_path(crawl_name),
                                                       logs=filemanager.get_crawl_log_path(crawl_name)
                                                       )

    def update_view(self):
        self._view.crawl_name_input.setText(self.master_cnt.crawl_specification.name)

    def send_to_queue(self):
        """
        Creates and sends an appropriate json crawl specification to the specified message queue.
        Perhaps it should send one specification per start url.
        :return:
        """
        # do some specific crawl specification setup
        self.master_cnt.crawl_specification.update(
            # these directories are rather arbitrary, because scrapy_wrapper is not being executed on THIS system
            # introduce a finalizer to supply resulting data from these output directories back to the user
            output="data",
            logs="logs",
            pipelines={"pipelines.Paragraph2CsvPipeline": 300},
            # extend finalizers by one that retrieves the crawl results and sends them away
            finalizers={}

        )

        queue_location = self._view.queue_input.displayText()

        json_text = self.master_cnt.crawl_specification.serialize()

        SimpleErrorInfo("Feature not yet implemented",
                        "Sending crawl specifications via http "
                        "has not yet been implemented, please be patient.").exec()

        # TODO: create http request with specification json (json_text)
        #  and send it to the specified message queue location (queue_location)
        #  either split specification into one per start url here or where the request is received
