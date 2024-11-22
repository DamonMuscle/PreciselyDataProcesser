import os


from map_convertor_configuration import MapConvertorConfiguration
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
from national_locator_factory import NationalLocatorFactory


def main():
    configuration_file = f'config{os.sep}national_configuration.xml'
    configuration = MapConvertorConfiguration(configuration_file)
    NationalMapLogger.init(configuration)
    MapConvertorConfiguration.set_arcpy_environment()
    NationalMapLogger.info('---------- Start ----------')

    enterprise_geodatabase = EnterpriseGeodatabase(configuration)
    enterprise_geodatabase.run()

    output_states = configuration.data['Outputs']['states']
    for state in output_states:
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

    sde_connection = enterprise_geodatabase.get_sde_connection()
    national_importer = NationalDataImporter(configuration, sde_connection)
    national_importer.run()

    restriction_turn_factory = NationalRestrictionTurnFactory(sde_connection)
    restriction_turn_factory.run()

    signpost_factory = NationalSignpostFactory(sde_connection)
    signpost_factory.run()

    locator_factory = NationalLocatorFactory(configuration, sde_connection)
    locator_factory.run()

    NationalMapLogger.info('---------- Completed ----------')


if __name__ == '__main__':
    main()
