"""
Class that handles installSynApps settings and metadata
"""

import os
import json

class MetaDataController:
    """
    Class for handling metadata and settings

    Attributes
    ----------
    pref_loc : str
        location for metadata/settings
    metadata : dict
        dictionary that stores all settings/metadata

    Methods
    -------
    save_metadata()
        function that writes the loaded metadata. Called at GUI close
    """

    def __init__(self):
        """ Constructor for MetaDataController """

        self.pref_loc = '.metadata'
        if not os.path.exists('.metadata'):
            try:
                os.mkdir('.metadata')
            except OSError:
                self.pref_loc = None

        if self.pref_loc is None:
            self.metadata = {}
        elif os.path.exists(self.pref_loc + '/isa_settings.json'):
            with open(self.pref_loc + '/isa_settings.json', 'r') as json_file:
                self.metadata = json.load(json_file)
        else:
            self.metadata = {}



    def save_metadata(self):
        """ Function that saves the loaded metadata to a json file """

        if self.pref_loc is None:
            return False, 'ERROR - Could not load preferences dir'
        if os.path.exists(self.pref_loc + '/isa_settings.json'):
            os.remove(self.pref_loc + '/isa_settings.json')

        with open(self.pref_loc + '/isa_settings.json', 'w') as set_file:
            json.dump(self.metadata, set_file) 

    