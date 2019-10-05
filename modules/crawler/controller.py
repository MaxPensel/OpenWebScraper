"""
Created on 27.05.2019

@author: Maximilian Pensel
"""

import os

from PyQt5 import sip
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter, QComboBox, QLineEdit, QPlainTextEdit, QWidget, QLayout

import core
from core.QtExtensions import saturate_combobox, build_save_file_connector
from core.Workspace import WorkspaceManager
from crawlUI import ModLoader
from modules import crawler
from modules.crawler import filemanager
from modules.crawler.model import CrawlSpecification

LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)


class CrawlerController(core.ViewController):

    MOD_PATH = os.path.join(ModLoader.MOD_DIR, "crawler")

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

        # self._view.blacklist_save.setEnabled(False)
        # self._view.url_save.setEnabled(False)
        self._view.crawl_specification_view.url_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        saturate_combobox(self._view.crawl_specification_view.url_select,
                          filemanager.get_url_filenames())

        self._view.crawl_specification_view.blacklist_select.setInsertPolicy(QComboBox.InsertAlphabetically)
        saturate_combobox(self._view.crawl_specification_view.blacklist_select,
                          filemanager.get_blacklist_filenames())

        self._view.crawl_specification_view.url_delete.setDisabled(True)
        self._view.crawl_specification_view.blacklist_delete.setDisabled(True)

        saturate_combobox(self._view.parser_select, crawler.PARSER_WIDGETS.keys(), include_empty=False)
        self._view.parser_select.setCurrentIndex(
            self._view.parser_select.findText(crawler.PARSER_DEFAULT))

        saturate_combobox(self._view.initializer_select, crawler.INITIALIZER_WIDGETS.keys(), include_empty=False)
        self._view.initializer_select.setCurrentIndex(self._view.initializer_select.findText(crawler.INITIALIZER_DEFAULT))

        self.register_parser_view(crawler.PARSER_WIDGETS[crawler.PARSER_DEFAULT])
        self.register_initializer_view(crawler.INITIALIZER_WIDGETS[crawler.INITIALIZER_DEFAULT])

    def setup_behaviour(self):
        """ Setup the behaviour of elements
        
        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

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

        self._view.initializer_select.currentIndexChanged.connect(self.switch_initializer_view)

        # trigger model updates
        self._view.crawl_specification_view.url_area.textChanged.connect(self.update_model)
        self._view.crawl_specification_view.blacklist_area.textChanged.connect(self.update_model)

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

    def switch_parser_view(self):
        key = self._view.parser_select.currentText()
        self.register_parser_view(crawler.PARSER_WIDGETS[key])

    def register_parser_view(self, parser_view_path):
        parser_view = core.get_class(parser_view_path)
        if issubclass(parser_view, QWidget):
            if self._view.crawl_parser_view is not None:
                self._view.parser_settings_layout.removeWidget(self._view.crawl_parser_view)
                sip.delete(self._view.crawl_parser_view)
                self.sub_controllers.remove(self._view.crawl_parser_view.cnt)

            self._view.crawl_parser_view = parser_view()
            if issubclass(parser_view, QWidget):
                self._view.parser_settings_layout.addWidget(self._view.crawl_parser_view)

            self._view.crawl_parser_view.cnt.register_master_cnt(self)
            self.sub_controllers.append(self._view.crawl_parser_view.cnt)

            self.update_view()

    def switch_initializer_view(self):
        key = self._view.initializer_select.currentText()
        self.register_initializer_view(crawler.INITIALIZER_WIDGETS[key])

    def register_initializer_view(self, initializer_view_path):
        init_view = core.get_class(initializer_view_path)
        if issubclass(init_view, QWidget):
            if self._view.crawl_init_view is not None:
                self._view.initializer_layout.removeWidget(self._view.crawl_init_view)
                sip.delete(self._view.crawl_init_view)
                self.sub_controllers.remove(self._view.crawl_init_view.cnt)

            self._view.crawl_init_view = init_view()
            if issubclass(init_view, QWidget):
                self._view.initializer_layout.addWidget(self._view.crawl_init_view)

            self._view.crawl_init_view.cnt.register_master_cnt(self)
            self.sub_controllers.append(self._view.crawl_init_view.cnt)

            self.update_view()

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
                controller._view.crawl_init_view.cnt.reset_view()
        return combobox_connector

    def update_view(self):
        self._view.crawl_specification_view.url_area.setPlainText("\n".join(self.crawl_specification.urls))
        self._view.crawl_specification_view.blacklist_area.setPlainText("\n".join(self.crawl_specification.blacklist))
        for cnt in self.sub_controllers:
            cnt.update_view()

    def update_model(self):
        # eventually we could enforce urls and blacklist to be sets instead of lists here
        self.crawl_specification\
            .update(workspace=WorkspaceManager().get_workspace(),
                    urls=self._view.crawl_specification_view.url_area.toPlainText().splitlines(),
                    blacklist=self._view.crawl_specification_view.blacklist_area.toPlainText().splitlines())
        for cnt in self.sub_controllers:
            cnt.update_model()
        LOG.debug("Crawl specification model updated.")  # this message is triggered very often
