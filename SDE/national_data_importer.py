import os.path
import arcpy

from national_map_logger import NationalMapLogger
from national_map_utility import NationalMapUtility
from national_map import constants


def _get_out_sde_feature_class(sde_connection, key):
    out_feature_class = None
    national_features = constants.GDB_ITEMS_DICT['NATIONAL']
    national_dataset = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']
    if key in national_features:
        out_name = national_features[key]
        out_feature_class = os.path.join(sde_connection, out_name)
    elif key in national_dataset:
        dataset_name = national_dataset['name']
        out_name = national_dataset[key]
        out_feature_class = os.path.join(sde_connection, dataset_name, out_name)
    return out_feature_class


def _convert_feature_class_to_sde(feature_class_or_table, out_feature_class_or_table):
    if arcpy.Exists(out_feature_class_or_table):
        arcpy.management.Append(feature_class_or_table, out_feature_class_or_table, schema_type='TEST')
    else:
        if NationalMapUtility.is_feature_class(feature_class_or_table):
            arcpy.management.CopyFeatures(feature_class_or_table, out_feature_class_or_table)
        else:
            arcpy.management.CopyRows(feature_class_or_table, out_feature_class_or_table)


class NationalDataImporter:
    """
    Import US national map data into Enterprise Geodatabase (SDE)
    """

    def __init__(self, configuration, sde_connection):
        self.states = configuration.data['Outputs']['states']
        self.scratch_gdb_location = configuration.data['Outputs']['scratch_folder']
        self.sde_connection = sde_connection

    def __del__(self):
        del self.states
        del self.scratch_gdb_location
        del self.sde_connection

    def _create_dataset(self):
        dataset_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['name']
        sde_dataset = os.path.join(self.sde_connection, dataset_name)

        if arcpy.Exists(sde_dataset):
            return

        arcpy.management.CreateFeatureDataset(self.sde_connection, dataset_name, constants.SR_WEB_MERCATOR)

    def _convert_to_sde(self):
        for state in self.states:
            gdb_name = f'{state.lower()}.gdb'
            gdb_file = os.path.join(self.scratch_gdb_location, gdb_name)
            self._convert_gdb_to_sde(gdb_file)

    def _convert_gdb_to_sde(self, gdb_file):
        message = f'_convert_gdb_to_sde {gdb_file}'
        NationalMapLogger.debug(message)

        for key, name in constants.GDB_ITEMS_DICT['STATE'].items():
            feature_class = os.path.join(gdb_file, name)
            out_feature_class = _get_out_sde_feature_class(self.sde_connection, key)
            if out_feature_class:
                _convert_feature_class_to_sde(feature_class, out_feature_class)

    def _add_attribute_index(self):
        street_feature_class = _get_out_sde_feature_class(self.sde_connection, 'street_name')
        if arcpy.Exists(street_feature_class):
            arcpy.management.AddIndex(
                in_table=street_feature_class,
                fields='State;City',
                index_name='idx_state_city'
            )

    def _generate_t_junctions(self):
        NationalMapLogger.debug(f'_generate_t_junctions')
        street_nodes_feature_class = _get_out_sde_feature_class(self.sde_connection, 'node_name')
        street_feature_class = _get_out_sde_feature_class(self.sde_connection, 'street_name')
        memory_layer = constants.TEMP_MEMORY_LAYER
        if arcpy.Exists(memory_layer):
            arcpy.management.Delete(memory_layer)

        field_mapping = (f'ELEVATION "ELEVATION" true true false 4 Long 0 0,First,#,'
                         f'{street_nodes_feature_class},ELEVATION,-1,-1')
        arcpy.analysis.SpatialJoin(
            target_features=street_nodes_feature_class,
            join_features=street_feature_class,
            out_feature_class=memory_layer,
            join_operation='JOIN_ONE_TO_ONE',
            join_type='KEEP_ALL',
            field_mapping=field_mapping,
            match_option='INTERSECT'
        )

        junctions_feature_class = _get_out_sde_feature_class(self.sde_connection, 't_junction_name')
        where_clause = 'Join_Count = 3'
        field_mapping = (f'ELEVATION "ZELEV" true true false 4 Long 0 0,First,#,'
                         f"'{memory_layer}',ELEVATION,-1,-1;")
        arcpy.conversion.ExportFeatures(
            in_features=memory_layer,
            out_features=junctions_feature_class,
            where_clause=where_clause,
            use_field_alias_as_name='NOT_USE_ALIAS',
            field_mapping=field_mapping
        )

        arcpy.management.Delete(memory_layer)

    def _generate_street_intersect(self):
        NationalMapLogger.debug(f'_generate_street_intersect')
        street_feature_class = _get_out_sde_feature_class(self.sde_connection, 'street_name')
        railroad_feature_class = _get_out_sde_feature_class(self.sde_connection, 'railroad_name')
        input_features = [street_feature_class, railroad_feature_class]
        memory_layer = constants.TEMP_MEMORY_LAYER
        if arcpy.Exists(memory_layer):
            arcpy.management.Delete(memory_layer)

        arcpy.analysis.Intersect(input_features, memory_layer, output_type='POINT')
        out_intersect = _get_out_sde_feature_class(self.sde_connection, 'street_railroad_intersect_name')
        where_clause = (f'FromElevation = ToElevation AND FromElevation_1 = ToElevation_1 AND '
                        f'FromElevation_1 = FromElevation AND ToElevation = ToElevation_1')
        arcpy.conversion.ExportFeatures(
            in_features=memory_layer,
            out_features=out_intersect,
            where_clause=where_clause,
            use_field_alias_as_name='NOT_USE_ALIAS'
        )

        arcpy.management.Delete(memory_layer)

    def _generate_street_polygon(self):
        NationalMapLogger.debug(f'_generate_street_polygon')
        street_feature_class = _get_out_sde_feature_class(self.sde_connection, 'street_name')
        out_street_polygon_feature_class = _get_out_sde_feature_class(self.sde_connection, 'street_polygon_name')
        arcpy.management.FeatureToPolygon(street_feature_class, out_street_polygon_feature_class)

    def run(self):
        self._create_dataset()
        self._convert_to_sde()
        self._add_attribute_index()
        self._generate_t_junctions()
        self._generate_street_intersect()
        self._generate_street_polygon()

