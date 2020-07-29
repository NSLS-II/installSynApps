"""Class that handles installSynApps settings and metadata
"""

import os
import json

class MetaDataController:
    """Class for handling metadata and settings

    Attributes
    ----------
    pref_loc : str
        location for metadata/settings
    metadata : dict
        dictionary that stores all settings/metadata
    """


    def __init__(self):
        """Initialzier for MetaDataController
        """

        home = os.path.expanduser('~')

        self.pref_loc = os.path.join(home, '.epics-install')
        if not self.pref_loc:
            try:
                os.mkdir(self.pref_loc)
            except OSError:
                self.pref_loc = None

        if self.pref_loc is None:
            self.metadata = {}
        elif os.path.exists(self.pref_loc + '/epics_install_metadata.json'):
            with open(self.pref_loc + '/epics_install_metadata.json', 'r') as json_file:
                self.metadata = json.load(json_file)
        else:
            self.metadata = {}


    def save_metadata(self):
        """Function that saves the loaded metadata to a json file
        """

        if self.pref_loc is None:
            return False, 'ERROR - Could not load preferences dir'
        
        settings_file_path = os.path.join(self.pref_loc, 'epics_install_metadata.json')
        
        if os.path.exists(settings_file_path):
            os.remove(settings_file_path)

        with open(settings_file_path, 'w') as set_file:
            json.dump(self.metadata, set_file) 

        return True, 'Saved preference metadata'
