import os.path

import arcpy

from national_sde_data_factory import NationalSDEDataFactory
from national_map_utility import NationalMapUtility
from national_map import constants

MAX_TURN_EDGES = 5

EDGE_POSITION = 0.5
PROHIBITED_TURN_FLAG = 1
RESTRICTED_TURN_FLAG = 0


def get_turn_feature_template(restriction_id):
    union_geometry, edge_end = None, None
    feature = [union_geometry, edge_end]

    for i in range(MAX_TURN_EDGES):
        feature.extend([None, None, None])

    feature.extend([restriction_id, PROHIBITED_TURN_FLAG, RESTRICTED_TURN_FLAG])
    return feature


def add_turn_fields(turn_feature_class):
    NationalMapUtility.add_field(turn_feature_class, 'RestrictionID', 'TEXT', 36)
    NationalMapUtility.add_field(turn_feature_class, 'ProhibitedTurnFlag', 'SHORT')
    NationalMapUtility.add_field(turn_feature_class, 'RestrictedTurnFlag', 'SHORT')


class NationalRestrictionTurnFactory(NationalSDEDataFactory):
    """
    Generate national map turn features from restriction features.
    """

    def __init__(self, sde_connection):
        super().__init__(sde_connection)
        self.turn_feature_class = None

    def __del__(self):
        super().__del__()
        del self.turn_feature_class

    def _get_restriction_feature_class(self):
        restriction_name = constants.GDB_ITEMS_DICT['NATIONAL']['restriction_name']
        return os.path.join(self.sde_connection, restriction_name)

    def _get_turn_feature_class(self):
        sde_dataset = self._get_sde_dataset()
        turn_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['turn_name']
        return os.path.join(sde_dataset, turn_name)

    def _create_turn_feature_class(self):
        turn_feature_class = self._get_turn_feature_class()
        if arcpy.Exists(turn_feature_class):
            arcpy.management.Delete(turn_feature_class)

        sde_dataset = self._get_sde_dataset()
        turn_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['turn_name']
        self.turn_feature_class = arcpy.na.CreateTurnFeatureClass(sde_dataset, turn_name, MAX_TURN_EDGES)
        add_turn_fields(self.turn_feature_class)

    def _create_turn_features(self):
        turn_features = self._generate_turn_features()
        print(f'_create_turn_features: count - {len(turn_features)}')

        fields = ['SHAPE@', 'Edge1End']
        for i in range(MAX_TURN_EDGES):
            fields.extend([f'Edge{i + 1}FCID', f'Edge{i + 1}FID', f'Edge{i + 1}Pos'])
        fields.extend(['RestrictionID', 'ProhibitedTurnFlag', 'RestrictedTurnFlag'])

        with arcpy.da.InsertCursor(self.turn_feature_class, fields) as cursor:
            for feature in turn_features:
                cursor.insertRow(feature)

    def _generate_turn_features(self):
        turn_features = []
        restriction_groups = self._generate_restriction_groups()
        print(f'_generate_turn_features, restriction_groups count: {len(restriction_groups)}')

        for group in restriction_groups:
            restriction_id = list(group.keys())[0]
            restriction_items = group[restriction_id]
            feature = self._generate_prohibited_turn(restriction_id, restriction_items)
            if feature is not None:
                turn_features.append(feature)

        return turn_features

    def _generate_restriction_groups(self):
        restriction_feature_class = self._get_restriction_feature_class()
        fields = ['RESTRICTION_ID', 'SEQUENCE_NUM', 'FEATURE_ID', 'SHAPE@']
        sql_clause = (None, 'ORDER BY RESTRICTION_ID, SEQUENCE_NUM')
        groups = []

        with arcpy.da.SearchCursor(restriction_feature_class, fields, sql_clause=sql_clause) as cursor:
            key, group = None, []

            for row in cursor:
                restriction_id, sequence_num, feature_id, geometry = row[0], row[1], row[2], row[3]
                item = (sequence_num, feature_id, geometry)

                if key is None or key == restriction_id:
                    key = restriction_id
                    group.append(item)
                else:
                    if len(group) <= MAX_TURN_EDGES:
                        groups.append({
                            key: group
                        })
                    key, group = restriction_id, [item]

        return groups

    def _generate_prohibited_turn(self, restriction_id, restriction_items):
        feature = get_turn_feature_template(restriction_id)

        feature_class_id = self.get_street_feature_class_id()

        union_geometry, edge_end = None, None
        first_geometry, second_geometry = None, None

        for index, items in enumerate(restriction_items):
            (sequence_num, feature_id, geometry) = items

            start_index = 2 + (sequence_num - 1) * 3
            feature[start_index] = feature_class_id
            feature[start_index + 1] = self._get_street_object_id(feature_id)
            feature[start_index + 2] = EDGE_POSITION

            if index == 0:
                union_geometry = geometry
            else:
                union_geometry = union_geometry | geometry

            if index == 0:
                first_geometry = geometry
            elif index == 1:
                second_geometry = geometry

        if second_geometry is None:
            # dirty data
            return None

        edge_end = NationalMapUtility.get_edge_end(first_geometry, second_geometry)
        feature[0] = union_geometry
        feature[1] = edge_end

        return feature

    def _add_state_and_city(self):
        in_data = self._get_turn_feature_class()
        restriction_feature_class = self._get_restriction_feature_class()
        arcpy.management.JoinField(
            in_data=in_data,
            in_field='RestrictionID',
            join_table=restriction_feature_class,
            join_field='RESTRICTION_ID',
            fields='State;City'
        )

    def run(self):
        self._create_turn_feature_class()
        self._create_turn_features()
        self._add_state_and_city()
