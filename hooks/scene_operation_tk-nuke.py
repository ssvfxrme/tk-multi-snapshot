# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import nuke

import tank
from tank import Hook
from tank import TankError

class SceneOperation(Hook):
    """
    Hook called to perform an operation with the 
    current scene
    """
    def execute(self, *args, **kwargs):
        """
        Main hook entry point
        
        :operation: String
                    Scene operation to perform
        
        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)
                    
        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    all others     - None
        """
        engine = self.parent.engine
        if hasattr(engine, "hiero_enabled") and engine.hiero_enabled:
            return self._hiero_execute(*args, **kwargs)
        else:
            return self._nuke_execute(*args, **kwargs)

    def _hiero_execute(self, operation, file_path, **kwargs):
        import hiero.core
        if operation == "current_path":
            # return the current script path
            project = self._get_current_project()
            curr_path = project.path().replace("/", os.path.sep)
            return curr_path
        
        elif operation == "open":
            # first close the current project then open the specified file 
            project = self._get_current_project()
            project.close()
            # manually fire signal since Hiero doesn't fire this when loading 
            # from the tk file manager
            hiero.core.events.sendEvent("kBeforeProjectLoad", None)
            hiero.core.openProject(file_path.replace(os.path.sep, "/"))

        elif operation == "save":
            # save the current script:
            project = self._get_current_project()
            project.save()        
    
    def _nuke_execute(self, operation, file_path, **kwargs):
        if file_path:
            file_path = file_path.replace("/", os.path.sep)        
        
        if operation == "current_path":
            # return the current script path
            return nuke.root().name().replace("/", os.path.sep)
        elif operation == "open":
            # open the specified script into the current window
            if nuke.root().modified():
                raise TankError("Script is modified!")
            nuke.scriptClear()
            nuke.scriptOpen(file_path)
        elif operation == "save":
            # save the current script:
            nuke.scriptSave()

    def _get_current_project(self):
        """
        Returns the current project based on where in the UI the user clicked 
        """
        import hiero.core
        # get the menu selection from hiero engine
        selection = self.parent.engine.get_menu_selection()

        if len(selection) != 1:
            raise TankError("Please select a single Project!")
        
        if not isinstance(selection[0] , hiero.core.Bin):
            raise TankError("Please select a Hiero Project!")
            
        project = selection[0].project()
        if project is None:
            # apparently bins can be without projects (child bins I think)
            raise TankError("Please select a Hiero Project!")
        
        return project
