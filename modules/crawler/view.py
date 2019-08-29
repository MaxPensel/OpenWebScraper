"""
Created on 27.05.2019

@author: Maximilian Pensel
"""
from core.QtExtensions import VerticalContainer, FileOpenPushButton
from modules.crawler.controller import CrawlerController
from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit, QPushButton, QSplitter, \
    QFileDialog, QCompleter, QComboBox, QGroupBox, QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout


class CrawlerWidget(VerticalContainer):
    
    def __init__(self):
        """ Initialises the components of this widget with their layout """
        super().__init__()
        
        # setup url side
        self.url_select = QComboBox()
        self.url_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.url_input = QLineEdit()
        self.url_input.setMinimumWidth(150)
        self.url_save = QPushButton("Save")
        
        self.url_area = QPlainTextEdit()

        url_selection_layout = QHBoxLayout()
        url_selection_layout.addWidget(self.url_select)
        url_selection_layout.addWidget(self.url_input)
        url_selection_layout.addWidget(self.url_save)

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
        self.blacklist_save = QPushButton("Save")
        
        self.blacklist_area = QPlainTextEdit()
        
        blacklist_selection_layout = QHBoxLayout()
        blacklist_selection_layout.addWidget(self.blacklist_select)
        blacklist_selection_layout.addWidget(self.blacklist_input)
        blacklist_selection_layout.addWidget(self.blacklist_save)

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
        
        crawl_name_input_label = QLabel("Crawl name:")
        self.crawl_name_input = QLineEdit()
        # self.crawl_dir_input_open = FileOpenPushButton(hook_field=self.crawl_name_input,
        #                                                title="Select",
        #                                                mode=QFileDialog.Directory)
        
        crawl_name_input_layout = QHBoxLayout()
        crawl_name_input_layout.addWidget(crawl_name_input_label)
        crawl_name_input_layout.addWidget(self.crawl_name_input)
        # crawl_name_input_layout.addWidget(self.crawl_dir_input_open)
        
        self.crawl_button = QPushButton("Start Crawling")

        self.addWidget(url_blacklist_splitter)
        self.addLayout(crawl_name_input_layout)
        self.addWidget(self.crawl_button)
        
        self.cnt = CrawlerController(self)
