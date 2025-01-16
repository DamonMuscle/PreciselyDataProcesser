import os
import arcpy
from typing import Literal


class NationalMapUtility:

    @staticmethod
    def ensure_path_exists(path) -> None:
        if not os.path.exists(path):
            os.mkdir(path)

    @staticmethod
    def set_arcpy_workspace(workspace) -> None:
        arcpy.env.workspace = workspace

    @staticmethod
    def get_count(feature_class_or_table):
        return arcpy.management.GetCount(feature_class_or_table)

    @staticmethod
    def is_field_exists(table_or_feature_class, field_name) -> bool:
        result = False
        fields = arcpy.ListFields(table_or_feature_class)
        for field in fields:
            if field.name == field_name:
                result = True
                break
        return result

    @staticmethod
    def add_field(in_table, field_name, field_type, field_length=None, field_is_nullable='NULLABLE') -> bool:
        result = False
        if not NationalMapUtility.is_field_exists(in_table, field_name):
            arcpy.management.AddField(in_table, field_name, field_type,
                                      field_length=field_length, field_is_nullable=field_is_nullable)
            result = True

        return result

    @staticmethod
    def is_feature_dataset_exists(feature_dataset_name) -> bool:
        result = False
        feature_datasets = arcpy.ListDatasets('*', 'Feature')
        if feature_datasets is None:
            return result

        for dataset in feature_datasets:
            if dataset == feature_dataset_name:
                result = True
                break

        return result

    @staticmethod
    def get_edge_end(first_geometry, second_geometry) -> Literal['Y', 'N']:
        result: Literal['Y', 'N'] = 'Y'
        first_start_point = first_geometry.firstPoint

        second_start_point = second_geometry.firstPoint
        second_end_point = second_geometry.lastPoint

        same_as_second_start = first_start_point.X == second_start_point.X and first_start_point.Y == second_start_point.Y
        same_as_second_end = first_start_point.X == second_end_point.X and first_start_point.Y == second_end_point.Y

        if same_as_second_start or same_as_second_end:
            result = 'N'

        return result

    @staticmethod
    def is_feature_class(feature_class_or_table) -> bool:
        desc = arcpy.Describe(feature_class_or_table)
        return hasattr(desc, 'featureType')
