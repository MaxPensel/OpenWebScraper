"""
Created on 27.05.2019

@author: Maximilian Pensel
"""
from PyQt5.QtGui import QCursor
from PyQt5.Qt import Qt

import core
from core.QtExtensions import VerticalContainer
from modules.crawler.controller import CrawlerController
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QPushButton, QSplitter, \
    QComboBox, QGroupBox, QVBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt5.QtWidgets import QHBoxLayout
import qtawesome

from modules import crawler


class CrawlerWidget(VerticalContainer):
    
    def __init__(self):
        """ Initialises the components of this widget with their layout """
        super().__init__()

        self.crawl_specification_view = CrawlSpecificationView()

        self.crawl_init_view = None
        # self.crawl_init_view = core.get_class(crawler.INITIALIZER_WIDGETS[crawler.INITIALIZER_DEFAULT])()

        self.initializer_select = QComboBox()
        self.initializer_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        initializer_label = QLabel("Select initializer: ")

        initializer_filler = QWidget()
        initializer_filler.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        initializer_layout = QHBoxLayout()
        initializer_layout.addWidget(initializer_label)
        initializer_layout.addWidget(self.initializer_select)
        initializer_layout.addWidget(initializer_filler)

        # put everything together
        self.addWidget(self.crawl_specification_view)
        self.addLayout(initializer_layout)
        # self.addWidget(self.crawl_init_view)

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

        self.url_area = QPlainTextEdit()

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

        # setup blacklist side
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

        # put together
        self.setChildrenCollapsible(False)
        self.addWidget(url_input_group)
        self.addWidget(blacklist_input_group)
