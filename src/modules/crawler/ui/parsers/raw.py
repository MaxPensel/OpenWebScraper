"""
Created on 27.01.2020

@author: Maximilian Pensel

Copyright 2020 Maximilian Pensel <maximilian.pensel@gmx.de>

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

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QCheckBox, QGroupBox, QVBoxLayout, QPlainTextEdit

from core import ViewController
from modules.crawler.controller import CrawlerController
from modules.crawler.model import CrawlSpecification
from modules.crawler import SETTINGS

KEY_ALLOWED_CONTENT_TYPES = "allowed_content_type"


class RawParserSettingsView(QHBoxLayout):

    def __init__(self):
        super().__init__()

        # TODO construct view elements
        # content type selection
        self.content_type_area = QPlainTextEdit()
        content_type_group = QGroupBox("Allowed Content Types")
        content_type_group.setLayout(QVBoxLayout())
        content_type_group.layout().addWidget(self.content_type_area)

        self.addWidget(content_type_group)

        self.cnt = RawParserSettingsController(self)


class RawParserSettingsController(ViewController):

    def __init__(self, view):
        super().__init__(view)
        self.master_cnt = None
        self.resettables.extend([])

        self.init_elements()

        self.setup_behaviour()

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller
        self.update_model()

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """
        self._view.content_type_area.setPlainText("\n".join(SETTINGS["ui"]["parser"]["defaults"]["content_types"]))

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        # trigger model updates
        self._view.content_type_area.textChanged.connect(self.update_model)

    def update_model(self):
        spec = self.master_cnt.crawl_specification  # type: CrawlSpecification
        data = {
            KEY_ALLOWED_CONTENT_TYPES: self._view.content_type_area.toPlainText().split("\n")
        }
        spec.update(parser="parsers.RawParser",
                    parser_data=data,
                    pipelines={"pipelines.Raw2FilePipeline": 300})

    def update_view(self):
        spec = self.master_cnt.crawl_specification  # type: CrawlSpecification

        # TODO update view elements depending on current specification
