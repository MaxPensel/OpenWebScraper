"""
Created on 27.05.2019

@author: Maximilian Pensel
"""
from PyQt5.QtGui import QCursor
from PyQt5.Qt import Qt

from core.QtExtensions import VerticalContainer, FileOpenPushButton
from modules.crawler.controller import CrawlerController
from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit, QPushButton, QSplitter, \
    QFileDialog, QCompleter, QComboBox, QGroupBox, QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
import qtawesome


class CrawlerWidget(VerticalContainer):
    
    def __init__(self):
        """ Initialises the components of this widget with their layout """
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
        self.url_delete.setDisabled(True)
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
        self.blacklist_delete.setDisabled(True)
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
        url_blacklist_splitter = QSplitter()
        url_blacklist_splitter.setChildrenCollapsible(False)
        url_blacklist_splitter.addWidget(url_input_group)
        url_blacklist_splitter.addWidget(blacklist_input_group)

        # ### Different options for initiating a crawl

        # reload previous crawl
        self.prev_crawl_combobox = QComboBox()
        self.prev_crawl_load = QPushButton("Load Crawl Settings")

        prev_crawl_layout = QVBoxLayout()
        prev_crawl_layout.addWidget(self.prev_crawl_combobox)
        prev_crawl_layout.addWidget(self.prev_crawl_load)

        prev_crawl_groupbox = QGroupBox("Load Previous Crawl")
        prev_crawl_groupbox.setLayout(prev_crawl_layout)
        prev_crawl_groupbox.setDisabled(True)

        # continue unfinished crawl
        self.continue_crawl_combobox = QComboBox()
        self.continue_crawl_button = QPushButton("Continue Crawl")

        continue_crawl_layout = QVBoxLayout()
        continue_crawl_layout.addWidget(self.continue_crawl_combobox)
        continue_crawl_layout.addWidget(self.continue_crawl_button)

        continue_crawl_groupbox = QGroupBox("Continue Unfinished Crawl")
        continue_crawl_groupbox.setLayout(continue_crawl_layout)

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
        crawl_starting_options_layout = QHBoxLayout()
        crawl_starting_options_layout.addWidget(prev_crawl_groupbox)
        crawl_starting_options_layout.addWidget(continue_crawl_groupbox)
        crawl_starting_options_layout.addWidget(new_crawl_input_group)

        # put everything together
        self.addWidget(url_blacklist_splitter)
        self.addLayout(crawl_starting_options_layout)
        
        self.cnt = CrawlerController(self)
