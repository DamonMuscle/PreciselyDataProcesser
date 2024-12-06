import arcpy
import constants

from national_map_logger import NationalMapLogger
from state_converter import StateConverter


class StateNodeConverter(StateConverter):

    def __init__(self, data_settings, state_exporter, data):
        super().__init__(data_settings, state_exporter, data)

    def __del__(self):
        super().__del__()

    def _export_state_nodes(self):
        street_name = f'usa_{self.state}_nodes'
        out_features = self.exporter.export_state_data_template(
            street_name,
            out_scratch_name='temp_nodes',
            where_clause='VALENCE > 2'
        )

        self.data['state_node_feature_class'] = out_features

    def _exclude_untouched_nodes(self):
        node_feature_class = self.data['state_node_feature_class']
        memory_layer = self.create_memory_layer()
        arcpy.management.MakeFeatureLayer(node_feature_class, memory_layer)

        select_features = self.data['state_street_feature_class']
        result = arcpy.management.SelectLayerByLocation(
            in_layer=memory_layer,
            overlap_type='INTERSECT',
            select_features=select_features,
            search_distance=None,
            selection_type='NEW_SELECTION',
            invert_spatial_relationship='INVERT'
        )
        selection_count = int(result.getOutput(2))
        message = f'_exclude_untouched_nodes {selection_count}, {self.state}'
        NationalMapLogger.debug(message)

        if selection_count > 0:
            arcpy.management.DeleteFeatures(memory_layer)

        self.dispose_memory_layer()

    def _project_state_node(self):
        out_features = self.data['state_node_feature_class']
        self.exporter.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['node_name'])

    def _clear_workspace(self):
        arcpy.management.Delete(self.data['state_node_feature_class'])
        arcpy.management.Delete(self.data['state_street_feature_class'])

    def run(self):
        self._export_state_nodes()
        self._exclude_untouched_nodes()
        self._project_state_node()
        self._clear_workspace()
