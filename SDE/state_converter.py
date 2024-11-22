import arcpy
from national_map import constants


class StateConverter:
    def __init__(self, data_settings, state_exporter, data=None):
        if data is None:
            data = {}

        self.state = data_settings.state
        self.settings = data_settings.data
        self.exporter = state_exporter
        self.data = data

    def __del__(self):
        del self.state
        del self.settings
        del self.exporter
        del self.data

    def create_memory_layer(self):
        self.dispose_memory_layer()
        return f'{constants.TEMP_MEMORY_LAYER}_{self.state}'

    def dispose_memory_layer(self):
        memory_layer = f'{constants.TEMP_MEMORY_LAYER}_{self.state}'
        if arcpy.Exists(memory_layer):
            arcpy.management.Delete(memory_layer)
