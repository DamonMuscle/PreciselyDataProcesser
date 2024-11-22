import os
import arcpy

from national_sde_data_factory import NationalSDEDataFactory
from national_map_logger import NationalMapLogger
from national_map import constants


class NationalSignpostFactory(NationalSDEDataFactory):
    def __init__(self, sde_connection):
        super().__init__(sde_connection)

    def __del__(self):
        super().__del__()

    def _update_signpost_table_edge_feature_id(self):
        national_signposts_table = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        national_streets = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name']
        sql_statement = (f'UPDATE {national_signposts_table} '
                         f'SET EdgeFID = S.OBJECTID '
                         f'FROM {national_streets} S '
                         f'WHERE SegmentID = S.LocalId;')
        self.execute_sql(sql_statement)

    def _update_signpost_table_feature_class_id(self):
        feature_class_id = self.get_street_feature_class_id()
        national_signposts_table = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        sql_statement = (f'UPDATE {national_signposts_table} '
                         f'SET EdgeFCID = {feature_class_id};')
        self.execute_sql(sql_statement)

    def _add_signpost_table_index(self):
        NationalMapLogger.debug(f'_add_signpost_table_index')
        index_fields = [('SignpostID', 'IDX_SignpostID'),
                        ('Sequence', 'IDX_Sequence'),
                        ('EdgeFCID', 'IDX_EdgeFCID'),
                        ('EdgeFID', 'IDX_EdgeFID')]
        signposts_table_name = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        national_signposts_table = os.path.join(self.sde_connection, signposts_table_name)

        for index_filed in index_fields:
            field_name, index_name = index_filed
            arcpy.management.AddIndex(national_signposts_table, [field_name], index_name)

    def _add_state_and_city(self):
        NationalMapLogger.debug(f'_add_state_and_city')

        sde_dataset = self._get_sde_dataset()
        signpost_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['signpost_name']
        signpost_feature_class = os.path.join(sde_dataset, signpost_name)

        signposts_table_name = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        national_signposts_table = os.path.join(self.sde_connection, signposts_table_name)

        street_feature_class = self._get_street_feature_class()
        arcpy.management.JoinField(
            in_data=national_signposts_table,
            in_field='SegmentID',
            join_table=street_feature_class,
            join_field='LocalId',
            fields='State;City'
        )

        arcpy.management.JoinField(
            in_data=signpost_feature_class,
            in_field='SrcSignID',
            join_table=national_signposts_table,
            join_field='SrcSignID',
            fields='State;City'
        )

    def run(self):
        self._update_signpost_table_edge_feature_id()
        self._update_signpost_table_feature_class_id()
        self._add_state_and_city()
        self._add_signpost_table_index()


