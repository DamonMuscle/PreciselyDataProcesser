import os
import arcpy

import constants
from national_gdb_data_factory import NationalGDBDataFactory
from national_map_utility import NationalMapUtility
from national_map_logger import NationalMapLogger

REFERENCE_LANDMARKS_IMPORTANCE = 100
REFERENCE_LANDMARKS_SIDE = 0  # Both
REFERENCE_LANDMARKS_GUIDANCE_TYPE = 4  # Railroad Crossing
START_LANDMARKS_ID = 1
HOTFIX_OFFSET = 0.00001


def add_reference_landmarks_fields(reference_landmarks_table):
    NationalMapUtility.add_field(reference_landmarks_table, 'LandmarkID', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'GuidanceType', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge1FCID', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge1FID', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge1FrmPos', 'DOUBLE')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge1ToPos', 'DOUBLE')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge1ConfirmationPos', 'DOUBLE')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge2FCID', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge2FID', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge2FrmPos', 'DOUBLE')
    NationalMapUtility.add_field(reference_landmarks_table, 'Edge2ToPos', 'DOUBLE')
    NationalMapUtility.add_field(reference_landmarks_table, 'Importance', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Side', 'LONG')
    NationalMapUtility.add_field(reference_landmarks_table, 'Name', 'TEXT', 255)
    NationalMapUtility.add_field(reference_landmarks_table, 'NameLng', 'TEXT', 255)
    NationalMapUtility.add_field(reference_landmarks_table, 'Phrase', 'TEXT', 255)


@NationalMapLogger.debug_decorator
def create_street_oid_and_shape_lookup(street_feature_class):
    return {
        (item[0]): item[1]
        for item in arcpy.da.SearchCursor(street_feature_class, ['OID@', 'SHAPE@'])
    }


def _calculate_from_to_position(position):
    from_position, to_position = 0, 1
    if position == 0:
        to_position = position + HOTFIX_OFFSET
    elif position == 1:
        from_position = position - HOTFIX_OFFSET
    else:
        from_position = position - HOTFIX_OFFSET
        to_position = position + HOTFIX_OFFSET

    return from_position, to_position


class NationalLandmarksFactory(NationalGDBDataFactory):
    def __init__(self, configuration, workspace):
        super().__init__(configuration, workspace)
        street_railroad_intersect_name = constants.GDB_ITEMS_DICT['NATIONAL']['street_railroad_intersect_name']
        self.street_railroad_intersect_feature_class = os.path.join(self.workspace, street_railroad_intersect_name)
        self.street_feature_class_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name']
        self.street_feature_class = os.path.join(self.workspace, self.street_feature_class_name)
        self.street_oid_shape_lookup = create_street_oid_and_shape_lookup(self.street_feature_class)
        self.reference_landmarks_table = None

    def __del__(self):
        del self.street_railroad_intersect_feature_class
        del self.street_feature_class_name
        del self.street_feature_class
        del self.street_oid_shape_lookup
        del self.reference_landmarks_table

    @NationalMapLogger.debug_decorator
    def _create_reference_landmarks_table(self):
        reference_landmarks_table_name = constants.GDB_ITEMS_DICT['NATIONAL']['reference_landmarks_table_name']
        reference_landmarks_table = arcpy.management.CreateTable(self.workspace, reference_landmarks_table_name)

        add_reference_landmarks_fields(reference_landmarks_table)
        self.reference_landmarks_table = reference_landmarks_table

    @NationalMapLogger.debug_decorator
    def _generate_reference_landmarks_records(self):
        street_feature_class_id = self.get_street_feature_class_id()
        search_fields = [f'FID_{self.street_feature_class_name}', 'SHAPE@']
        insert_fields = ['LandmarkID', 'GuidanceType', 'Edge1FCID',
                         'Edge1FID', 'Edge1FrmPos', 'Edge1ToPos', 'Edge1ConfirmationPos', 'Importance', 'Side']

        landmark_id = START_LANDMARKS_ID

        with arcpy.da.SearchCursor(self.street_railroad_intersect_feature_class, search_fields) as search_cursor:
            with arcpy.da.InsertCursor(self.reference_landmarks_table, insert_fields) as insert_cursor:
                for intersect_feature in search_cursor:
                    street_oid = intersect_feature[0]
                    position = self._calculate_intersect_point_position(intersect_feature)
                    from_position, to_position = _calculate_from_to_position(position)
                    row = [landmark_id, REFERENCE_LANDMARKS_GUIDANCE_TYPE, street_feature_class_id,
                           street_oid, from_position, to_position, position,
                           REFERENCE_LANDMARKS_IMPORTANCE, REFERENCE_LANDMARKS_SIDE]
                    insert_cursor.insertRow(row)
                    landmark_id += 1

    def _calculate_intersect_point_position(self, intersect_feature):
        street_oid = intersect_feature[0]
        intersect_point = intersect_feature[1].firstPoint

        street_geometry = self.street_oid_shape_lookup[street_oid]
        street_length = street_geometry.length
        point_distance = street_geometry.measureOnLine(intersect_point)
        position = round(1.0 * point_distance / street_length, 2)
        return position

    def run(self):
        self._create_reference_landmarks_table()
        self._generate_reference_landmarks_records()

