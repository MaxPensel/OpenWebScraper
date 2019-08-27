"""
The filemanager is the interface between a module and the operating system,
at least as far as filesystem interactions are concerned.
A filemanager is module-specific because it handles pathing and the directory structure.
Modules may also rely on the filemanager of other modules.
For some modules such a dependency makes sense and is semantically required, but be
aware that an overuse of this dependency reduces the separability of modules.

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

running_crawl_settings_path = "running"
url_file_extension = "urls"
blacklist_file_extension = "blacklist"
incomplete_flag = "-INCOMPLETE"


def get_crawl_raw_path(crawlname):
    """ Returns '%workspace-dir%/data/%crawlname%/raw/' """
    return os.path.join(get_crawl_path(crawlname), "raw")


def get_crawl_path(crawlname):
    """ Returns '%workspace-dir%/data/%crawlname%/' """
    return os.path.join(get_data_path(), crawlname)


def get_data_path():
    """ Returns '%workspace-dir%/data/' """
    return os.path.join(WorkspaceManager().get_workspace(), "data")


def get_url_filenames():
    global url_file_extension
    wsm = WorkspaceManager()

    return __get_filenames_of_type("." + url_file_extension, wsm.get_workspace())


def get_blacklist_filenames():
    global blacklist_file_extension
    wsm = WorkspaceManager()

    return __get_filenames_of_type("." + blacklist_file_extension, wsm.get_workspace())


def get_crawlnames():
    return __get_filenames_of_type("", get_data_path(), directories=True)


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


def save_dataframe(crawl: str, name: str, df: pandas.DataFrame):
    df.to_excel(os.path.join(get_crawl_path(crawl), name + ".xls"))


def extend_dataframe(crawl: str, name: str, df: pandas.DataFrame):
    df_file = os.path.join(get_crawl_path(crawl), name + ".xls")
    if os.path.exists(df_file):
        base_df = pandas.read_excel(df_file)
        columns = base_df.columns.union(df.columns)
        base_df = base_df.reindex(columns=columns, fill_value=0)
        df = df.reindex(columns=columns, fill_value=0)
        df = base_df.append(df)

    save_dataframe(crawl, name, df)


def get_running_crawls():
    global running_crawl_settings_path
    wsm = WorkspaceManager()

    return __get_filenames_of_type(".json", os.path.join(wsm.get_workspace(), running_crawl_settings_path))


def get_path_to_run_spec(crawl_name):
    global running_crawl_settings_path
    wsm = WorkspaceManager()
    path = os.path.join(wsm.get_workspace(), running_crawl_settings_path, crawl_name + ".json")
    if os.path.exists(path):
        return path
    else:
        return None


def save_crawl_settings(name, settings):
    if not name:
        print("Error: please name the crawl before starting it.", file=sys.stderr)
        return

    global running_crawl_settings_path
    try:
        os.makedirs(os.path.join(WorkspaceManager().get_workspace(), running_crawl_settings_path), exist_ok=True)
        filepath = os.path.join(WorkspaceManager().get_workspace(), running_crawl_settings_path, name + ".json")

        __save_file_content(json.dumps(settings, sort_keys=True, indent=4, separators=(',', ': ')), filepath)
    except Exception as exc:
        print(traceback.format_exc())
        print("[save_crawl_settings] - {0}".format(exc))
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
    path = get_crawl_raw_path(crawl)
    if not os.path.exists(path):
        os.makedirs(path)


def create_csv(crawl: str, domain: str, overwrite=False, incomplete=True):
    global incomplete_flag
    inc = incomplete_flag if incomplete else ""
    fullpath = os.path.join(get_crawl_raw_path(crawl), domain + inc + ".csv")

    if overwrite or not os.path.exists(fullpath):
        df = pandas.DataFrame(columns=["url", "content", "depth"])
        df.to_csv(fullpath, sep=";", index=False, encoding="utf-8")


def add_to_csv(crawl: str, domain: str, data: dict, incomplete=True):
    global incomplete_flag
    inc = incomplete_flag if incomplete else ""
    fullpath = os.path.join(get_crawl_raw_path(crawl), domain + inc + ".csv")

    if os.path.exists(fullpath):
        df = pandas.DataFrame.from_dict(data)
        df.to_csv(fullpath, mode="a", sep=";", index=False, encoding="utf-8", header=False, line_terminator="")


def complete_csv(crawl: str, domain: str):
    global incomplete_flag
    crawl_path = get_crawl_raw_path(crawl)
    fullpath_inc = os.path.join(crawl_path, domain + incomplete_flag + ".csv")
    fullpath_com = os.path.join(crawl_path, domain + ".csv")

    shutil.move(fullpath_inc, fullpath_com)


def finalize_crawl(crawl):
    global running_crawl_settings_path
    running_filename = crawl + ".json"
    running_file = os.path.join(WorkspaceManager().get_workspace(), running_crawl_settings_path, running_filename)
    destination = os.path.join(get_crawl_path(crawl), running_filename)

    shutil.move(running_file, destination)

    delete_and_clean(os.path.join(WorkspaceManager().get_workspace(), running_crawl_settings_path))


def __get_filenames_of_type(ext, path, directories=False):
    filenames = []

    try:
        for filename in os.listdir(path):
            if directories and os.path.isdir(os.path.join(path, filename)):
                filenames.append(filename)
            elif not directories and filename.endswith(ext):
                filenames.append(os.path.splitext(filename)[0])
    except IOError as err:
        print("[__get_filenames_of_type] - {0}".format(err), file=sys.stderr)
    except Exception as exc:
        print(traceback.format_exc())
        print("[__get_filenames_of_type] - {0}".format(exc), file=sys.stderr)

    return filenames


def __get_file_content(path):
    content = ""
    try:
        with open(path) as in_file:
            content = in_file.read()
    except IOError as err:
        print("[__get_file_content] - {0}".format(err), file=sys.stderr)
    except Exception as exc:
        print(traceback.format_exc())
        print("[__get_file_content] - {0}".format(exc), file=sys.stderr)

    return content


def __save_file_content(content, path):
    try:
        with open(path, "w") as out_file:
            out_file.write(content)
        print("Content successfully saved to {0}".format(path))
    except IOError as err:
        print(err, file=sys.stderr)
