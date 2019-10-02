"""
Created on 27.05.2019

@author: Maximilian Pensel
"""
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QFileDialog, QBoxLayout, QMessageBox, QComboBox, \
    QPlainTextEdit
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


class FileOpenPushButton(QPushButton):

    def __init__(self,
                 hook_field: QLineEdit = None,
                 hook=None,
                 title: str = "Open",
                 mode: QFileDialog.FileMode = QFileDialog.AnyFile):
        super().__init__(title)
        self._hook_field = hook_field
        if not callable(hook) and hook_field is not None:
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
        self.setIcon(icon)
        self.setText(text)
        self.setInformativeText(details)
        self.setWindowTitle(title)


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