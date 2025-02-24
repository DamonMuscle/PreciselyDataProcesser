import os.path

import arcpy

import constants


def create_street_local_id_and_oid_lookup(street_feature_class):
    return {
        (item[0]): item[1]
        for item in arcpy.da.SearchCursor(street_feature_class, ['LocalId', 'OID@'])
    }


class NationalGDBDataFactory:

    def __init__(self, configuration, workspace):
        self.configuration = configuration
        self.workspace = workspace
        self.street_local_id_oid_lookup = None
        self._init_street_lookup()

    def __del__(self):
        del self.configuration
        del self.workspace
        del self.street_local_id_oid_lookup

    def _get_dataset(self):
        dataset_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['name']
        return os.path.join(self.workspace, dataset_name)

    def _get_street_feature_class(self):
        dataset = self._get_dataset()
        street_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name']
        feature_class = os.path.join(dataset, street_name)
        return feature_class

    def get_street_feature_class_id(self):
        describe_id = None
        feature_class = self._get_street_feature_class()
        if arcpy.Exists(feature_class):
            describe_id = arcpy.Describe(feature_class).DSID
        return describe_id

    def _init_street_lookup(self):
        if self.street_local_id_oid_lookup:
            return

        street_feature_class = self._get_street_feature_class()
        self.street_local_id_oid_lookup = create_street_local_id_and_oid_lookup(street_feature_class)

    def _get_street_object_id(self, local_id):
        try:
            return self.street_local_id_oid_lookup[local_id]
        except Exception as e:
            return None

    def _get_enterprise_database_connection(self):
        sql_connection = arcpy.ArcSDESQLExecute(self.workspace)
        return sql_connection

    def execute_sql(self, sql_statement):
        try:
            sql_connection = self._get_enterprise_database_connection()
            sql_connection.execute(sql_statement)
        except Exception as e:
            print(e)
