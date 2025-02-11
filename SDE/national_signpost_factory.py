import os
import arcpy

from national_gdb_data_factory import NationalGDBDataFactory
from national_map_logger import NationalMapLogger
import constants


@NationalMapLogger.debug_decorator
def _update_signpost_feature_class_id_in_file_gdb(national_signposts_table, feature_class_id):
    field_names = ['EdgeFCID']
    with arcpy.da.UpdateCursor(national_signposts_table, field_names) as cursor:
        for row in cursor:
            row[0] = feature_class_id
            cursor.updateRow(row)


class NationalSignpostFactory(NationalGDBDataFactory):
    def __init__(self, configuration, workspace):
        super().__init__(workspace)
        output_configuration = configuration.data['Outputs']
        self.output_format = output_configuration['format']
        self.signpost_feature_class = None

    def __del__(self):
        super().__del__()
        del self.output_format
        del self.signpost_feature_class

    @NationalMapLogger.debug_decorator
    def _update_signpost_table_edge_feature_id(self):
        national_signposts_table = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        if self.output_format == constants.OUT_FORMAT['SDE']:
            national_streets = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name']
            self._update_signpost_edge_feature_id_in_sde(national_signposts_table, national_streets)
        elif self.output_format == constants.OUT_FORMAT['FILE_GDB']:
            national_signposts_table_path = os.path.join(self.workspace, national_signposts_table)
            self._update_signpost_edge_feature_id_in_file_gdb(national_signposts_table_path)

    def _update_signpost_edge_feature_id_in_sde(self, national_signposts_table, national_streets):
        sql_statement = (f'UPDATE {national_signposts_table} '
                         f'SET EdgeFID = S.OBJECTID '
                         f'FROM {national_streets} S '
                         f'WHERE SegmentID = S.LocalId;')
        self.execute_sql(sql_statement)

    @NationalMapLogger.debug_decorator
    def _update_signpost_edge_feature_id_in_file_gdb(self, national_signposts_table):
        signposts_field_names = ['SegmentID', 'EdgeFID']
        with arcpy.da.UpdateCursor(national_signposts_table, signposts_field_names) as cursor:
            for row in cursor:
                segment_id = row[0]
                row[1] = self._get_street_object_id(segment_id)
                cursor.updateRow(row)

    @NationalMapLogger.debug_decorator
    def _update_signpost_table_feature_class_id(self):
        feature_class_id = self.get_street_feature_class_id()
        national_signposts_table = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        if self.output_format == constants.OUT_FORMAT['SDE']:
            self._update_signpost_feature_class_id_in_sde(national_signposts_table, feature_class_id)
        elif self.output_format == constants.OUT_FORMAT['FILE_GDB']:
            national_signposts_table_path = os.path.join(self.workspace, national_signposts_table)
            _update_signpost_feature_class_id_in_file_gdb(national_signposts_table_path, feature_class_id)

    def _update_signpost_feature_class_id_in_sde(self, national_signposts_table, feature_class_id):
        sql_statement = (f'UPDATE {national_signposts_table} '
                         f'SET EdgeFCID = {feature_class_id};')
        self.execute_sql(sql_statement)

    @NationalMapLogger.debug_decorator
    def _add_signpost_table_index(self):
        index_fields = [('SignpostID', 'IDX_SignpostID'),
                        ('Sequence', 'IDX_Sequence'),
                        ('EdgeFCID', 'IDX_EdgeFCID'),
                        ('EdgeFID', 'IDX_EdgeFID')]
        signposts_table_name = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        national_signposts_table = os.path.join(self.workspace, signposts_table_name)

        for index_filed in index_fields:
            field_name, index_name = index_filed
            arcpy.management.AddIndex(national_signposts_table, [field_name], index_name)

    @NationalMapLogger.debug_decorator
    def _add_state_and_city(self):
        sde_dataset = self._get_dataset()
        signpost_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['signpost_name']
        self.signpost_feature_class = os.path.join(sde_dataset, signpost_name)

        signposts_table_name = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        national_signposts_table = os.path.join(self.workspace, signposts_table_name)

        street_feature_class = self._get_street_feature_class()
        arcpy.management.JoinField(
            in_data=national_signposts_table,
            in_field='SegmentID',
            join_table=street_feature_class,
            join_field='LocalId',
            fields='State;City'
        )

        arcpy.management.JoinField(
            in_data=self.signpost_feature_class,
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
