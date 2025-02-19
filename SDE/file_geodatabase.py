import arcpy


class FileGeodatabase:
    def __init__(self, configuration):
        self.configuration = configuration

    def __del__(self):
        del self.configuration

    def _create_geodatabase(self) -> None:
        out_geodatabase = self.configuration.get_file_geodatabase()
        if arcpy.Exists(out_geodatabase):
            arcpy.management.Delete(out_geodatabase)

        arcpy.management.CreateFileGDB(self.configuration.get_geodatabase_folder(),
                                       self.configuration.get_geodatabase_name())

    def run(self):
        self._create_geodatabase()
