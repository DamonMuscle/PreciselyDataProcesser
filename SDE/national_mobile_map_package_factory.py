import os.path

import arcpy

import constants
from national_map_logger import NationalMapLogger
from national_map_utility import NationalMapUtility


def _update_layer_data_source(layer, database, dataset):
    try:
        layer_connection_properties = layer.connectionProperties
        layer_connection_properties['connection_info']['database'] = database
        layer_connection_properties['dataset'] = dataset
        layer.updateConnectionProperties(layer.connectionProperties, layer_connection_properties)
    except Exception as ex:
        NationalMapLogger.warning(f' failed: {layer.name}, database: {database}, source: {dataset}')


class NationalMobileMapPackageFactory:
    def __init__(self, configuration):
        output_configuration = configuration.data['Outputs']
        self.scratch_folder = configuration.get_scratch_folder()
        self.scratch_map_file = None
        self.scratch_map_package_project = None
        self.out_geodatabase_folder = configuration.get_geodatabase_folder()
        self.out_mobile_geodatabase_folder = output_configuration['mobile_geodatabase_folder']
        self.gdb_name = configuration.get_geodatabase_name()
        self.out_map_package = None

    def __del__(self):
        del self.scratch_folder
        del self.scratch_map_file
        del self.scratch_map_package_project
        del self.out_geodatabase_folder
        del self.out_mobile_geodatabase_folder
        del self.gdb_name
        del self.out_map_package

    @NationalMapLogger.debug_decorator
    def _create_scratch_map_file(self):
        project_template = os.path.join('templates', 'mobile_map_package_project_template.aprx')

        if not arcpy.Exists(project_template):
            NationalMapLogger.error(f'{project_template} not exists!  _create_scratch_map_file Failed!')
            return

        geodatabase = os.path.join(self.out_geodatabase_folder, f'{self.gdb_name}.gdb')
        if not arcpy.Exists(geodatabase):
            NationalMapLogger.error(f'{geodatabase} not exists!  _create_scratch_map_file Failed!')
            return

        scratch_map_file = None
        try:
            aprx = arcpy.mp.ArcGISProject(project_template)
            map = aprx.listMaps()[0]
            map.spatialReference = constants.SR_WEB_MERCATOR

            layers = map.listLayers()
            for layer in layers:
                layer_name = layer.name
                dataset = constants.MMPK_DATA_SOURCE[layer_name]
                _update_layer_data_source(layer, geodatabase, dataset)

            scratch_map_file = os.path.join(self.scratch_folder, 'mmpk_map.mapx')
            if arcpy.Exists(scratch_map_file):
                arcpy.management.Delete(scratch_map_file)

            map.exportToMAPX(scratch_map_file)

            scratch_map_package_project = os.path.join(self.scratch_folder, 'mmpk_out.aprx')
            if arcpy.Exists(scratch_map_package_project):
                arcpy.management.Delete(scratch_map_package_project)

            aprx.saveACopy(scratch_map_package_project)
            self.scratch_map_package_project = scratch_map_package_project

        except Exception as e:
            NationalMapLogger.error(f'_create_scratch_map_file Failed! {e}')
            return

        self.scratch_map_file = scratch_map_file

    @NationalMapLogger.debug_decorator
    def _create_mobile_map_package(self):
        if self.scratch_map_file is None:
            NationalMapLogger.error(f'{self.scratch_map_file} not exists!  _create_mobile_map_package Failed!')
            return

        out_map_package = os.path.join(self.scratch_folder, f'{self.gdb_name}.mmpk')
        if arcpy.Exists(out_map_package):
            arcpy.management.Delete(out_map_package)

        arcpy.management.CreateMobileMapPackage(
            in_map=self.scratch_map_file,
            output_file=out_map_package,
            extent='DEFAULT',
            title='NationalMap'
        )
        arcpy.management.Delete(self.scratch_map_file)
        arcpy.management.Delete(self.scratch_map_package_project)

        self.out_map_package = out_map_package

    def _extract_mobile_geodatabase(self):
        if self.out_map_package is None:
            return

        output_folder = os.path.join(self.out_mobile_geodatabase_folder, self.gdb_name)
        NationalMapUtility.ensure_path_exists(output_folder)

        arcpy.management.ExtractPackage(
            in_package=self.out_map_package,
            output_folder=output_folder,
            cache_package='NO_CACHE'
        )

    def run(self):
        self._create_scratch_map_file()
        self._create_mobile_map_package()
        self._extract_mobile_geodatabase()
