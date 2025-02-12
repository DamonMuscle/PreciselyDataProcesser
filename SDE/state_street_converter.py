import os
import arcpy
import constants

from state_converter import StateConverter
from national_map_logger import NationalMapLogger


def _get_street_mapping_fields(source: str) -> str:
    return (
        f'Street "Street" true true false 100 Text 0 0,First,#,{source},STREET,0,99;'
        f'STREET2 "STREET2" true true false 100 Text 0 0,First,#,{source},STREET2,0,99;'
        f'STREET3 "STREET3" true true false 100 Text 0 0,First,#,{source},STREET3,0,99;'
        f'STREET4 "STREET4" true true false 100 Text 0 0,First,#,{source},STREET4,0,99;'
        f'Fromleft "Fromleft" true true false 4 Long 0 0,First,#,{source},FROMLEFT,-1,-1;'
        f'Toleft "Toleft" true true false 4 Long 0 0,First,#,{source},TOLEFT,-1,-1;'
        f'Fromright "Fromright" true true false 4 Long 0 0,First,#,{source},FROMRIGHT,-1,-1;'
        f'Toright "Toright" true true false 4 Long 0 0,First,#,{source},TORIGHT,-1,-1;'
        f'L_STRUCT "L_STRUCT" true true false 4 Long 0 0,First,#,{source},L_STRUCT,-1,-1;'
        f'R_STRUCT "R_STRUCT" true true false 4 Long 0 0,First,#,{source},R_STRUCT,-1,-1;'
        f'A1_LEFT "A1_LEFT" true true false 50 Text 0 0,First,#,{source},A1_LEFT,0,49;'
        f'A1_RIGHT "A1_RIGHT" true true false 50 Text 0 0,First,#,{source},A1_RIGHT,0,49;'
        f'LOCALITY_LEFT "LOCALITY_LEFT" true true false 50 Text 0 0,First,#,{source},LOCALITY_LEFT,0,49;'
        f'LOCALITY_CODE_LEFT "LOCALITY_CODE_LEFT" true true false 50 Text 0 0,First,#,{source},LOCALITY_CODE_LEFT,0,49;'
        f'LOCALITY_RIGHT "LOCALITY_RIGHT" true true false 50 Text 0 0,First,#,{source},LOCALITY_RIGHT,0,49;'
        f'LOCALITY_CODE_RIGHT "LOCALITY_CODE_RIGHT" true true false 50 Text 0 0,First,#,{source},LOCALITY_CODE_RIGHT,0,49;'
        f'Postcode_Left "Postcode_Left" true true false 10 Text 0 0,First,#,{source},PC_LEFT,0,9;'
        f'PostcodeName_Left "PostcodeName_Left" true true false 50 Text 0 0,First,#,{source},PNAM_LEFT,0,49;'
        f'Postcode_Right "Postcode_Right" true true false 10 Text 0 0,First,#,{source},PC_RIGHT,0,9;'
        f'PostcodeName_Right "PostcodeName_Right" true true false 50 Text 0 0,First,#,{source},PNAM_RIGHT,0,49;'
        f'streettype "streettype" true true false 4 Long 0 0,First,#,{source},FCODE,-1,-1;'
        f'ROAD_CLASS "ROAD_CLASS" true true false 2 Text 0 0,First,#,{source},ROAD_CLASS,0,1;'
        f'ROAD_TYPE "ROAD_TYPE" true true false 2 Text 0 0,First,#,{source},ROAD_TYPE,0,1;'
        f'AREA_TYPE "AREA_TYPE" true true false 2 Text 0 0,First,#,{source},AREA_TYPE,0,1;'
        f'LENGTH_GEO "LENGTH_GEO" true true false 8 Double 0 0,First,#,{source},LENGTH,-1,-1;'
        f'SURFACE_TYPE "SURFACE_TYPE" true true false 4 Long 0 0,First,#,{source},SURFACE_TYPE,-1,-1;'
        f'SPEED "SPEED" true true false 4 Long 0 0,First,#,{source},SPEED,-1,-1;'
        f'SPEED_VERIFIED "SPEED_VERIFIED" true true false 4 Long 0 0,First,#,{source},SPEED_VERIFIED,-1,-1;'
        f'SPEED_AMPEAK "SPEED_AMPEAK" true true false 8 Double 0 0,First,#,{source},SPEED_AMPEAK,-1,-1;'
        f'SPEED_PMPEAK "SPEED_PMPEAK" true true false 8 Double 0 0,First,#,{source},SPEED_PMPEAK,-1,-1;'
        f'SPEED_INTERPEAK "SPEED_INTERPEAK" true true false 8 Double 0 0,First,#,{source},SPEED_INTERPEAK,-1,-1;'
        f'SPEED_NIGHT "SPEED_NIGHT" true true false 8 Double 0 0,First,#,{source},SPEED_NIGHT,-1,-1;'
        f'SPEED_SEVENDAY "SPEED_SEVENDAY" true true false 8 Double 0 0,First,#,{source},SPEED_SEVENDAY,-1,-1;'
        f'Oneway "Oneway" true true false 4 Long 0 0,First,#,{source},ONEWAY,-1,-1;'
        f'ROUGHRD "ROUGHRD" true true false 4 Long 0 0,First,#,{source},ROUGHRD,-1,-1;'
        f'TOLL "TOLL" true true false 4 Long 0 0,First,#,{source},TOLL,-1,-1;'
        f'START_NODE "START_NODE" true true false 36 Text 0 0,First,#,{source},START_NODE,0,35;'
        f'END_NODE "END_NODE" true true false 36 Text 0 0,First,#,{source},END_NODE,0,35;'
        f'ROUTE_NUM "ROUTE_NUM" true true false 10 Text 0 0,First,#,{source},ROUTE_NUM,0,9;'
        f'FromElevation "FromElevation" true true false 4 Long 0 0,First,#,{source},LEVEL_BEG,-1,-1;'
        f'ToElevation "ToElevation" true true false 4 Long 0 0,First,#,{source},LEVEL_END,-1,-1;'
        f'HeightClearance "HeightClearance" true true false 8 Double 0 0,First,#,{source},MAX_HEIGHT,-1,-1;'
        f'MAX_WIDTH "MAX_WIDTH" true true false 8 Double 0 0,First,#,{source},MAX_WIDTH,-1,-1;'
        f'WeightLimit "WeightLimit" true true false 8 Double 0 0,First,#,{source},MAX_WEIGHT,-1,-1;'
        f'FEATURE_ID "FEATURE_ID" true true false 36 Text 0 0,First,#,{source},FEATURE_ID,0,35'
    )


