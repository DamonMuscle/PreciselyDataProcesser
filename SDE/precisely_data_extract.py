import os
import shutil
import arcpy
from zipfile import ZipFile

from arcgis.features.feature import arcpy

from national_map_utility import NationalMapUtility


def get_file_gdb(root_path: str) -> list:
    file_gdb_list = []
    gdb_suffix_dot = '.gdb'
    for (root, folder, files) in os.walk(root_path):
        if files:
            # not empty
            continue

        for name in folder:
            if name.endswith(gdb_suffix_dot):
                file_gdb = os.path.join(root, name)
                file_gdb_list.append(file_gdb)

    return file_gdb_list


def extract_file_gdb(root_folder, target_folder):
    file_gdb_list = get_file_gdb(root_folder)
    for gdb in file_gdb_list:
        gdb_file_name = os.path.basename(gdb)
        target_gdb = os.path.join(target_folder, gdb_file_name)
        if arcpy.Exists(target_gdb):
            arcpy.management.Delete(target_gdb)

        shutil.move(gdb, target_folder)
    del file_gdb_list


class PreciselyDataExtract:
    def __init__(self, state: str, configuration):
        self.state = state
        self.settings = configuration.data['Precisely']
        self.zip_location = self.settings['zip_location']
        self.fgdb_location = self.settings['fgdb_location']

    def __del__(self):
        del self.state
        del self.settings
        del self.zip_location
        del self.fgdb_location

    def _get_zip_file(self):
        version = self.settings['version']
        file_name = f'USA_{self.state.upper()}_NAVPREM_{version}_FGDB.zip'
        return os.path.join(self.zip_location, file_name)

    def _extract_zip(self, src_zip_file: str):
        # print(f'Extract {src_zip_file}')
        dist_gdb_folder = self.fgdb_location
        NationalMapUtility.ensure_path_exists(dist_gdb_folder)

        tmp_folder = os.path.join(dist_gdb_folder, 'temp')
        NationalMapUtility.ensure_path_exists(tmp_folder)

        with ZipFile(src_zip_file, mode='r') as archive:
            file_name = os.path.splitext(os.path.basename(archive.filename))[0]
            dist_folder = os.path.join(tmp_folder, file_name)
            NationalMapUtility.ensure_path_exists(dist_folder)
            archive.extractall(dist_folder)
        del archive

        extract_file_gdb(tmp_folder, dist_gdb_folder)
        shutil.rmtree(tmp_folder, ignore_errors=True)

    def run(self):
        src_zip_file = self._get_zip_file()
        self._extract_zip(src_zip_file)
