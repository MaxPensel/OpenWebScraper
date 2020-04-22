"""
Created on 22.04.2020

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
from core.QtExtensions import VerticalContainer, HorizontalContainer, FileOpenPushButton

from PyQt5.QtWidgets import QLineEdit, QLabel, QPlainTextEdit, QComboBox, QSpacerItem, QSizePolicy, QFrame, QPushButton, \
    QTableView, QProgressBar
import core
from modules.analyzer.controller import AnalyzerController
from modules.template import LOG


class AnalyzerView(VerticalContainer):

    def __init__(self):
        """ Initialises the components of this widget with their layout """
        super().__init__()
        LOG.info("Initialising analyzer view.")

        self.crawl_selector = QComboBox()
        self.stat_generator = QPushButton("Analyze Crawl")
        self.analyzing_feedback_label = QLabel("Analysis:")
        self.analysis_progress_bar = QProgressBar()
        self.stats_view = QTableView()

        title_label = QLabel("<h1>Paragraph Crawl Analyzer</h1>"
                             "<p>Use this tab to create and view statistics of a running or finished crawl. "
                             "For now, such statistics can only be obtained from paragraph-parsed crawl data, not raw "
                             "crawl data."
                             "</p>")

        selection_container = HorizontalContainer()
        selection_container.addWidget(QLabel("Select crawl: "))
        selection_container.addWidget(self.crawl_selector)
        selection_container.addWidget(self.stat_generator)
        selection_container.addWidget(self.analyzing_feedback_label)
        selection_container.addWidget(self.analysis_progress_bar)
        selection_container.layout().addSpacerItem(QSpacerItem(100, 1, QSizePolicy.Expanding, QSizePolicy.Fixed))

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        self.addWidget(title_label)
        self.addWidget(line)
        self.addWidget(selection_container)
        self.addWidget(line)
        self.addWidget(self.stats_view)
        #self.layout().addSpacerItem(QSpacerItem(1, 100, QSizePolicy.Fixed, QSizePolicy.Expanding))

        self.cnt = AnalyzerController(self)