def _get_plus_street_mapping_fields(source: str) -> str:
    return (
        f'Street "Street" true true false 255 Text 0 0,First,#,{source},STREET,0,99;'
        f'Fromleft "Fromleft" true true false 255 Text 0 0,First,#,{source},FROMLEFT,-1,-1;'
        f'Toleft "Toleft" true true false 255 Text 0 0,First,#,{source},TOLEFT,-1,-1;'
        f'Fromright "Fromright" true true false 255 Text 0 0,First,#,{source},FROMRIGHT,-1,-1;'
        f'Toright "Toright" true true false 255 Text 0 0,First,#,{source},TORIGHT,-1,-1;'
        f'LOCALITY_CODE_LEFT "LOCALITY_CODE_LEFT" true true false 50 Text 0 0,First,#,{source},LOCALITY_CODE_LEFT,0,49;'
        f'LOCALITY_CODE_RIGHT "LOCALITY_CODE_RIGHT" true true false 50 Text 0 0,First,#,{source},LOCALITY_CODE_RIGHT,0,49;'
        f'Postcode_Left "Postcode_Left" true true false 10 Text 0 0,First,#,{source},PC_LEFT,0,9;'
        f'Postcode_Right "Postcode_Right" true true false 10 Text 0 0,First,#,{source},PC_RIGHT,0,9;'
        f'streettype "streettype" true true false 4 Long 0 0,First,#,{source},FCODE,-1,-1;'
        f'ROAD_CLASS "ROAD_CLASS" true true false 2 Text 0 0,First,#,{source},ROAD_CLASS,0,1;'
        f'LENGTH_GEO "LENGTH_GEO" true true false 8 Double 0 0,First,#,{source},LENGTH,-1,-1;'
        f'SPEED "SPEED" true true false 4 Long 0 0,First,#,{source},SPEED,-1,-1;'
        f'Oneway "Oneway" true true false 255 Text 0 0,First,#,{source},ONEWAY,-1,-1;'
        f'ROUGHRD "ROUGHRD" true true false 4 Long 0 0,First,#,{source},ROUGHRD,-1,-1;'
        f'FromElevation "FromElevation" true true false 2 Short 0 0,First,#,{source},LEVEL_BEG,-1,-1;'
        f'ToElevation "ToElevation" true true false 2 Short 0 0,First,#,{source},LEVEL_END,-1,-1;'
        f'HeightClearance "HeightClearance" true true false 8 Double 0 0,First,#,{source},MAX_HEIGHT,-1,-1;'
        f'WeightLimit "WeightLimit" true true false 8 Double 0 0,First,#,{source},MAX_WEIGHT,-1,-1;'
        f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{source},FEATURE_ID,0,35'
    )


