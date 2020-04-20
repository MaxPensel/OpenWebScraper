"""
Created on 27.05.2019

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
from PyQt5.QtGui import QCursor
from PyQt5.Qt import Qt

import core
from core.QtExtensions import VerticalContainer, HorizontalSeparator, LineHighlighter
from modules.crawler.controller import CrawlerController
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QPushButton, QSplitter, \
    QComboBox, QGroupBox, QVBoxLayout, QLabel, QWidget, QSizePolicy, QFrame, QSpacerItem, QTextEdit
from PyQt5.QtWidgets import QHBoxLayout
import qtawesome

from modules import crawler


class CrawlerWidget(QSplitter):
    
    def __init__(self):
        """ Initialises the components of this widget with their layout """
        super().__init__()

        # general crawl settings part
        self.crawl_specification_view = CrawlSpecificationView()


        # parser settings part
        self.crawl_parser_view = None
        parser_label = QLabel("Select parser: ")

        self.parser_select = QComboBox()
        self.parser_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        parser_settings_select_layout = QHBoxLayout()
        parser_settings_select_layout.addWidget(parser_label)
        parser_settings_select_layout.addWidget(self.parser_select)
        parser_settings_select_layout.addSpacerItem(QSpacerItem(100, 1, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.parser_settings_container = VerticalContainer()
        self.parser_settings_container.addLayout(parser_settings_select_layout)

        # initializer part
        self.crawl_init_view = None

        initializer_label = QLabel("Select initializer: ")

        self.initializer_select = QComboBox()
        self.initializer_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.initializer_info = QLabel()

        initializer_select_layout = QHBoxLayout()
        initializer_select_layout.addWidget(initializer_label)
        initializer_select_layout.addWidget(self.initializer_select)
        initializer_select_layout.addSpacerItem(QSpacerItem(100, 1, QSizePolicy.Expanding, QSizePolicy.Fixed))
        initializer_select_layout.addWidget(self.initializer_info)
        initializer_select_layout.addSpacerItem(QSpacerItem(100, 1, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.initializer_container = VerticalContainer()
        self.initializer_container.addLayout(initializer_select_layout)

        # put everything together
        self.setChildrenCollapsible(False)
        self.setOrientation(Qt.Vertical)

        self.addWidget(self.crawl_specification_view)
        self.addWidget(self.parser_settings_container)
        self.addWidget(self.initializer_container)
        self.setSizes([450, 250, 100])

        self.cnt = CrawlerController(self)


class CrawlSpecificationView(QSplitter):

    def __init__(self):
        super().__init__()
        # ### Setting up a crawl
        
        # setup url side
        self.url_select = QComboBox()
        self.url_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.url_input = QLineEdit()
        self.url_input.setMinimumWidth(150)

        self.url_save = QPushButton(icon=qtawesome.icon("fa5s.save", scale_factor=1.2))
        self.url_save.setProperty("class", "iconbutton")
        self.url_save.setCursor(QCursor(Qt.PointingHandCursor))

        self.url_delete = QPushButton(icon=qtawesome.icon("fa5s.trash-alt", scale_factor=1.2))
        self.url_delete.setProperty("class", "iconbutton")
        self.url_delete.setCursor(QCursor(Qt.PointingHandCursor))

        self.url_area = QTextEdit()
        self.url_highlighter = LineHighlighter(self.url_area.document())

        url_selection_layout = QHBoxLayout()
        url_selection_layout.addWidget(self.url_select)
        url_selection_layout.addWidget(self.url_input)
        url_selection_layout.addWidget(self.url_save)
        url_selection_layout.addWidget(self.url_delete)

        url_container_layout = QVBoxLayout()
        url_container_layout.addLayout(url_selection_layout)
        url_container_layout.addWidget(self.url_area)

        url_input_group = QGroupBox("Urls")
        url_input_group.setLayout(url_container_layout)

        # setup blacklist area
        self.blacklist_select = QComboBox()
        self.blacklist_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.blacklist_input = QLineEdit()
        self.blacklist_input.setMinimumWidth(150)

        self.blacklist_save = QPushButton(icon=qtawesome.icon("fa5s.save", scale_factor=1.2))
        self.blacklist_save.setProperty("class", "iconbutton")
        self.blacklist_save.setCursor(QCursor(Qt.PointingHandCursor))

        self.blacklist_delete = QPushButton(icon=qtawesome.icon("fa5s.trash-alt", scale_factor=1.2))
        self.blacklist_delete.setProperty("class", "iconbutton")
        self.blacklist_delete.setCursor(QCursor(Qt.PointingHandCursor))

        self.blacklist_area = QPlainTextEdit()

        blacklist_selection_layout = QHBoxLayout()
        blacklist_selection_layout.addWidget(self.blacklist_select)
        blacklist_selection_layout.addWidget(self.blacklist_input)
        blacklist_selection_layout.addWidget(self.blacklist_save)
        blacklist_selection_layout.addWidget(self.blacklist_delete)

        blacklist_container_layout = QVBoxLayout()
        blacklist_container_layout.addLayout(blacklist_selection_layout)
        blacklist_container_layout.addWidget(self.blacklist_area)

        blacklist_input_group = QGroupBox("Blacklist")
        blacklist_input_group.setLayout(blacklist_container_layout)

        # setup whitelist area
        self.whitelist_select = QComboBox()
        self.whitelist_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.whitelist_input = QLineEdit()
        self.whitelist_input.setMinimumWidth(150)

        self.whitelist_save = QPushButton(icon=qtawesome.icon("fa5s.save", scale_factor=1.2))
        self.whitelist_save.setProperty("class", "iconbutton")
        self.whitelist_save.setCursor(QCursor(Qt.PointingHandCursor))

        self.whitelist_delete = QPushButton(icon=qtawesome.icon("fa5s.trash-alt", scale_factor=1.2))
        self.whitelist_delete.setProperty("class", "iconbutton")
        self.whitelist_delete.setCursor(QCursor(Qt.PointingHandCursor))

        self.whitelist_area = QPlainTextEdit()

        whitelist_selection_layout = QHBoxLayout()
        whitelist_selection_layout.addWidget(self.whitelist_select)
        whitelist_selection_layout.addWidget(self.whitelist_input)
        whitelist_selection_layout.addWidget(self.whitelist_save)
        whitelist_selection_layout.addWidget(self.whitelist_delete)

        whitelist_container_layout = QVBoxLayout()
        whitelist_container_layout.addLayout(whitelist_selection_layout)
        whitelist_container_layout.addWidget(self.whitelist_area)

        whitelist_input_group = QGroupBox("Whitelist")
        whitelist_input_group.setLayout(whitelist_container_layout)

        # put together blacklist and whitelist
        blacklist_whitelist_surround = QSplitter()
        blacklist_whitelist_surround.setOrientation(Qt.Vertical)
        blacklist_whitelist_surround.addWidget(blacklist_input_group)
        blacklist_whitelist_surround.addWidget(whitelist_input_group)

        # put together
        self.setChildrenCollapsible(False)
        self.addWidget(url_input_group)
        self.addWidget(blacklist_whitelist_surround)
