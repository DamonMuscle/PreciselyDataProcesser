import os

import arcpy
from national_map import constants

from state_converter import StateConverter
from national_map_utility import NationalMapUtility
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
        f'Oneway "Oneway" true true false 4 Long 0 0,First,#,{source},ONEWAY,-1,-1;'
        f'ROUGHRD "ROUGHRD" true true false 4 Long 0 0,First,#,{source},ROUGHRD,-1,-1;'
        f'FromElevation "FromElevation" true true false 4 Long 0 0,First,#,{source},LEVEL_BEG,-1,-1;'
        f'ToElevation "ToElevation" true true false 4 Long 0 0,First,#,{source},LEVEL_END,-1,-1;'
        f'HeightClearance "HeightClearance" true true false 8 Double 0 0,First,#,{source},MAX_HEIGHT,-1,-1;'
        f'MAX_WIDTH "MAX_WIDTH" true true false 8 Double 0 0,First,#,{source},MAX_WIDTH,-1,-1;'
        f'WeightLimit "WeightLimit" true true false 8 Double 0 0,First,#,{source},MAX_WEIGHT,-1,-1;'
        f'LocalId "LocalId" true true false 255 Text 0 0,First,#,{source},FEATURE_ID,0,35'
    )


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

    def _calculate_field(self, field_name, expression):
        street_feature_class = self.data['state_street_feature_class']
        arcpy.management.CalculateField(street_feature_class, field_name, expression)

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

    def _calculate_state_field(self):
        message = f'_calculate_state_field {self.state}'
        NationalMapLogger.debug(message)

        field_name = 'State'
        self._add_field(field_name, 'Text', 255)

        field_value = self.state.upper()
        self._calculate_field(field_name, f'"{field_value}"')

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

    def _calculate_ramp_street(self):
        NationalMapLogger.debug(f'_calculate_ramp_street')
        self._cast_field_template(
            field_name='Street',
            field_value='"Ramp"',
            where_clause=f"Street = '' AND (MOD(streettype, 1000) = 10 OR MOD(streettype, 1000) = 510)"
        )

    def _calculate_unnamed_street(self):
        NationalMapLogger.debug(f'_calculate_unnamed_street')
        self._cast_field_template(field_name='Street', field_value='"Unnamed"', where_clause=f"Street = ''")

    def _calculate_address_range(self):
        NationalMapLogger.debug(f'_calculate_address_range')
        field_names = ['Fromleft', 'Toleft', 'Fromright', 'Toright']
        field_value = 0
        for field_name in field_names:
            NationalMapLogger.debug(f'calculate {field_name}')
            self._cast_field_template(field_name, field_value, where_clause=f"{field_name} = '-1'")

    def _calculate_default_road_class(self):
        self._calculate_field('RoadClass', 1)

    def _cast_field_template(self, field_name, field_value, where_clause):
        street_feature_class = self.data['state_street_feature_class']
        memory_layer = self.create_memory_layer()
        arcpy.management.MakeFeatureLayer(street_feature_class, memory_layer, where_clause)
        arcpy.management.CalculateField(memory_layer, field_name, field_value)
        self.dispose_memory_layer()

    def _cast_highways(self):
        self._cast_field_template(field_name='RoadClass', field_value=2, where_clause="ROAD_CLASS IN ('M','N','G','I')")

    def _cast_major_road(self):
        self._cast_field_template(field_name='RoadClass', field_value=6, where_clause="ROAD_CLASS IN ('S','T','P','Q')")

    def _cast_pedestrian(self):
        self._cast_field_template(
            field_name='RoadClass',
            field_value=10,
            where_clause="streettype IN (26014,27014,27514,28014,28015,29016,28515,29116,29216) AND ROAD_CLASS = 'Z'"
        )

    def _cast_ramps(self):
        self._cast_field_template(field_name='RoadClass', field_value=3,
                                  where_clause="MOD(streettype, 1000) = 10 OR MOD(streettype, 1000) = 510")

    def _cast_roundabouts(self):
        self._cast_field_template(field_name='RoadClass', field_value=5, where_clause="MOD(streettype, 1000) = 4")

    def _cast_stairs(self):
        self._cast_field_template(field_name='RoadClass', field_value=12, where_clause="streettype = 28019")

    def _calculate_road_class(self):
        message = f'_calculate_road_class {self.state}'
        NationalMapLogger.debug(message)

        self._add_field('RoadClass', 'SHORT')
        self._calculate_default_road_class()
        self._cast_highways()
        self._cast_major_road()
        self._cast_pedestrian()
        self._cast_ramps()
        self._cast_roundabouts()
        self._cast_stairs()

    def _calculate_default_hierarchy(self):
        self._calculate_field('Hierarchy', 5)

    def _cast_hierarchy_1(self):
        self._cast_field_template(field_name='Hierarchy', field_value=1, where_clause="ROAD_CLASS IN ('M','N','G','I')")

    def _cast_hierarchy_2(self):
        self._cast_field_template(field_name='Hierarchy', field_value=2, where_clause="ROAD_CLASS IN ('P','Q')")

    def _cast_hierarchy_3(self):
        self._cast_field_template(field_name='Hierarchy', field_value=3, where_clause="ROAD_CLASS IN ('S','T')")

    def _cast_hierarchy_4(self):
        self._cast_field_template(field_name='Hierarchy', field_value=4, where_clause="ROAD_CLASS IN ('C','F')")

    def _calculate_hierarchy(self):
        message = f'_calculate_hierarchy {self.state}'
        NationalMapLogger.debug(message)

        self._add_field('Hierarchy', 'SHORT')
        self._calculate_default_hierarchy()
        self._cast_hierarchy_1()
        self._cast_hierarchy_2()
        self._cast_hierarchy_3()
        self._cast_hierarchy_4()

    def _calculate_speed_left(self):
        field_name = 'Speedleft'
        self._add_field(field_name, 'LONG')
        self._calculate_field(field_name, '!SPEED!')
        self._cast_field_template(field_name, field_value=0, where_clause='ONEWAY = 2')

    def _calculate_speed_right(self):
        field_name = 'Speedright'
        self._add_field(field_name, 'LONG')
        self._calculate_field(field_name, '!SPEED!')
        self._cast_field_template(field_name, field_value=0, where_clause='ONEWAY = 3')

    def _calculate_oneway(self):
        message = f"_calculate_oneway {self.state}"
        NationalMapLogger.debug(message)

        self._calculate_speed_left()
        self._calculate_speed_right()

    def _calculate_walk_time(self):
        field_name = 'WALK_TIME'
        self._add_field(field_name, 'DOUBLE')
        self._calculate_field(field_name, '!LENGTH_GEO! / 84!')

    def _calculate_left_time(self):
        field_name = 'LEFT_TIME'
        self._add_field(field_name, 'DOUBLE')
        self._cast_field_template(field_name, field_value=0, where_clause='Speedleft = 0')
        self._cast_field_template(
            field_name,
            field_value='(!LENGTH_GEO! / !Speedleft!) * 0.000621371192 * 60',
            where_clause='Speedleft <> 0'
        )

    def _calculate_right_time(self):
        field_name = 'RIGHT_TIME'
        self._add_field(field_name, 'DOUBLE')
        self._cast_field_template(field_name, field_value=0, where_clause='Speedright = 0')
        self._cast_field_template(
            field_name,
            field_value='(!LENGTH_GEO! / !Speedright!) * 0.000621371192 * 60',
            where_clause='Speedright <> 0'
        )

    def _calculate_travel_time(self):
        message = f'_calculate_travel_time {self.state}'
        NationalMapLogger.debug(message)

        self._calculate_walk_time()
        self._calculate_left_time()
        self._calculate_right_time()

    def _calculate_traversable_by_vehicle(self):
        field_name = 'TraversableByVehicle'
        self._add_field(field_name, 'TEXT', 255)
        self._cast_field_template(field_name, field_value='"F"', where_clause='Traversable <> 1')
        self._cast_field_template(field_name, field_value='"T"', where_clause='Traversable = 1')

    def _calculate_traversable_by_walker(self):
        field_name = 'TraversableByWalkers'
        self._add_field(field_name, 'TEXT', 255)
        self._calculate_field(field_name, '"T"')

    def _cast_traversable(self):
        field_name = 'Traversable'
        self._add_field(field_name, 'SHORT')
        self._calculate_field(field_name, 1)
        self._cast_field_template(field_name, field_value=0, where_clause='ONEWAY = 4 AND RoadClass IN (10, 12)')
        self._cast_field_template(field_name, field_value=0, where_clause='ROUGHRD = 1')

    def _calculate_traversable(self):
        self._cast_traversable()
        self._calculate_traversable_by_vehicle()
        self._calculate_traversable_by_walker()

    def _add_posted_left(self):
        field_name = 'PostedLeft'
        self._add_field(field_name, 'LONG')
        self._calculate_field(field_name, '!Speedleft!')

    def _add_posted_right(self):
        field_name = 'PostedRight'
        self._add_field(field_name, 'LONG')
        self._calculate_field(field_name, '!Speedright!')

    def _add_from_to_to_from(self):
        field_name = 'fromtotofrom'
        self._add_field(field_name, 'TEXT', 5)
        self._calculate_field(field_name, '!ONEWAY!')

    def _add_left_post_code(self):
        field_name = 'LeftPostalCode'
        self._add_field(field_name, 'TEXT', 255)
        self._calculate_field(field_name, '!Postcode_Left![:5]')

    def _add_right_post_code(self):
        field_name = 'RightPostalCode'
        self._add_field(field_name, 'TEXT', 255)
        self._calculate_field(field_name, '!Postcode_Right![:5]')

    def _add_state_left(self):
        field_name = 'StateLeft'
        self._add_field(field_name, 'TEXT', 2)
        self._calculate_field(field_name, '!LOCALITY_CODE_LEFT![0:2]')

    def _add_state_right(self):
        field_name = 'StateRight'
        self._add_field(field_name, 'TEXT', 2)
        self._calculate_field(field_name, '!LOCALITY_CODE_RIGHT![0:2]')

    def _add_prohibit_crosser(self):
        field_name = 'ProhibitCrosser'
        street_feature_class = self.data['state_street_feature_class']
        if not NationalMapUtility.is_field_exists(street_feature_class, field_name):
            arcpy.management.AddField(street_feature_class, field_name, 'SHORT', field_is_nullable='NULLABLE')
            arcpy.management.AssignDefaultToField(street_feature_class, field_name, '0',
                                                  clear_value='DO_NOT_CLEAR')
            self._calculate_field(field_name, 0)

    def _duplicate_fields_for_plus(self):
        message = f'_duplicate_fields_for_plus {self.state}'
        NationalMapLogger.debug(message)

        self._add_posted_left()
        self._add_posted_right()
        # self._add_from_to_to_from()
        self._add_left_post_code()
        self._add_right_post_code()
        self._add_state_left()
        self._add_state_right()
        self._add_prohibit_crosser()

    def _remove_fields_for_plus(self):
        message = f'_remove_fields_for_plus {self.state}'
        NationalMapLogger.debug(message)

        street_feature_class = self.data['state_street_feature_class']
        # Remove useless fields on routefinder plus
        drop_fields = ['ROUGHRD', 'Postcode_Left', 'Postcode_Right', 'LOCALITY_CODE_LEFT', 'LOCALITY_CODE_RIGHT']
        arcpy.management.DeleteField(street_feature_class, drop_fields)

    def _consistent_fields_for_plus(self):
        self._add_field('GroupID', 'DOUBLE')
        self._add_field('Style', 'TEXT', 255)
        self._add_field('Cfcc', 'TEXT', 255)
        self._add_field('Lock', 'TEXT', 255)
        self._add_field('Fow', 'SHORT')

        self._add_field('created_user', 'TEXT', 255)
        self._add_field('created_date', 'DATE')
        self._add_field('last_edited_user', 'TEXT', 255)
        self._add_field('last_edited_date', 'DATE')

        self._add_field('LastUpdated', 'DATE')
        self._add_field('LastUpdatedBy', 'LONG')
        self._add_field('CreatedOn', 'DATE')
        self._add_field('CreatedBy', 'LONG')

    def _modify_street_fields(self):
        self._calculate_state_field()
        self._add_city_field()
        self._calculate_ramp_street()
        self._calculate_unnamed_street()
        self._calculate_address_range()
        self._calculate_road_class()
        self._calculate_hierarchy()
        self._calculate_oneway()
        self._calculate_travel_time()
        self._calculate_traversable()

        self._duplicate_fields_for_plus()
        self._remove_fields_for_plus()
        self._consistent_fields_for_plus()

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

