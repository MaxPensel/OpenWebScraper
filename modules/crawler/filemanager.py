"""
Created on 20.07.2019

@author: Maximilian Pensel
"""
import json
import os
import shutil
import sys
import traceback
import pandas

from core.Workspace import WorkspaceManager

raw_data_path = os.path.join("data", "raw")
running_crawl_settings_path = "running"
url_file_extension = "urls"
blacklist_file_extension = "blacklist"


def get_url_filenames():
    global url_file_extension
    wsm = WorkspaceManager()

    return __get_filenames_of_type("." + url_file_extension, wsm.get_workspace())


def get_blacklist_filenames():
    global blacklist_file_extension
    wsm = WorkspaceManager()

    return __get_filenames_of_type("." + blacklist_file_extension, wsm.get_workspace())


def get_crawlnames():
    global raw_data_path
    wsm = WorkspaceManager()
    raw_fullpath = os.path.join(wsm.get_workspace(), raw_data_path)

    return __get_filenames_of_type("", raw_fullpath, directories=True)


def get_url_content(filename):
    global url_file_extension
    filepath = os.path.join(WorkspaceManager().get_workspace(), filename + "." + url_file_extension)

    return __get_file_content(filepath)


def get_blacklist_content(filename):
    global blacklist_file_extension
    filepath = os.path.join(WorkspaceManager().get_workspace(), filename + "." + blacklist_file_extension)

    return __get_file_content(filepath)


def save_url_content(content, filename):
    if not filename:
        print("Error: please specify a filename before saving.", file=sys.stderr)
        return

    global url_file_extension
    filepath = os.path.join(WorkspaceManager().get_workspace(), filename + "." + url_file_extension)

    __save_file_content(content, filepath)


def save_blacklist_content(content, filename):
    if not filename:
        print("Error: please specify a filename before saving.", file=sys.stderr)
        return

    global blacklist_file_extension
    filepath = os.path.join(WorkspaceManager().get_workspace(), filename + "." + blacklist_file_extension)

    __save_file_content(content, filepath)


def get_running_crawls():
    global running_crawl_settings_path
    wsm = WorkspaceManager()

    return __get_filenames_of_type(".json", os.path.join(wsm.get_workspace(), running_crawl_settings_path))


def save_crawl_settings(name, settings):
    if not name:
        print("Error: please name the crawl before starting it.", file=sys.stderr)
        return

    global running_crawl_settings_path
    try:
        os.makedirs(os.path.join(WorkspaceManager().get_workspace(), running_crawl_settings_path), exist_ok=True)
        filepath = os.path.join(WorkspaceManager().get_workspace(), running_crawl_settings_path, name + ".json")

        __save_file_content(json.dumps(settings), filepath)
    except Exception as exc:
        print(traceback.format_exc())
        print(exc)
        return False

    return filepath


def delete_and_clean(path, ignore_empty=False):
    if os.path.isfile(path):
        os.remove(path)
        path = os.path.dirname(path)

    # only delete the directory if it is empty, unless otherwise specified
    if ignore_empty or not os.listdir(path):
        # combination of the following three delete the full directory tree whose root is specified by path
        shutil.rmtree(path)
        os.makedirs(path)
        os.removedirs(path)


def make_raw_data_path(crawl: str):
    global raw_data_path
    fullpath = os.path.join(WorkspaceManager().get_workspace(), raw_data_path, crawl)
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)


def create_csv(crawl: str, domain: str, overwrite=False, incomplete=True):
    global raw_data_path
    inc = "-INCOMPLETE" if incomplete else ""
    fullpath = os.path.join(WorkspaceManager().get_workspace(), raw_data_path, crawl, domain + inc + ".csv")

    if overwrite or not os.path.exists(fullpath):
        df = pandas.DataFrame(columns=["url", "content", "depth"])
        df.to_csv(fullpath, sep=";", index=False, encoding="utf-8")


def add_to_csv(crawl: str, domain: str, data: dict, incomplete=True):
    global raw_data_path
    inc = "-INCOMPLETE" if incomplete else ""
    fullpath = os.path.join(WorkspaceManager().get_workspace(), raw_data_path, crawl, domain + inc + ".csv")

    if os.path.exists(fullpath):
        df = pandas.DataFrame.from_dict(data)
        df.to_csv(fullpath, mode="a", sep=";", index=False, encoding="utf-8", header=False, line_terminator="")


def complete_csv(crawl: str, domain: str):
    global raw_data_path
    inc = "-INCOMPLETE"
    fullpath_inc = os.path.join(WorkspaceManager().get_workspace(), raw_data_path, crawl, domain + inc + ".csv")
    fullpath_com = os.path.join(WorkspaceManager().get_workspace(), raw_data_path, crawl, domain + ".csv")

    shutil.move(fullpath_inc, fullpath_com)


def __get_filenames_of_type(ext, path, directories=False):
    filenames = []

    try:
        for filename in os.listdir(path):
            if (directories and os.path.isdir(os.path.join(path, filename)))\
                    or (not directories and filename.endswith(ext)):
                filenames.append(os.path.splitext(filename)[0])
    except IOError as err:
        print(err, file=sys.stderr)
    except Exception as exc:
        print(traceback.format_exc())
        print(exc, file=sys.stderr)

    return filenames


def __get_file_content(path):
    content = ""
    try:
        with open(path) as in_file:
            content = in_file.read()
    except IOError as err:
        print(err, file=sys.stderr)
    except Exception as exc:
        print(traceback.format_exc())
        print(exc, file=sys.stderr)

    return content


def __save_file_content(content, path):
    try:
        with open(path, "w") as out_file:
            out_file.write(content)
        print("Content successfully saved to {0}".format(path))
    except IOError as err:
        print(err, file=sys.stderr)
