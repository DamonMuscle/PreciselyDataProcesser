import os
import arcpy

from national_map_utility import NationalMapUtility


class EnterpriseGeodatabase:
    def __init__(self, configuration):
        self.settings = configuration.data['ArcGIS']['enterprise_geodatabase']
        self.geodatabase_folder = configuration.data['Outputs']['geodatabase_folder']
        self.enterprise_geodatabase_connection = configuration.data['Outputs']['enterprise_geodatabase_connection']
        self.database_name = configuration.data['Outputs']['gdb_name']

    def __del__(self):
        # print('call EnterpriseGeodatabase __del__')
        del self.settings
        del self.geodatabase_folder
        del self.enterprise_geodatabase_connection
        del self.database_name

    def _create_geodatabase(self) -> None:
        instance_name = self.settings['sql_server_instance']
        database_admin = self.settings['database_administrator']
        database_admin_password = self.settings['database_administrator_password']
        authorization_file = self.settings['authorization_file']
        arcpy.management.CreateEnterpriseGeodatabase(
            database_platform='SQL_Server',
            instance_name=instance_name,
            database_name=self.database_name,
            database_admin=database_admin,
            database_admin_password=database_admin_password,
            sde_schema='DBO_SCHEMA',
            authorization_file=authorization_file
        )

    def _create_database_connection(self) -> None:
        NationalMapUtility.ensure_path_exists(self.geodatabase_folder)

        sde_connection_file = self.get_sde_connection()
        if arcpy.Exists(sde_connection_file):
            print('connection_file exists')
            return

        instance_name = self.settings['sql_server_instance']
        database_admin = self.settings['database_administrator']
        database_admin_password = self.settings['database_administrator_password']
        arcpy.management.CreateDatabaseConnection(
            out_folder_path=self.geodatabase_folder,
            out_name=self.enterprise_geodatabase_connection,
            database_platform='SQL_SERVER',
            instance=instance_name,
            account_authentication='DATABASE_AUTH',
            username=database_admin,
            password=database_admin_password,
            database=self.database_name
        )

    def get_sde_connection(self):
        return os.path.join(self.geodatabase_folder, f'{self.enterprise_geodatabase_connection}.sde')

    def run(self):
        self._create_geodatabase()
        self._create_database_connection()
