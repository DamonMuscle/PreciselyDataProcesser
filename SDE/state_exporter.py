import os

import arcpy

from national_map_logger import NationalMapLogger
from national_map_utility import NationalMapUtility
import constants


def add_editable_fields(layer):
    # keep consistent with plus
    NationalMapUtility.add_field(layer, 'LastUpdated', 'DATE')
    NationalMapUtility.add_field(layer, 'LastUpdatedBy', 'LONG')
    NationalMapUtility.add_field(layer, 'CreatedOn', 'DATE')
    NationalMapUtility.add_field(layer, 'CreatedBy', 'LONG')


def add_style_field(out_features):
    NationalMapUtility.add_field(out_features, 'Style', 'TEXT', 255)


def add_local_id_field(out_features):
    NationalMapUtility.add_field(out_features, 'LocalId', 'TEXT', 255)


def add_name_field(out_features):
    NationalMapUtility.add_field(out_features, 'Name', 'TEXT', 255)


class StateExporter:
    """
    Convert US State basemap data to routefinder plus data format.
    Basemap data includes: county, landmark, postcode, railroad, river, town and waterbody.
    """

    def __init__(self, data_settings):
        self.state = data_settings.state
        self.settings = data_settings.data
        self.temp_town_features = None

    def __del__(self):
        del self.state
        del self.settings
        del self.temp_town_features

    def export_state_data_template(self, in_name, out_scratch_name, where_clause='#',
                                   use_field_alias_as_name='#', field_mapping='#', sort_field='#'):
        in_features = self.get_precisely_feature_path(in_name)
        out_features = self._get_scratch_feature_class(out_scratch_name)
        arcpy.conversion.ExportFeatures(in_features, out_features, where_clause,
                                        use_field_alias_as_name, field_mapping, sort_field)
        return out_features

    def project_state_data(self, in_feature_class, out_name):
        message = f'project_state_data, {self.state}, {out_name}'
        NationalMapLogger.debug(message)

        out_features = os.path.join(self.settings['scratch_geodatabase'], out_name)

        arcpy.env.XYTolerance = '0.001 Meters'
        arcpy.management.Project(in_feature_class, out_features, constants.SR_WEB_MERCATOR)

    def _get_scratch_feature_class(self, scratch_name):
        return os.path.join(self.settings['scratch_geodatabase'], scratch_name)

    def _create_scratch_file_geodatabase(self):
        scratch_geodatabase = self.settings['scratch_geodatabase']
        if not arcpy.Exists(scratch_geodatabase):
            scratch_folder = self.settings['scratch_folder']
            arcpy.management.CreateFileGDB(scratch_folder, self.state)

    def get_precisely_feature_path(self, feature_name):
        precisely_gdb = self.settings['precisely_geodatabase']
        return os.path.join(precisely_gdb, feature_name)

    def _export_temp_town_features(self):
        scratch_name = 'temp_town_features'
        town_name = f'{self.state}towns'
        in_features = self.get_precisely_feature_path(town_name)
        field_mapping = (
            f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'State "State" true true false 255 Text 0 0,First,#,{in_features},A1_Abbrev,0,1;'
            f'A2_Code "A2_Code" true true false 5 Text 0 0,First,#,{in_features},A2_Code,0,4;'
            f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35'
        )

        out_features = self.export_state_data_template(
            town_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )
        return out_features

    def _join_county_fields(self, input_table):
        county_name = f'{self.state}counties'
        join_table = self.get_precisely_feature_path(county_name)

        arcpy.management.JoinField(
            in_data=input_table,
            in_field='A2_Code',
            join_table=join_table,
            join_field='A2_Code',
            fields=None,
            fm_option='USE_FM',
            field_mapping=f'County "County" true true false 255 Text 0 0,First,#,{join_table},Name,0,99',
            index_join_fields='NO_INDEXES'
        )

        arcpy.management.DeleteField(input_table, ['A2_Code'])

    def _export_state_towns(self):
        out_features = self._export_temp_town_features()
        self._join_county_fields(out_features)

        add_style_field(out_features)
        add_editable_fields(out_features)
        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['town_name'])
        self.temp_town_features = out_features

    def _export_state_counties(self):
        scratch_name = 'temp_counties_features'
        counties_name = f'{self.state}counties'
        in_features = self.get_precisely_feature_path(counties_name)

        field_mapping = (
            f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'State "State" true true false 255 Text 0 0,First,#,{in_features},A1_Abbrev,0,1;'
            f'County "County" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35'
        )
        out_features = self.export_state_data_template(
            counties_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )

        add_style_field(out_features)
        add_editable_fields(out_features)

        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['counties_name'])

    def _export_state_water_bodies(self):
        scratch_name = 'temp_water_bodies_features'
        waterbodies_name = f'{self.state}waterbodies'
        in_features = self.get_precisely_feature_path(waterbodies_name)
        field_mapping = (
            f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35'
        )
        out_features = self.export_state_data_template(
            waterbodies_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )

        add_style_field(out_features)
        add_editable_fields(out_features)
        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['waterbody_name'])

    def _export_state_rivers(self):
        scratch_name = 'temp_rivers_features'
        rivers_name = f'{self.state}rivers'
        in_features = self.get_precisely_feature_path(rivers_name)
        field_mapping = (
            f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35'
        )
        out_features = self.export_state_data_template(
            rivers_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )

        add_style_field(out_features)
        add_editable_fields(out_features)
        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['river_name'])

    def _export_state_railroads(self):
        scratch_name = 'temp_railroads_features'
        railroads_name = f'{self.state}railroads'
        in_features = self.get_precisely_feature_path(railroads_name)
        field_mapping = (
            f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35;'
            f'FromElevation "FromElevation" true true false 4 Long 0 0,First,#,{in_features},BeginGradeLevel,-1,-1;'
            f'ToElevation "ToElevation" true true false 4 Long 0 0,First,#,{in_features},EndGradeLevel,-1,-1'
        )
        out_features = self.export_state_data_template(
            railroads_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )

        add_style_field(out_features)
        add_editable_fields(out_features)

        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['railroad_name'])

    def _export_state_landuse(self):
        scratch_name = 'temp_landuse_features'
        landuse_name = f'{self.state}landuse'
        in_features = self.get_precisely_feature_path(landuse_name)
        out_features = None
        if arcpy.Exists(in_features):
            field_mapping = (
                f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
                f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35;'
            )
            out_features = self.export_state_data_template(
                landuse_name,
                out_scratch_name=scratch_name,
                field_mapping=field_mapping
            )

            add_style_field(out_features)
            add_editable_fields(out_features)
        return out_features

    def _export_state_airports(self):
        scratch_name = 'temp_airports_features'
        airports_name = f'{self.state}airports'
        in_features = self.get_precisely_feature_path(airports_name)
        out_features = None
        if arcpy.Exists(in_features):
            field_mapping = (
                f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
                f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35;'
            )
            out_features = self.export_state_data_template(
                airports_name,
                out_scratch_name=scratch_name,
                field_mapping=field_mapping
            )

            add_style_field(out_features)
            add_editable_fields(out_features)
        return out_features

    def _export_state_landmarks_polygon(self):
        scratch_name = 'temp_landmarks_polygon_features'
        out_features = self._get_scratch_feature_class(scratch_name)

        state_airports = self._export_state_airports()
        state_landuse = self._export_state_landuse()

        arcpy.management.CopyFeatures(state_landuse, out_features)
        if state_airports:
            arcpy.management.Append(state_airports, out_features, 'NO_TEST')

        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['landmark_polygon_name'])

    def _export_state_landmarks_polyline(self):
        state_landmark_polyline = constants.GDB_ITEMS_DICT['STATE']['landmark_polyline_name']
        out_gdb = self.settings['scratch_geodatabase']
        arcpy.management.CreateFeatureclass(out_gdb, state_landmark_polyline,
                                            geometry_type='POLYLINE',
                                            spatial_reference=constants.SR_WEB_MERCATOR)

        out_features = self._get_scratch_feature_class(state_landmark_polyline)
        add_name_field(out_features)
        add_style_field(out_features)
        add_local_id_field(out_features)
        add_editable_fields(out_features)

    def _export_state_landmarks_point(self):
        scratch_name = 'temp_landmarks_features'
        landmarks_name = f'{self.state}landmarks'
        in_features = self.get_precisely_feature_path(landmarks_name)
        field_mapping = (
            f'Name "Name" true true false 255 Text 0 0,First,#,{in_features},Name,0,99;'
            f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{in_features},ID,0,35;'
        )
        out_features = self.export_state_data_template(
            landmarks_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )

        add_style_field(out_features)
        add_editable_fields(out_features)
        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['landmark_name'])

    def _export_state_landmarks(self):
        self._export_state_landmarks_polygon()
        self._export_state_landmarks_polyline()
        self._export_state_landmarks_point()

    def _export_temp_postcodes_features(self):
        scratch_name = 'temp_postcodes_features'
        postcodes_name = f'{self.state}postcodes'
        in_features = self.get_precisely_feature_path(postcodes_name)
        field_mapping = (
            f'PC_Name "PC_Name" true true false 50 Text 0 0,First,#,{in_features},PC_Name,0,50;'
            f'PostalCode "PostalCode" true true false 10 Text 0 0,First,#,{in_features},PostalCode,0,10;'
        )
        out_features = self.export_state_data_template(
            postcodes_name,
            out_scratch_name=scratch_name,
            field_mapping=field_mapping
        )
        return out_features

    def _join_city_and_state(self, input_table):
        field_mapping = (
            f'State "State" true true false 255 Text 0 0,First,#,{self.temp_town_features},State,0,254;'
            f'City "City" true true false 255 Text 0 0,First,#,{self.temp_town_features},County,0,254'
        )
        arcpy.management.AddSpatialJoin(
            target_features=input_table,
            join_features=self.temp_town_features,
            field_mapping=field_mapping,
            match_option='CLOSEST',
            permanent_join='PERMANENT_FIELDS'
        )

    def _export_state_postcodes(self):
        out_features = self._export_temp_postcodes_features()
        self._join_city_and_state(out_features)

        add_name_field(out_features)
        arcpy.management.CalculateField(out_features, 'Name', '!PostalCode!')

        add_style_field(out_features)
        add_local_id_field(out_features)
        arcpy.management.CalculateField(out_features, 'LocalId', '!PostalCode!')

        add_editable_fields(out_features)

        drop_fields = ['Join_Count', 'PC_Name', 'PostalCode']
        arcpy.management.DeleteField(out_features, drop_fields)

        self.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['postcode_name'])

    def run(self):
        self._create_scratch_file_geodatabase()
        self._export_state_landmarks()
        self._export_state_railroads()
        self._export_state_towns()
        self._export_state_postcodes()
        self._export_state_rivers()
        self._export_state_water_bodies()
        # self._export_state_counties()
