import os

import constants
from map_convertor_configuration import MapConvertorConfiguration
from file_geodatabase import FileGeodatabase
from national_landmarks_factory import NationalLandmarksFactory

from national_mobile_map_package_factory import NationalMobileMapPackageFactory
from national_map_logger import NationalMapLogger
from enterprise_geodatabase import EnterpriseGeodatabase
from precisely_data_extract import PreciselyDataExtract
from state_data_settings import StateDataSettings
from state_exporter import StateExporter
from state_street_converter import StateStreetConverter
from state_node_converter import StateNodeConverter
from state_restriction_converter import StateRestrictionConverter
from state_signpost_converter import StateSignpostConverter
from national_data_importer import NationalDataImporter
from national_restriction_turn_factory import NationalRestrictionTurnFactory
from national_signpost_factory import NationalSignpostFactory
from national_network_factory import NationalNetworkFactory
from national_locator_factory import NationalLocatorFactory


def convert_state_data_for_national(state, configuration):
    message = f'convert_state_data_for_national, {state}'
    NationalMapLogger.info(message)

    precisely_data_extract = PreciselyDataExtract(state, configuration)
    precisely_data_extract.run()

    state_data_settings = StateDataSettings(state, configuration)
    state_exporter = StateExporter(state_data_settings)
    state_exporter.run()

    street_converter = StateStreetConverter(state_data_settings, state_exporter)
    street_converter.run()
    street_data = street_converter.data

    restriction_converter = StateRestrictionConverter(state_data_settings, state_exporter, street_data)
    restriction_converter.run()

    signpost_convert = StateSignpostConverter(state_data_settings, state_exporter, street_data)
    signpost_convert.run()

    node_converter = StateNodeConverter(state_data_settings, state_exporter, street_data)
    node_converter.run()

    precisely_data_extract.dispose()


def generate_national_enterprise_geodatabase(configuration):
    enterprise_geodatabase = EnterpriseGeodatabase(configuration)
    enterprise_geodatabase.run()

    sde_connection = enterprise_geodatabase.get_sde_connection()
    _generate_national_data(configuration, sde_connection)


def generate_national_file_geodatabase(configuration):
    file_geodatabase = FileGeodatabase(configuration)
    file_geodatabase.run()

    file_gdb_path = file_geodatabase.get_file_geodatabase()
    _generate_national_data(configuration, file_gdb_path)

    locator_factory = NationalLocatorFactory(configuration, file_gdb_path)
    locator_factory.run()

    network_factory = NationalNetworkFactory(configuration, file_gdb_path)
    network_factory.run()


def _generate_national_data(configuration, workspace):
    national_importer = NationalDataImporter(configuration, workspace)
    national_importer.run()

    restriction_turn_factory = NationalRestrictionTurnFactory(workspace)
    restriction_turn_factory.run()

    signpost_factory = NationalSignpostFactory(configuration, workspace)
    signpost_factory.run()

    landmarks_factory = NationalLandmarksFactory(configuration, workspace)
    landmarks_factory.run()


def main():
    configuration_file = os.path.join('config', 'national_configuration.xml')
    configuration = MapConvertorConfiguration(configuration_file)
    NationalMapLogger.init(configuration)
    MapConvertorConfiguration.set_arcpy_environment()
    NationalMapLogger.info('---------- Start ----------')

    output_states = configuration.data['Outputs']['states']
    for state in output_states:
        convert_state_data_for_national(state, configuration)

    output_format = configuration.data['Outputs']['format']
    if output_format == constants.OUT_FORMAT['SDE']:
        generate_national_enterprise_geodatabase(configuration)
    elif output_format == constants.OUT_FORMAT['FILE_GDB']:
        generate_national_file_geodatabase(configuration)

        national_mobile_map_package_factory = NationalMobileMapPackageFactory(configuration)
        national_mobile_map_package_factory.run()

    NationalMapLogger.info('---------- Completed ----------')


if __name__ == '__main__':
    main()
