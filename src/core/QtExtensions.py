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
import toml
from PyQt5 import QtCore
from PyQt5.Qt import Qt
from PyQt5.QtGui import QSyntaxHighlighter
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QFileDialog, QBoxLayout, QMessageBox, QComboBox, \
    QPlainTextEdit, QFrame, QMainWindow, QTextEdit
from PyQt5.QtWidgets import QLayout, QVBoxLayout, QHBoxLayout

import core


class ArrangedContainer(QWidget):

    def __init__(self, layout: QBoxLayout = QVBoxLayout()):
        super().__init__()
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, widget: QWidget):
        self.layout().addWidget(widget)

    def addLayout(self, layout: QLayout):
        self.layout().addLayout(layout)


class HorizontalContainer(ArrangedContainer):

    def __init__(self):
        super().__init__(QHBoxLayout())


class VerticalContainer(ArrangedContainer):

    def __init__(self):
        super().__init__(QVBoxLayout())


class HorizontalSeparator(QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class FileOpenPushButton(QPushButton):

    def __init__(self,
                 hook_field: QLineEdit = None,
                 hook=None,
                 title: str = "Open",
                 mode: QFileDialog.FileMode = QFileDialog.AnyFile):
        super().__init__(title)
        self._hook_field = hook_field
        if callable(hook):
            self._hook = hook
        elif hook_field is not None:
            self._hook = self.fill_field

        self.clicked.connect(self.on_click)

        self._dialog = QFileDialog(self)
        self._dialog.setFileMode(mode)
        self._dialog.setDirectory(".")
        if mode == QFileDialog.Directory:
            self._dialog.setOption(QFileDialog.ShowDirsOnly)

    def on_click(self):
        if self._dialog.exec_():
            file_name = self._dialog.selectedFiles()[0]
            if callable(self._hook):
                self._hook(file_name)

    def fill_field(self, path):
        """ Fill the hook_field (if given and of type QLineEdit) with the selected file/path """
        self._hook_field.setText(path)


class SimpleMessageBox(QMessageBox):

    def __init__(self, title, text, details="", icon=None):
        super().__init__()
        if icon:
            self.setIcon(icon)
        self.setText(text)
        self.setInformativeText(details)
        self.setWindowTitle(title)
        self.setTextFormat(Qt.RichText)


class SimpleYesNoMessage(SimpleMessageBox):

    def __init__(self, title, text, details=""):
        super().__init__(title, text, details, QMessageBox.Question)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    def is_confirmed(self) -> bool:
        return self.exec_() == QMessageBox.Ok


class SimpleErrorInfo(SimpleMessageBox):

    def __init__(self, title, text, details=""):
        super().__init__(title, text, details, QMessageBox.Critical)
        self.setStandardButtons(QMessageBox.Ok)


class LineHighlighter(QSyntaxHighlighter):

    def highlightBlock(self, text: str) -> None:
        for checker, line_format, format_else in self.color_conditions:
            if checker(text):
                self.setFormat(0, len(text), line_format)
                break
            elif format_else:
                self.setFormat(0, len(text), format_else)
                break

    def append_rule(self, rule):
        if not hasattr(self, "color_conditions"):
            self.color_conditions = list()
        self.color_conditions.append(rule)

###
# Several reoccurring routines to handle Qt Elements
###


def reset_combobox(combobox: QComboBox):
    """
    Simply resets the index of the given QComboBox to 0.
    :param combobox:
    :return:
    """
    combobox.setCurrentIndex(0)


def saturate_combobox(combobox: QComboBox, items: [str], include_empty=True):
    """
    Saturates the given QComboBox with the given list of string elements.
    :param combobox:
    :param items:
    :param include_empty: If True, an additional empty string element is inserted at index 0.
    :return:
    """
    for i in range(combobox.count()):
        combobox.removeItem(0)
    if include_empty:
        combobox.addItem("")
    combobox.addItems(items)


def build_save_file_connector(input_field: QLineEdit,
                              combobox: QComboBox,
                              text_area: QPlainTextEdit,
                              content_saver,
                              content_loader):
    """
    Defines and returnes a connector for the click of a save-file button.
    It connects the given view elements input_field, combobox and text_area.
    The interaction of this trio abstracts a filesystem interaction. Essentially the content given in text_area
    is saved to the file named in input_field, which is then "stored" in the list of files in the combobox.
    As a result, certain safety dialogs are invoked when saving content to an "already existing file".
    The actual filesystem interactions, saving content to a file on the hard disk and reloading the list of
    files in the combobox is provided by content_saver and content_loader respectively.
    :param input_field: Field to provide the filename to be saved to.
    :param combobox:
    :param text_area:
    :param content_saver:
    :param content_loader:
    :return:
    """
    def save_button_connector():
        filename = input_field.displayText()

        if not filename:
            msg = SimpleErrorInfo("Error", "You have to specify a name to be associated with your data.")
            msg.exec()
            return

        idx = combobox.findText(filename, flags=QtCore.Qt.MatchExactly)
        if idx >= 0 and idx is not combobox.currentIndex():
            msg = SimpleYesNoMessage("Continue?",
                                     "There is already data associated with '{0}'. Continue and overwrite?"
                                     .format(filename))
            if not msg.is_confirmed():
                return None

        core.MASTER_LOGGER.info("Saving data as {0}".format(filename))
        content = text_area.toPlainText()
        content_saver(content, filename)
        saturate_combobox(combobox, content_loader())
        combobox.setCurrentIndex(combobox.findText(filename, flags=QtCore.Qt.MatchExactly))
    return save_button_connector


def reset_element(element):
    """
    Resets the given Qt element depending on what it is, e.g. clearing a QLineEdit, setting the index of a
    QComboBox to 0, etc.
    :param element:
    :return:
    """
    if isinstance(element, QComboBox):
        element.setCurrentIndex(0)
    elif isinstance(element, QLineEdit):
        element.setText("")
    else:
        core.MASTER_LOGGER.warning("No routine for resetting element of type {0}".format(type(element)))


def delete_layout(layout):
    if isinstance(layout, QLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                delete_layout(widget)
                layout.removeItem(widget)


class TomlConfigWindow(QMainWindow):

    open_window = None

    @staticmethod
    def create_window(toml_file, parent=None):
        if not TomlConfigWindow.open_window:
            TomlConfigWindow.open_window = TomlConfigWindow(toml_file, parent)
            TomlConfigWindow.open_window.show()

    def __init__(self, toml_file, parent=None):
        super().__init__(parent)

        self.toml_file = toml_file

        self.setWindowTitle("Settings - " + toml_file)

        self.toml_area = QTextEdit()
        with open(toml_file, "r") as tf:
            self.toml_area.setText(tf.read())

        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_content)

        central = VerticalContainer()
        central.addWidget(self.toml_area)
        central.addWidget(save_button)

        self.setCentralWidget(central)

        # Automatically determine a good size with the given layout
        self.setFixedSize(500, 600)

    def save_content(self):
        content = self.toml_area.toPlainText()
        try:
            toml.loads(content)

            with open(self.toml_file, "w") as tf:
                tf.write(content)
            SimpleMessageBox("File Saved", "Successfully saved configuration.").exec()
        except toml.TomlDecodeError as exc:
            core.MASTER_LOGGER.exception(f"{type(exc).__name__}: {exc}")
            SimpleErrorInfo("Error", "Content not in correct toml formal.", details=str(exc)).exec()

    def closeEvent(self, event):
        TomlConfigWindow.open_window = None