global_group_id = 1
DEFAULT_ARCPY_WORKSPACE = None
BUFFER_DISTANCE = '500 Meters'


def set_street_group_id(feature_class, where_clause=''):
    global global_group_id
    with arcpy.da.UpdateCursor(feature_class, ['GroupID'], where_clause) as cursor:
        for row in cursor:
            row[0] = global_group_id
            cursor.updateRow(row)
            global_group_id += 1


@NationalMapLogger.debug_decorator
def set_empty_street_group_id(feature_class):
    set_street_group_id(feature_class, "Street = ''")


@NationalMapLogger.debug_decorator
def calculate_group_id(streets_features, state_streets_group_polygon):

    field_name = 'GroupID'
    out_street_layer = 'temp_street_join_layer'
    arcpy.management.MakeFeatureLayer(streets_features, out_street_layer, "Street <> ''")

    print('- add spatial join')
    temp_name = 'GroupID1'
    arcpy.management.AddSpatialJoin(
        out_street_layer,
        state_streets_group_polygon,
        join_operation='JOIN_ONE_TO_ONE',
        join_type='KEEP_ALL',
        field_mapping=f'{temp_name} "{temp_name}" true true false 8 Double 0 0,First,#,streets_Group,{field_name},-1,-1',
        match_option='COMPLETELY_WITHIN',
        match_fields='Street Street'
    )

    print('- calculate field')
    arcpy.management.CalculateField(out_street_layer, field_name, f'!{temp_name}!')

    print('- remove join')
    arcpy.management.RemoveJoin(out_street_layer)
    arcpy.management.Delete(out_street_layer)


