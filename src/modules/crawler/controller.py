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
import validators
from PyQt5.Qt import Qt
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter, QComboBox, QLineEdit, QPlainTextEdit, QLayout

import core
from core.QtExtensions import saturate_combobox, build_save_file_connector, delete_layout
from modules.crawler import filemanager, SETTINGS
from modules.crawler.model import CrawlSpecification
from crawlUI import APP_SETTINGS

LOG = core.simple_logger(modname="crawler", file_path=APP_SETTINGS["general"]["master_log"])


class CrawlerController(core.ViewController):

    def __init__(self, view):
        super().__init__(view)

        self.resettables.extend([view.crawl_specification_view.url_select,
                                view.crawl_specification_view.blacklist_select,
                                view.crawl_specification_view.url_input,
                                view.crawl_specification_view.blacklist_input])

        self.sub_controllers = []

        # for now, init with default pipeline
        self.crawl_specification = CrawlSpecification()

        self.init_elements()

        self.setup_behaviour()

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """

        # initialize url/blacklist/whitelist file selectors
        self._view.crawl_specification_view.url_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        saturate_combobox(self._view.crawl_specification_view.url_select,
                          filemanager.get_url_filenames())

        self._view.crawl_specification_view.blacklist_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        saturate_combobox(self._view.crawl_specification_view.blacklist_select,
                          filemanager.get_blacklist_filenames())

        self._view.crawl_specification_view.whitelist_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        saturate_combobox(self._view.crawl_specification_view.whitelist_select,
                          filemanager.get_whitelist_filenames())

        self._view.crawl_specification_view.url_delete.setDisabled(True)
        self._view.crawl_specification_view.blacklist_delete.setDisabled(True)
        self._view.crawl_specification_view.whitelist_delete.setDisabled(True)

        # initialize highlighting for url area
        self._view.crawl_specification_view.url_highlighter.append_rule(
            (lambda l: l.startswith("#"), Qt.darkMagenta, None)
        )
        self._view.crawl_specification_view.url_highlighter.append_rule(
            (lambda l: validators.url(l), Qt.darkGreen, Qt.red)
        )

        # initialize comboboxes of parser and initializer sub-views
        saturate_combobox(self._view.parser_select, SETTINGS["ui"]["parser"]["widgets"].keys(), include_empty=False)
        self._view.parser_select.setCurrentIndex(
            self._view.parser_select.findText(SETTINGS["ui"]["parser"]["default"]))

        saturate_combobox(self._view.initializer_select,
                          SETTINGS["ui"]["initializer"]["widgets"].keys(),
                          include_empty=False)
        self._view.initializer_select.setCurrentIndex(
            self._view.initializer_select.findText(SETTINGS["ui"]["initializer"]["default"]))

        self.register_sub_view(SETTINGS["ui"]["parser"]["widgets"][SETTINGS["ui"]["parser"]["default"]],
                               self._view.parser_settings_container.layout())
        self.register_sub_view(
            SETTINGS["ui"]["initializer"]["widgets"][SETTINGS["ui"]["initializer"]["default"]],
            self._view.initializer_container.layout())

    def setup_behaviour(self):
        """ Setup the behaviour of elements
        
        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        # setup url, blacklist and whitelist combobox and save button connectors
        # url
        self._view.crawl_specification_view.url_select.currentIndexChanged.connect(
            CrawlerController.load_file_to_editor(self._view.crawl_specification_view.url_select,
                                                  filemanager.get_url_content,
                                                  self._view.crawl_specification_view.url_area,
                                                  self._view.crawl_specification_view.url_input,
                                                  self))
        self._view.crawl_specification_view.url_save.clicked.connect(
            build_save_file_connector(self._view.crawl_specification_view.url_input,
                                      self._view.crawl_specification_view.url_select,
                                      self._view.crawl_specification_view.url_area,
                                      filemanager.save_url_content,
                                      filemanager.get_url_filenames))
        # blacklist
        self._view.crawl_specification_view.blacklist_select.currentIndexChanged.connect(
            CrawlerController.load_file_to_editor(self._view.crawl_specification_view.blacklist_select,
                                                  filemanager.get_blacklist_content,
                                                  self._view.crawl_specification_view.blacklist_area,
                                                  self._view.crawl_specification_view.blacklist_input,
                                                  self))
        self._view.crawl_specification_view.blacklist_save.clicked.connect(
            build_save_file_connector(self._view.crawl_specification_view.blacklist_input,
                                      self._view.crawl_specification_view.blacklist_select,
                                      self._view.crawl_specification_view.blacklist_area,
                                      filemanager.save_blacklist_content,
                                      filemanager.get_blacklist_filenames))
        # whitelist
        self._view.crawl_specification_view.whitelist_select.currentIndexChanged.connect(
            CrawlerController.load_file_to_editor(self._view.crawl_specification_view.whitelist_select,
                                                  filemanager.get_whitelist_content,
                                                  self._view.crawl_specification_view.whitelist_area,
                                                  self._view.crawl_specification_view.whitelist_input,
                                                  self))
        self._view.crawl_specification_view.whitelist_save.clicked.connect(
            build_save_file_connector(self._view.crawl_specification_view.whitelist_input,
                                      self._view.crawl_specification_view.whitelist_select,
                                      self._view.crawl_specification_view.whitelist_area,
                                      filemanager.save_whitelist_content,
                                      filemanager.get_whitelist_filenames))

        # sub view switching
        self._view.parser_select.currentIndexChanged.connect(
            lambda: self.switch_sub_view(SETTINGS["ui"]["parser"]["widgets"],
                                         self._view.parser_settings_container.layout(),
                                         self._view.parser_select)
        )

        self._view.initializer_select.currentIndexChanged.connect(
            lambda: self.set_initializer_info("")
        )
        self._view.initializer_select.currentIndexChanged.connect(
            lambda: self.switch_sub_view(SETTINGS["ui"]["initializer"]["widgets"],
                                         self._view.initializer_container.layout(),
                                         self._view.initializer_select)
        )

        # trigger model updates
        self._view.crawl_specification_view.url_area.textChanged.connect(self.update_model)
        self._view.crawl_specification_view.blacklist_area.textChanged.connect(self.update_model)
        self._view.crawl_specification_view.whitelist_area.textChanged.connect(self.update_model)

    @DeprecationWarning
    def setup_completion(self):
        url_model = QStringListModel()
        url_model.setStringList(filemanager.get_url_filenames())
        url_completer = QCompleter()
        url_completer.setModel(url_model)
        url_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._view.crawl_specification_view.url_input.setCompleter(url_completer)

        blacklist_model = QStringListModel()
        blacklist_model.setStringList(filemanager.get_blacklist_filenames())
        blacklist_completer = QCompleter()
        blacklist_completer.setModel(blacklist_model)
        blacklist_completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._view.crawl_specification_view.blacklist_input.setCompleter(blacklist_completer)

    def switch_sub_view(self, view_dict, layout, combobox):
        key = combobox.currentText()
        self.register_sub_view(view_dict[key], layout)

    def register_sub_view(self, view_classpath, layout):
        view_class = core.get_class(view_classpath)
        if issubclass(view_class, QLayout):
            view = view_class()
            if layout.count() > 1:
                prev_layout = layout.itemAt(1)
                self.sub_controllers.remove(prev_layout.cnt)
                delete_layout(prev_layout)
                layout.removeItem(prev_layout)
            layout.addLayout(view)

            view.cnt.register_master_cnt(self)
            self.sub_controllers.append(view.cnt)
            self.update_view()

    def set_initializer_info(self, text, color="black"):
        self._view.initializer_info.setText(text)
        self._view.initializer_info.setStyleSheet('QLabel { color: %s }' % color)

    @staticmethod
    def load_file_to_editor(combobox: QComboBox,
                            content_loader,
                            text_area: QPlainTextEdit,
                            input_field: QLineEdit,
                            controller):
        def combobox_connector(index):
            if index > 0:  # index 0 should always be empty option, do not load content for that (or index < 0)
                filename = combobox.itemText(index)
                content = content_loader(filename)
                text_area.setPlainText(content)
                input_field.setText(filename)
                for sub_controller in controller.sub_controllers:
                    sub_controller.reset_view()
        return combobox_connector

    def update_view(self):
        self._view.crawl_specification_view.url_area.setPlainText("\n".join(self.crawl_specification.urls))
        self._view.crawl_specification_view.blacklist_area.setPlainText("\n".join(self.crawl_specification.blacklist))
        self._view.crawl_specification_view.whitelist_area.setPlainText("\n".join(self.crawl_specification.whitelist))
        for cnt in self.sub_controllers:
            cnt.update_view()

    def update_model(self):
        # eventually we could enforce urls and blacklist to be sets instead of lists here
        self.crawl_specification\
            .update(urls=self._view.crawl_specification_view.url_area.toPlainText().splitlines(),
                    blacklist=self._view.crawl_specification_view.blacklist_area.toPlainText().splitlines(),
                    whitelist=self._view.crawl_specification_view.whitelist_area.toPlainText().splitlines())
        for cnt in self.sub_controllers:
            cnt.update_model()
        LOG.debug("Crawl specification model updated.")  # this message is triggered very often
