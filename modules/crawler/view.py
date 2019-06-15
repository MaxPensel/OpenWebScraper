'''
Created on 27.05.2019

@author: Maximilian Pensel
'''
from core.QtExtensions import VerticalContainer, FileOpenPushButton
from modules.crawler.controller import CrawlerController
from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit, QPushButton, QSplitter
from PyQt5.QtWidgets import QHBoxLayout

class CrawlerWidget(VerticalContainer):
    
    def __init__(self):
        ''' Initialises the components of this widget with their layout '''
        super().__init__()
        
        ## setup url side
        url_input_label  = QLabel("URL File:")
        self._url_input  = QLineEdit()
        self._url_input_open  = FileOpenPushButton(hook_field=self._url_input)
        
        self._url_area   = QPlainTextEdit()
        self._url_load   = QPushButton("Load")
        self._url_append = QPushButton("Append")
        self._url_save   = QPushButton("Save")
        
        url_input_layout = QHBoxLayout()
        url_input_layout.addWidget(url_input_label)
        url_input_layout.addWidget(self._url_input)
        url_input_layout.addWidget(self._url_input_open)
        
        url_buttons_layout = QHBoxLayout()
        for button in [self._url_load, self._url_append, self._url_save]:
            url_buttons_layout.addWidget(button)
        
        url_container = VerticalContainer()
        url_container.addLayout(url_input_layout)
        url_container.addLayout(url_buttons_layout)
        url_container.addWidget(self._url_area)
        #for element in [url_input_layout, url_buttons_layout, self._url_area]:
            
        
        ## setup blacklist side
        blacklist_input_label  = QLabel("Blacklist File:")
        self._blacklist_input  = QLineEdit()
        self._blacklist_input_open  = FileOpenPushButton(hook_field=self._blacklist_input)
        
        self._blacklist_area   = QPlainTextEdit()
        self._blacklist_load   = QPushButton("Load")
        self._blacklist_append = QPushButton("Append")
        self._blacklist_save   = QPushButton("Save")
        
        blacklist_input_layout = QHBoxLayout()
        blacklist_input_layout.addWidget(blacklist_input_label)
        blacklist_input_layout.addWidget(self._blacklist_input)
        blacklist_input_layout.addWidget(self._blacklist_input_open)
        
        blacklist_buttons_layout = QHBoxLayout()
        for button in [self._blacklist_load, self._blacklist_append, self._blacklist_save]:
            blacklist_buttons_layout.addWidget(button)
        
        blacklist_container = VerticalContainer()
        blacklist_container.addLayout(blacklist_input_layout)
        blacklist_container.addLayout(blacklist_buttons_layout)
        blacklist_container.addWidget(self._blacklist_area)
        #for element in [self._blacklist_input, blacklist_buttons_layout, self._blacklist_area]:
            
        
        ## put together
        url_blacklist_splitter = QSplitter()
        url_blacklist_splitter.setChildrenCollapsible(False)
        url_blacklist_splitter.addWidget(url_container)
        url_blacklist_splitter.addWidget(blacklist_container)
        
        crawl_dir_input_label  = QLabel("Crawler output directory:")
        self._crawl_dir_input  = QLineEdit()
        self._crawl_dir_input_open  = FileOpenPushButton(hook_field=self._crawl_dir_input)
        
        crawl_dir_input_layout = QHBoxLayout()
        crawl_dir_input_layout.addWidget(crawl_dir_input_label)
        crawl_dir_input_layout.addWidget(self._crawl_dir_input)
        crawl_dir_input_layout.addWidget(self._crawl_dir_input_open)
        
        self._crawl_button = QPushButton("Start Crawling")
        
        
        self.addWidget(url_blacklist_splitter)
        self.addLayout(crawl_dir_input_layout)
        self.addWidget(self._crawl_button)
        
        self.cnt = CrawlerController(self)


TITLE       = "Crawler"
MAIN_WIDGET = CrawlerWidget