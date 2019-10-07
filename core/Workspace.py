"""
Created on 20.07.2019

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
import os
import core

LOG_DIR = "logs"
LOG = core.simple_logger(file_path=core.MASTER_LOG)


class WorkspaceManager:
    class __WorkspaceManager:

        def __init__(self, path=""):
            self._default_workspace = os.path.join(os.getcwd(), "default_workspace")
            self._workspace_path = path

            self.get_workspace()  # calling this on init ensures that the workspace always exists

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
            LOG.info("Switched workspace to {0}.".format(self._workspace_path))

    # End of inner __WorkspaceManager

    _instance = None

    def __init__(self, path=""):
        if WorkspaceManager._instance is None:
            WorkspaceManager._instance = WorkspaceManager.__WorkspaceManager(path)
        else:
            if path:
                LOG.warning("Attention, calling WorkspaceManager.__init__ with non-empty path even though "
                            "WorkspaceManager singleton already exists. The current workspace is {0}."
                            .format(self.get_workspace()))

    def __getattr__(self, item):
        return getattr(self._instance, item)

    @staticmethod
    def _create_workspace_path(path):
        os.makedirs(path, exist_ok=True)
