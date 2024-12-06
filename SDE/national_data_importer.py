import os.path
import arcpy

from national_map_logger import NationalMapLogger
from national_map_utility import NationalMapUtility
import constants


def _get_out_target_feature_class(target_workspace, key):
    out_feature_class = None
    national_features = constants.GDB_ITEMS_DICT['NATIONAL']
    national_dataset = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']
    if key in national_features:
        out_name = national_features[key]
        out_feature_class = os.path.join(target_workspace, out_name)
    elif key in national_dataset:
        dataset_name = national_dataset['name']
        out_name = national_dataset[key]
        out_feature_class = os.path.join(target_workspace, dataset_name, out_name)
    return out_feature_class


def _convert_feature_class_to_sde(feature_class_or_table, out_feature_class_or_table):
    is_feature_class = NationalMapUtility.is_feature_class(feature_class_or_table)
    is_out_exists = arcpy.Exists(out_feature_class_or_table)

    if is_out_exists:
        if is_feature_class:
            _append_features_with_cursor(feature_class_or_table, out_feature_class_or_table)
        else:
            _append_rows_with_cursor(feature_class_or_table, out_feature_class_or_table)
    else:
        if is_feature_class:
            arcpy.management.CopyFeatures(feature_class_or_table, out_feature_class_or_table)
        else:
            arcpy.management.CopyRows(feature_class_or_table, out_feature_class_or_table)


def _append_features_with_cursor(source_feature_class, target_feature_class):
    source_describe = arcpy.Describe(source_feature_class)
    source_fields = source_describe.fields
    exclude_fields = ['OBJECTID', 'Shape', 'Shape_Length', 'Shape_Area']
    field_names = [field.name for field in source_fields if field not in exclude_fields]
    field_names.append('SHAPE@')

    memory_layer = constants.TEMP_MEMORY_LAYER
    if arcpy.Exists(memory_layer):
        arcpy.management.Delete(memory_layer)
    arcpy.management.MakeFeatureLayer(source_feature_class, memory_layer)

    with arcpy.da.SearchCursor(memory_layer, field_names) as search_cursor:
        with arcpy.da.InsertCursor(target_feature_class, field_names) as insert_cursor:
            for row in search_cursor:
                insert_cursor.insertRow(row)

    arcpy.management.Delete(memory_layer)
    del memory_layer
    arcpy.management.Delete("memory")


def _append_rows_with_cursor(source_table, target_table):
    source_describe = arcpy.Describe(source_table)
    source_fields = source_describe.fields
    field_names = [field.name for field in source_fields]

    with arcpy.da.SearchCursor(source_table, field_names) as search_cursor:
        with arcpy.da.InsertCursor(target_table, field_names) as insert_cursor:
            for row in search_cursor:
                insert_cursor.insertRow(row)


class NationalDataImporter:
    """
    Import US national map data into Enterprise Geodatabase (SDE)
    """

    def __init__(self, configuration, out_workspace):
        self.states = configuration.data['Outputs']['states']
        self.scratch_gdb_location = configuration.data['Outputs']['scratch_folder']
        self.target_workspace = out_workspace

    def __del__(self):
        del self.states
        del self.scratch_gdb_location
        del self.target_workspace

    def _create_dataset(self):
        dataset_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['name']
        target_dataset = os.path.join(self.target_workspace, dataset_name)

        if arcpy.Exists(target_dataset):
            return

        arcpy.management.CreateFeatureDataset(self.target_workspace, dataset_name, constants.SR_WEB_MERCATOR)

    def _convert_to_target_workspace(self):
        for state in self.states:
            gdb_name = f'{state.lower()}.gdb'
            gdb_file = os.path.join(self.scratch_gdb_location, gdb_name)
            self._convert_gdb_to_target_workspace(gdb_file)

    def _convert_gdb_to_target_workspace(self, gdb_file):
        message = f'_convert_gdb_to_target_workspace {gdb_file}'
        NationalMapLogger.debug(message)

        for key, name in constants.GDB_ITEMS_DICT['STATE'].items():
            feature_class = os.path.join(gdb_file, name)
            out_feature_class = _get_out_target_feature_class(self.target_workspace, key)
            if out_feature_class:
                _convert_feature_class_to_sde(feature_class, out_feature_class)

    def _add_attribute_index(self):
        street_feature_class = _get_out_target_feature_class(self.target_workspace, 'street_name')
        if arcpy.Exists(street_feature_class):
            NationalMapLogger.debug(f'_add_attribute_index: idx_state_city')
            arcpy.management.AddIndex(
                in_table=street_feature_class,
                fields='State;City',
                index_name='idx_state_city'
            )

    def _generate_t_junctions(self):
        NationalMapLogger.debug(f'_generate_t_junctions')
        street_nodes_feature_class = _get_out_target_feature_class(self.target_workspace, 'node_name')
        street_feature_class = _get_out_target_feature_class(self.target_workspace, 'street_name')
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

        junctions_feature_class = _get_out_target_feature_class(self.target_workspace, 't_junction_name')
        where_clause = 'Join_Count = 3'
        field_mapping = (f'ELEVATION "ZELEV" true true false 4 Long 0 0,First,#,'
                         f"'{memory_layer}',ELEVATION,-1,-1;")

        NationalMapLogger.debug(f'export {junctions_feature_class}')
        arcpy.conversion.ExportFeatures(
            in_features=memory_layer,
            out_features=junctions_feature_class,
            where_clause=where_clause,
            use_field_alias_as_name='NOT_USE_ALIAS',
            field_mapping=field_mapping
        )

        arcpy.management.Delete(memory_layer)
        del memory_layer
        arcpy.management.Delete("memory")

    def _generate_street_intersect(self):
        NationalMapLogger.debug(f'_generate_street_intersect')
        street_feature_class = _get_out_target_feature_class(self.target_workspace, 'street_name')
        railroad_feature_class = _get_out_target_feature_class(self.target_workspace, 'railroad_name')
        input_features = [street_feature_class, railroad_feature_class]
        memory_layer = constants.TEMP_MEMORY_LAYER
        if arcpy.Exists(memory_layer):
            arcpy.management.Delete(memory_layer)

        arcpy.analysis.PairwiseIntersect(input_features, memory_layer, output_type='POINT')
        out_intersect = _get_out_target_feature_class(self.target_workspace, 'street_railroad_intersect_name')

        NationalMapLogger.debug(f'export {out_intersect}')
        where_clause = (f'FromElevation = ToElevation AND FromElevation_1 = ToElevation_1 AND '
                        f'FromElevation_1 = FromElevation AND ToElevation = ToElevation_1')
        arcpy.conversion.ExportFeatures(
            in_features=memory_layer,
            out_features=out_intersect,
            where_clause=where_clause,
            use_field_alias_as_name='NOT_USE_ALIAS'
        )

        arcpy.management.Delete(memory_layer)
        del memory_layer
        arcpy.management.Delete("memory")

    def _generate_street_polygon(self):
        NationalMapLogger.debug(f'_generate_street_polygon')
        street_feature_class = _get_out_target_feature_class(self.target_workspace, 'street_name')
        out_street_polygon_feature_class = _get_out_target_feature_class(self.target_workspace, 'street_polygon_name')
        arcpy.management.FeatureToPolygon(street_feature_class, out_street_polygon_feature_class)

    def run(self):
        self._create_dataset()
        self._convert_to_target_workspace()
        self._add_attribute_index()
        self._generate_t_junctions()
        self._generate_street_intersect()
        self._generate_street_polygon()