class StateStreetConverter(StateConverter):

    def __init__(self, data_settings, state_exporter):
        super().__init__(data_settings, state_exporter)
        self.data = {
            'state_street_feature_class': '',
            'state_node_feature_class': '',
            'state_restriction_feature_class': '',
            'state_signpost_feature_class': '',
            'state_signpost_table': '',
            'temp_town_features': ''
        }

    def __del__(self):
        super().__del__()

    def _add_field(self, field_name, field_type, field_length=None):
        street_feature_class = self.data['state_street_feature_class']
        NationalMapUtility.add_field(street_feature_class, field_name, field_type, field_length)

    def _drop_fields(self, field_name_list):
        street_feature_class = self.data['state_street_feature_class']
        arcpy.management.DeleteField(street_feature_class, field_name_list)

    def _export_state_streets(self):
        street_name = f'usa_{self.state}_streets'
        in_features = self.exporter.get_precisely_feature_path(street_name)
        field_mapping = _get_plus_street_mapping_fields(in_features)

        out_features = self.exporter.export_state_data_template(
            street_name,
            out_scratch_name='temp_streets',
            where_clause="ROAD_CLASS <> 'H'",
            field_mapping=field_mapping
        )

        self.data['state_street_feature_class'] = out_features

    def _export_temp_towns(self):
        town_name = f'{self.state}towns'
        in_features = self.exporter.get_precisely_feature_path(town_name)
        field_mapping = f'Name "Name" true true false 100 Text 0 0,First,#,{in_features},Name,0,99'
        out_features = self.exporter.export_state_data_template(
            town_name,
            out_scratch_name='temp_town_features',
            field_mapping=field_mapping
        )

        self.data['temp_town_features'] = out_features

    def _add_city_field(self):
        message = f'_add_city_field {self.state}'
        NationalMapLogger.debug(message)

        street_feature_class = self.data['state_street_feature_class']
        town_feature_class = self.data['temp_town_features']
        field_mapping = f'City "City" true true false 255 Text 0 0,First,#,{town_feature_class},Name,0,99'
        arcpy.management.AddSpatialJoin(
            target_features=street_feature_class,
            join_features=town_feature_class,
            join_operation='JOIN_ONE_TO_ONE',
            join_type='KEEP_ALL',
            field_mapping=field_mapping,
            match_option='WITHIN',
            search_radius=None,
            distance_field_name='',
            permanent_join='PERMANENT_FIELDS',
            match_fields=None
        )
        arcpy.management.DeleteField(street_feature_class, ['Join_Count'])

    @NationalMapLogger.debug_decorator
    def _create_street_group(self, street_feature_class):
        out_state_file_gdb = self.settings['scratch_geodatabase']
        out_state_streets_buffer_dissolve = os.path.join(out_state_file_gdb, 'streets_Buffer_Dissolve')
        arcpy.analysis.Buffer(street_feature_class, out_state_streets_buffer_dissolve,
                              buffer_distance_or_field=BUFFER_DISTANCE,
                              dissolve_option='LIST',
                              dissolve_field='STREET',
                              method='GEODESIC')
        out_buffer_layer = os.path.join(out_state_file_gdb, 'buffer_layer')

        arcpy.management.MakeFeatureLayer(out_state_streets_buffer_dissolve, out_buffer_layer)
        arcpy.management.SelectLayerByAttribute(out_buffer_layer, 'NEW_SELECTION', "STREET = ''")
        arcpy.management.DeleteFeatures(out_buffer_layer)
        arcpy.management.Delete(out_buffer_layer)

        out_state_streets_group = os.path.join(out_state_file_gdb, 'streets_Group')
        arcpy.management.MultipartToSinglepart(out_state_streets_buffer_dissolve, out_state_streets_group)
        arcpy.management.Delete(out_state_streets_buffer_dissolve)

        return out_state_streets_group

    @NationalMapLogger.debug_decorator
    def _add_group_id(self):
        out_state_file_gdb = self.settings['scratch_geodatabase']
        arcpy.env.workspace = out_state_file_gdb

        street_feature_class = self.data['state_street_feature_class']
        arcpy.management.AddField(street_feature_class, 'GroupID', 'DOUBLE')
        set_empty_street_group_id(street_feature_class)

        out_streets_group = self._create_street_group(street_feature_class)
        arcpy.management.AddField(out_streets_group, 'GroupID', 'DOUBLE')
        set_street_group_id(out_streets_group)

        calculate_group_id(street_feature_class, out_streets_group)
        arcpy.management.Delete(out_streets_group)

        arcpy.env.workspace = DEFAULT_ARCPY_WORKSPACE

    def _match_up_to_plus(self):
        message = f'_match_up_to_plus {self.state}'
        NationalMapLogger.debug(message)

        # Remove useless fields on routefinder plus
        fields = ['ROUGHRD', 'Postcode_Left', 'Postcode_Right',
                  'LOCALITY_CODE_LEFT', 'LOCALITY_CODE_RIGHT',
                  'streettype', 'ROAD_CLASS', 'SPEED']
        self._drop_fields(fields)

        # Add fields
        self._add_field('Style', 'TEXT', 255)
        self._add_field('Lock', 'TEXT', 255)
        self._add_field('Fow', 'SHORT')

        self._add_field('LastUpdated', 'DATE')
        self._add_field('LastUpdatedBy', 'LONG')
        self._add_field('CreatedOn', 'DATE')
        self._add_field('CreatedBy', 'LONG')

    def _alter_street_fields(self):
        # Add Fields
        self._add_field('State', 'Text', 255)
        self._add_field('RoadClass', 'LONG')
        self._add_field('Hierarchy', 'SHORT')
        self._add_field('Speedleft', 'LONG')
        self._add_field('Speedright', 'LONG')
        self._add_field('WALK_TIME', 'DOUBLE')
        self._add_field('LEFT_TIME', 'DOUBLE')
        self._add_field('RIGHT_TIME', 'DOUBLE')
        self._add_field('TraversableByVehicle', 'TEXT', 255)
        self._add_field('TraversableByWalkers', 'TEXT', 255)

        self._add_field('PostedLeft', 'LONG')
        self._add_field('PostedRight', 'LONG')
        self._add_field('LeftPostalCode', 'TEXT', 255)
        self._add_field('RightPostalCode', 'TEXT', 255)
        self._add_field('Cfcc', 'TEXT', 255)

        prohibit_crosser_default_value = 0
        street_feature_class = self.data['state_street_feature_class']
        arcpy.management.AddField(street_feature_class, 'ProhibitCrosser', 'SHORT', field_is_nullable='NULLABLE')
        arcpy.management.AssignDefaultToField(street_feature_class, 'ProhibitCrosser', prohibit_crosser_default_value,
                                              clear_value='DO_NOT_CLEAR')

    @NationalMapLogger.debug_decorator
    def _calculate_street_fields(self):
        street_feature_class = self.data['state_street_feature_class']
        prohibit_crosser_default_value = 0

        # Update Fields
        state_value = self.state.upper()
        address_value = '0'

        edit_fields = ['State', 'Street', 'Fromleft', 'Toleft', 'Fromright',
                       'Toright', 'RoadClass', 'Hierarchy', 'Speedleft', 'Speedright',
                       'WALK_TIME', 'LEFT_TIME', 'RIGHT_TIME', 'TraversableByVehicle', 'TraversableByWalkers',
                       'ProhibitCrosser']
        duplicate_fields = ['PostedLeft', 'PostedRight', 'LeftPostalCode', 'RightPostalCode', 'Cfcc']
        selected_fields = ['ROAD_CLASS', 'streettype', 'SPEED', 'Oneway', 'LENGTH_GEO',
                           'ROUGHRD', 'Postcode_Left', 'Postcode_Right']

        update_fields = edit_fields + duplicate_fields + selected_fields
        with arcpy.da.UpdateCursor(street_feature_class, update_fields) as cursor:
            for row in cursor:
                road_class, streettype, speed, oneway, length = row[21], row[22], row[23], row[24], row[25]
                roughrd, postcode_left, postcode_right = row[26], row[27], row[28]
                is_ramp_street = streettype % 1000 == 10 or streettype % 1000 == 510

                # Edit - 'State'
                row[0] = state_value

                # Edit - 'Street'
                if row[1] == '':
                    row[1] = 'Ramp' if is_ramp_street else 'Unnamed'

                # Edit - 'Fromleft', 'Toleft', 'Fromright', 'Toright'
                if row[2] == '-1':
                    row[2] = address_value
                if row[3] == '-1':
                    row[3] = address_value
                if row[4] == '-1':
                    row[4] = address_value
                if row[5] == '-1':
                    row[5] = address_value

                # Edit - 'RoadClass'
                if streettype == 28019:
                    # _cast_stairs
                    row[6] = 12
                elif streettype % 1000 == 4:
                    # _cast_roundabouts
                    row[6] = 5
                elif is_ramp_street:
                    # _cast_ramps
                    row[6] = 3
                elif road_class == 'Z' and streettype in [26014, 27014, 27514, 28014, 28015, 29016, 28515, 29116,
                                                          29216]:
                    # _cast_pedestrian
                    row[6] = 10
                elif road_class in ['S', 'T', 'P', 'Q']:
                    # _cast_major_road
                    row[6] = 6
                elif road_class in ['M', 'N', 'G', 'I']:
                    # _cast_highways
                    row[6] = 2
                else:
                    # default
                    row[6] = 1

                # Duplicate - 'Cfcc'
                row[20] = row[6]

                # Edit - 'Hierarchy'
                if road_class in ['M', 'N', 'G', 'I']:
                    row[7] = 1
                elif road_class in ['P', 'Q']:
                    row[7] = 2
                elif road_class in ['S', 'T']:
                    row[7] = 3
                elif road_class in ['C', 'F']:
                    row[7] = 4
                else:
                    row[7] = 5

                # Edit - 'Speedleft', 'Speedright'
                speed_left = 0 if oneway == '2' else speed
                speed_right = 0 if oneway == '3' else speed
                row[8], row[9] = speed_left, speed_right
                # Duplicate - 'PostedLeft', 'PostedRight'
                row[16], row[17] = row[8], row[9]

                # Edit - 'WALK_TIME', 'LEFT_TIME', 'RIGHT_TIME'
                row[10] = length / 84.0
                row[11] = 0 if speed_left == 0 else (length / speed_left) * 0.000621371192 * 60
                row[12] = 0 if speed_right == 0 else (length / speed_right) * 0.000621371192 * 60

                # Edit - 'TraversableByVehicle', 'TraversableByWalkers'
                if (oneway == '4' and road_class in [10, 12]) or (roughrd == 1):
                    row[13] = 'F'
                else:
                    row[13] = 'T'
                row[14] = 'T'

                # Edit - 'ProhibitCrosser'
                row[15] = prohibit_crosser_default_value

                # Duplicate - 'LeftPostalCode', 'RightPostalCode'
                row[18], row[19] = postcode_left[:5], postcode_right[:5]

                cursor.updateRow(row)

    @NationalMapLogger.info_decorator
    def _modify_street_fields(self):
        self._alter_street_fields()
        self._add_group_id()
        self._calculate_street_fields()
        self._add_city_field()
        self._match_up_to_plus()

    def _project_state_street(self):
        out_features = self.data['state_street_feature_class']
        self.exporter.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['street_name'])

    def _clear_workspace(self):
        arcpy.management.Delete(self.data['temp_town_features'])

    def run(self):
        self._export_state_streets()
        self._export_temp_towns()
        self._modify_street_fields()
        self._project_state_street()
        self._clear_workspace()
