"""
Created on 27.05.2019

@author: Maximilian Pensel
"""
from core.QtExtensions import VerticalContainer, FileOpenPushButton
from modules.crawler.controller import CrawlerController
from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit, QPushButton, QSplitter,\
    QFileDialog
from PyQt5.QtWidgets import QHBoxLayout


class CrawlerWidget(VerticalContainer):
    
    def __init__(self):
        """ Initialises the components of this widget with their layout """
        super().__init__()
        
        # setup url side
        url_input_label = QLabel("URL File:")
        self.url_input = QLineEdit()
        self.url_input_open = FileOpenPushButton(hook_field=self.url_input)
        
        self.url_area = QPlainTextEdit()
        self.url_load = QPushButton("Load")
        self.url_append = QPushButton("Append")
        self.url_save = QPushButton("Save")
        
        url_input_layout = QHBoxLayout()
        url_input_layout.addWidget(url_input_label)
        url_input_layout.addWidget(self.url_input)
        url_input_layout.addWidget(self.url_input_open)
        
        url_buttons_layout = QHBoxLayout()
        for button in [self.url_load, self.url_append, self.url_save]:
            url_buttons_layout.addWidget(button)
        
        url_container = VerticalContainer()
        url_container.addLayout(url_input_layout)
        url_container.addLayout(url_buttons_layout)
        url_container.addWidget(self.url_area)
        # for element in [url_input_layout, url_buttons_layout, self.url_area]:

        # setup blacklist side
        blacklist_input_label = QLabel("Blacklist File:")
        self.blacklist_input = QLineEdit()
        self.blacklist_input_open = FileOpenPushButton(hook_field=self.blacklist_input)
        
        self.blacklist_area = QPlainTextEdit()
        self.blacklist_load = QPushButton("Load")
        self.blacklist_append = QPushButton("Append")
        self.blacklist_save = QPushButton("Save")
        
        blacklist_input_layout = QHBoxLayout()
        blacklist_input_layout.addWidget(blacklist_input_label)
        blacklist_input_layout.addWidget(self.blacklist_input)
        blacklist_input_layout.addWidget(self.blacklist_input_open)
        
        blacklist_buttons_layout = QHBoxLayout()
        for button in [self.blacklist_load, self.blacklist_append, self.blacklist_save]:
            blacklist_buttons_layout.addWidget(button)
        
        blacklist_container = VerticalContainer()
        blacklist_container.addLayout(blacklist_input_layout)
        blacklist_container.addLayout(blacklist_buttons_layout)
        blacklist_container.addWidget(self.blacklist_area)
        # for element in [self.blacklist_input, blacklist_buttons_layout, self.blacklist_area]:

        # put together
        url_blacklist_splitter = QSplitter()
        url_blacklist_splitter.setChildrenCollapsible(False)
        url_blacklist_splitter.addWidget(url_container)
        url_blacklist_splitter.addWidget(blacklist_container)
        
        crawl_dir_input_label = QLabel("Crawler output directory:")
        self.crawl_dir_input = QLineEdit()
        self.crawl_dir_input_open = FileOpenPushButton(hook_field=self.crawl_dir_input,
                                                       title="Select",
                                                       type=QFileDialog.Directory)
        
        crawl_dir_input_layout = QHBoxLayout()
        crawl_dir_input_layout.addWidget(crawl_dir_input_label)
        crawl_dir_input_layout.addWidget(self.crawl_dir_input)
        crawl_dir_input_layout.addWidget(self.crawl_dir_input_open)
        
        self.crawl_button = QPushButton("Start Crawling")

        self.addWidget(url_blacklist_splitter)
        self.addLayout(crawl_dir_input_layout)
        self.addWidget(self.crawl_button)
        
        self.cnt = CrawlerController(self)


TITLE = "Crawler"
MAIN_WIDGET = CrawlerWidget
VERSION = "1.0.0"
