import os
import arcpy


class FileGeodatabase:
    def __init__(self, configuration):
        self.geodatabase_folder = configuration.data['Outputs']['geodatabase_folder']
        self.database_name = configuration.data['Outputs']['gdb_name']
        self.out_geodatabase = os.path.join(self.geodatabase_folder, f'{self.database_name}.gdb')

    def __del__(self):
        del self.geodatabase_folder
        del self.database_name
        del self.out_geodatabase

    def _create_geodatabase(self) -> None:
        if arcpy.Exists(self.out_geodatabase):
            arcpy.management.Delete(self.out_geodatabase)

        arcpy.management.CreateFileGDB(self.geodatabase_folder, self.database_name)

    def get_file_geodatabase(self):
        return self.out_geodatabase

    def run(self):
        self._create_geodatabase()
