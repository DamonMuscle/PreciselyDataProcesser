import os
import arcpy

import constants
from national_gdb_data_factory import NationalGDBDataFactory
from national_map_logger import NationalMapLogger

SCRATCH_GDB_NAME = 'scratch_gdb'


def build_network_dataset(network_dataset):
    if arcpy.Exists(network_dataset):
        arcpy.na.BuildNetwork(network_dataset)


def check_out_network_analyst_extension_license():
    result = True
    if arcpy.CheckExtension('Network') == 'Available':
        arcpy.CheckOutExtension('Network')
    else:
        NationalMapLogger.error('The Network Analyst license is unavailable.')
        result = False
    return result


def check_in_network_analyst_extension_license():
    arcpy.CheckInExtension('Network')


class NationalNetworkFactory(NationalGDBDataFactory):
    def __init__(self, configuration, workspace):
        super().__init__(workspace)
        output_configuration = configuration.data['Outputs']
        self.output_format = output_configuration['format']
        self.network_dataset_template = self._get_network_dataset_template()
        self.dissolve_network_file_gdb_name = output_configuration['dissolve_network_file_geodatabase_name']

        self.out_geodatabase_folder = output_configuration['geodatabase_folder']
        self.scratch_folder = output_configuration['scratch_folder']
        self.network_dataset = None
        self.scratch_network_dataset = None

    def __del__(self):
        super().__del__()
        del self.output_format
        del self.network_dataset_template
        del self.dissolve_network_file_gdb_name

        del self.out_geodatabase_folder
        del self.scratch_folder
        del self.network_dataset
        del self.scratch_network_dataset

    def _get_network_dataset_template(self):
        network_dataset_template = None
        if self.output_format == constants.OUT_FORMAT['SDE']:
            network_dataset_template = os.path.join('templates', 'sde_network_dataset_template.xml')
        elif self.output_format == constants.OUT_FORMAT['FILE_GDB']:
            network_dataset_template = os.path.join('templates', 'file_gdb_network_dataset_template.xml')
        return network_dataset_template

    @NationalMapLogger.debug_decorator
    def _create_network_dataset(self):
        dataset = self._get_dataset()
        self.network_dataset = arcpy.na.CreateNetworkDatasetFromTemplate(self.network_dataset_template, dataset)
        build_network_dataset(self.network_dataset)

    @NationalMapLogger.debug_decorator
    def _copy_network_dataset(self):
        result = arcpy.management.CreateFileGDB(self.scratch_folder, SCRATCH_GDB_NAME)
        scratch_network_location = result.getOutput(0)
        scratch_network_dataset = os.path.join(scratch_network_location, 'RoutingND')
        self.scratch_network_dataset = scratch_network_dataset

        dataset = self._get_dataset()

        street_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name']
        node_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['node_name']
        signpost_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['signpost_name']
        turn_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['turn_name']
        signpost_table_name = constants.GDB_ITEMS_DICT['NATIONAL']['signpost_table_name']
        dataset_name = constants.NATIONAL_NETWORK_DATASET_NAME
        db_schema = constants.DEFAULT_GEODATABASE_SCHEMA
        feature_class_prefix = f'{db_schema}.' if self.output_format == constants.OUT_FORMAT['SDE'] else ''

        associated_data = (
            f'{feature_class_prefix}{street_name} FeatureClass {street_name} #;'
            f'{feature_class_prefix}{node_name} FeatureClass {node_name} #;'
            f'{feature_class_prefix}{signpost_name} FeatureClass {signpost_name} #;'
            f'{feature_class_prefix}{turn_name} FeatureClass {turn_name} #;'
            f'{feature_class_prefix}{dataset_name}_Junctions FeatureClass {dataset_name}_Junctions #;'
            f'{feature_class_prefix}{dataset_name} NetworkDataset {dataset_name} #;'
            f'{feature_class_prefix}{signpost_table_name} TableDataset {signpost_table_name} #'
        )
        arcpy.management.Copy(
            in_data=dataset,
            out_data=scratch_network_dataset,
            data_type='FeatureDataset',
            associated_data=associated_data
        )

    @NationalMapLogger.debug_decorator
    def _generate_dissolved_network_dataset(self):
        result = arcpy.management.CreateFileGDB(self.out_geodatabase_folder, self.dissolve_network_file_gdb_name)
        dissolve_network_location = result.getOutput(0)
        network_dataset = os.path.join(self.scratch_network_dataset, constants.NATIONAL_NETWORK_DATASET_NAME)

        result = arcpy.na.DissolveNetwork(network_dataset, dissolve_network_location)
        dissolve_network_dataset = result.getOutput(0)

        build_network_dataset(dissolve_network_dataset)

    def run(self):
        if check_out_network_analyst_extension_license():
            self._create_network_dataset()
            self._copy_network_dataset()
            self._generate_dissolved_network_dataset()
            check_in_network_analyst_extension_license()
