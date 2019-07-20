"""
Created on 20.07.2019

@author: Maximilian Pensel
"""
import os


class WorkspaceManager:
    class __WorkspaceManager:

        def __init__(self, path=""):
            self._default_workspace = "default_workspace"
            self._workspace_path = path

            self.get_workspace() # calling this on init ensures that the workspace always exists

        def is_workspace_selected(self):
            """ Determine if a custom workspace is selected. """
            return self._workspace_path is not ""

        def get_workspace(self):
            """ Provides an existing workspace path, either the previously selected one, or _default_workspace"""
            if not self.is_workspace_selected():
                ws_path = self._default_workspace
            else:
                ws_path = self._workspace_path

            WorkspaceManager._create_workspace_path(ws_path)  # in any case, make sure the path exists upon fetching it
            return ws_path

        def set_workspace(self, path):
            """ Set the current workspace to path, creating it if necessary in the process. """
            WorkspaceManager._create_workspace_path(path)
            self._workspace_path = path

    # End of inner __WorkspaceManager

    _instance = None

    def __init__(self, path=""):
        if WorkspaceManager._instance is None:
            WorkspaceManager._instance = WorkspaceManager.__WorkspaceManager(path)
        else:
            if path:
                print("Attention, WorkspaceManager singleton already exists. The current workspace is {0}."
                      .format(self.get_workspace()))

    def __getattr__(self, item):
        return getattr(self._instance, item)

    @staticmethod
    def _create_workspace_path(path):
        os.makedirs(path, exist_ok=True)
