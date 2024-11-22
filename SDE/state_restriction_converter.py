import arcpy
from national_map import constants

from state_converter import StateConverter


class StateRestrictionConverter(StateConverter):
    def __init__(self, data_settings, state_exporter, data):
        super().__init__(data_settings, state_exporter, data)

    def __del__(self):
        super().__del__()

    def _export_state_restrictions(self):
        restriction_name = f'usa_{self.state}_restrictions'
        in_features = self.exporter.get_precisely_feature_path(restriction_name)
        field_mapping = (
            f'RESTRICTION_ID "RESTRICTION_ID" true true false 36 Text 0 0,First,#,{in_features},RESTRICTION_ID,0,35;'
            f'SEQUENCE_NUM "SEQUENCE_NUM" true true false 4 Long 0 0,First,#,{in_features},SEQUENCE_NUM,-1,-1;'
            f'FEATURE_ID "FEATURE_ID" true true false 36 Text 0 0,First,#,{in_features},FEATURE_ID,0,35'
        )
        out_features = self.exporter.export_state_data_template(
            restriction_name,
            out_scratch_name='temp_restrictions',
            where_clause="RESTRICTION_TYPE = '8I' AND VEHICLE_TYPE = 0",
            field_mapping=field_mapping
        )

        self.data['state_restriction_feature_class'] = out_features

    def _add_state_and_city(self):
        in_data = self.data['state_restriction_feature_class']
        street_feature_class = self.data['state_street_feature_class']
        arcpy.management.JoinField(
            in_data=in_data,
            in_field='FEATURE_ID',
            join_table=street_feature_class,
            join_field='LocalId',
            fields='State;City'
        )

    def _project_state_restriction(self):
        out_features = self.data['state_restriction_feature_class']
        self.exporter.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['restriction_name'])

    def _clear_workspace(self):
        arcpy.management.Delete(self.data['state_restriction_feature_class'])

    def run(self):
        self._export_state_restrictions()
        self._add_state_and_city()
        self._project_state_restriction()
        self._clear_workspace()
