import os

from national_map_utility import NationalMapUtility


class StateDataSettings:

    def __init__(self, state, configuration):
        self.state = state.lower()
        self.configuration = configuration
        self.data = {
            'scratch_folder': '',
            'scratch_geodatabase': '',
            'precisely_geodatabase': ''
        }
        self._read_configuration()

    def __del__(self):
        del self.state
        del self.configuration
        del self.data

    def _read_configuration(self):
        _ = self.get_precisely_file_geodatabase()
        _ = self.get_scratch_file_geodatabase()

    def get_precisely_file_geodatabase(self):
        if self.data['precisely_geodatabase'] != '':
            return self.data['precisely_geodatabase']

        fgdb_location = self.configuration.data['Precisely']['fgdb_location']
        version = self.configuration.data['Precisely']['version']
        precisely_gdb_name = f'usa_{self.state}_navprem_{version}.gdb'
        precisely_geodatabase = os.path.join(fgdb_location, precisely_gdb_name)
        self.data['precisely_geodatabase'] = precisely_geodatabase
        return precisely_geodatabase

    def get_scratch_file_geodatabase(self):
        if self.data['scratch_geodatabase'] != '':
            return self.data['scratch_geodatabase']

        scratch_folder = self.configuration.data['Outputs']['scratch_folder']
        NationalMapUtility.ensure_path_exists(scratch_folder)
        self.data['scratch_folder'] = scratch_folder

        geodatabase_name = f'{self.state}.gdb'
        scratch_geodatabase = os.path.join(scratch_folder, geodatabase_name)
        self.data['scratch_geodatabase'] = scratch_geodatabase
        return scratch_geodatabase
