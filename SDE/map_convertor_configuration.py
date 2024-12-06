from typing import Dict, Any
import os
import arcpy
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree

import constants
from national_map_utility import NationalMapUtility

ALL_US_STATES = 'ALL'


class MapConvertorConfiguration:
    data: dict[str, Any]
    tree: ElementTree

    def __init__(self, configuration_file):
        self.tree = ET.parse(configuration_file)
        self.root = self.tree.getroot()
        self.data = {
            'Precisely': {},
            'Logging': {},
            'ArcGIS': {},
            'Outputs': {}
        }
        self.run()

    def __del__(self):
        del self.tree
        del self.root
        del self.data

    def _read_precisely_configuration(self):
        precisely_element = self.root.find('Precisely')
        version_element = precisely_element.find('Version')
        precisely_data_version = version_element.text

        file_gdb_location_element = precisely_element.find('FGDBLocation')
        precisely_gdb_location = file_gdb_location_element.text

        zip_location_element = precisely_element.find('ZipLocation')
        zip_location = zip_location_element.text

        self.data['Precisely'] = {
            'version': precisely_data_version,
            'fgdb_location': precisely_gdb_location,
            'zip_location': zip_location
        }

    def _read_logging_configuration(self):
        logging_element = self.root.find('Logging')

        logging_level_element = logging_element.find('Level')
        log_level = logging_level_element.text.upper()

        self.data['Logging'] = {
            'log_level': log_level
        }

    def _read_arcgis_enterprise_geodatabase_configuration(self):
        arcgis_element = self.root.find('ArcGIS')
        enterprise_gdb_element = arcgis_element.find('EnterpriseGeodatabase')

        authorization_file_element = enterprise_gdb_element.find('AuthorizationFile')
        authorization_file = authorization_file_element.text

        sql_server_instance_element = enterprise_gdb_element.find('SQLServerInstance')
        sql_server_instance = sql_server_instance_element.text

        database_administrator_element = enterprise_gdb_element.find('DatabaseAdministrator')
        database_administrator = database_administrator_element.text

        database_administrator_password_element = enterprise_gdb_element.find('DatabaseAdministratorPassword')
        database_administrator_password = database_administrator_password_element.text

        self.data['ArcGIS']['enterprise_geodatabase'] = {
            'authorization_file': authorization_file,
            'sql_server_instance': sql_server_instance,
            'database_administrator': database_administrator,
            'database_administrator_password': database_administrator_password
        }

    def _read_arcgis_server_configuration(self):
        arcgis_element = self.root.find('ArcGIS')
        server_element = arcgis_element.find('Server')

        administrator_directory_url_element = server_element.find('AdministratorDirectoryURL')
        administrator_directory_url = administrator_directory_url_element.text

        user_name_element = server_element.find('UserName')
        user_name = user_name_element.text

        password_element = server_element.find('Password')
        password = password_element.text

        self.data['ArcGIS']['server'] = {
            'admin_url': administrator_directory_url,
            'user_name': user_name,
            'password': password
        }

    def _read_outputs_configuration(self):
        outputs_element = self.root.find('Outputs')
        workspace_element = outputs_element.find('Workspace')
        workspace = workspace_element.text
        NationalMapUtility.ensure_path_exists(workspace)

        output_folder_element = outputs_element.find('OutputFolder')
        output_folder_name = output_folder_element.text
        output_folder = os.path.join(workspace, output_folder_name)
        NationalMapUtility.ensure_path_exists(output_folder)

        scratch_folder_element = outputs_element.find('ScratchFolder')
        scratch_folder_name = scratch_folder_element.text
        scratch_folder = os.path.join(workspace, scratch_folder_name)
        NationalMapUtility.ensure_path_exists(scratch_folder)

        format_element = outputs_element.find('Format')
        out_format = format_element.text.upper()

        log_folder = os.path.join(output_folder, 'Log')
        NationalMapUtility.ensure_path_exists(log_folder)

        locator_folder = os.path.join(output_folder, 'Locator')
        NationalMapUtility.ensure_path_exists(locator_folder)

        geodatabase_folder = os.path.join(output_folder, 'Geodatabase')
        NationalMapUtility.ensure_path_exists(geodatabase_folder)

        mobile_geodatabase_folder = os.path.join(output_folder, 'MobileGeodatabase')
        NationalMapUtility.ensure_path_exists(mobile_geodatabase_folder)

        locator_name_element = outputs_element.find('LocatorName')
        locator_name = locator_name_element.text

        gdb_name_element = outputs_element.find('GDBName')
        gdb_name = gdb_name_element.text

        enterprise_geodatabase_connection_element = outputs_element.find('EnterpriseGeodatabaseConnection')
        enterprise_geodatabase_connection = enterprise_geodatabase_connection_element.text

        log_file_name_element = outputs_element.find('LogFileName')
        log_file_name = log_file_name_element.text

        us_states_element = outputs_element.find('USStates')
        us_states_value = us_states_element.text.upper()
        us_states = constants.US_STATES if us_states_value == ALL_US_STATES else us_states_value.split(';')

        dissolve_network_file_geodatabase_name_element = outputs_element.find('DissolvedNetworkFileGDBName')
        dissolve_network_file_geodatabase_name = dissolve_network_file_geodatabase_name_element.text

        arcgis_server_connection_element = outputs_element.find('ArcGISServerConnection')
        arcgis_server_connection_name = arcgis_server_connection_element.text

        self.data['Outputs'] = {
            'format': out_format,
            'gdb_name': gdb_name,
            'states': us_states,
            'scratch_folder': scratch_folder,
            'geodatabase_folder': geodatabase_folder,
            'mobile_geodatabase_folder': mobile_geodatabase_folder,
            'locator_folder': locator_folder,
            'locator': os.path.join(locator_folder, locator_name),
            'log_folder': log_folder,
            'log': os.path.join(log_folder, log_file_name),
            'dissolve_network_file_geodatabase_name': dissolve_network_file_geodatabase_name,
            'enterprise_geodatabase_connection': enterprise_geodatabase_connection,
            'arcgis_server_connection_name': arcgis_server_connection_name
        }

    @staticmethod
    def set_arcpy_environment():
        arcpy.env.maintainSpatialIndex = True
        arcpy.env.outputMFlag = 'Disabled'
        arcpy.env.outputZFlag = 'Disabled'
        arcpy.env.overwriteOutput = True
        arcpy.env.processorType = 'CPU'
        arcpy.env.parallelProcessingFactor = '80%'
        if arcpy.GetLogHistory():
            arcpy.SetLogHistory(False)

        if arcpy.GetLogMetadata():
            arcpy.SetLogMetadata(False)

    def run(self):
        self._read_precisely_configuration()
        self._read_logging_configuration()
        self._read_arcgis_enterprise_geodatabase_configuration()
        self._read_arcgis_server_configuration()
        self._read_outputs_configuration()


