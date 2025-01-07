from string import Template
import arcpy


from national_gdb_data_factory import NationalGDBDataFactory
from national_map_utility import NationalMapUtility
from national_map_logger import NationalMapLogger
import constants


class NationalLocatorFactory(NationalGDBDataFactory):
    def __init__(self, configuration, workspace):
        super().__init__(workspace)
        self.configuration = configuration
        self.locator = None

    def __del__(self):
        del self.configuration
        del self.locator

    def _init(self):
        out_locator_folder = self.configuration.data['Outputs']['locator_folder']
        NationalMapUtility.ensure_path_exists(out_locator_folder)
        self.locator = self.configuration.data['Outputs']['locator']

    @NationalMapLogger.debug_decorator
    def _create_locator(self):
        arcpy.env.workspace = self._get_dataset()
        address_type = 'StreetAddress'

        street_name = constants.GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name']
        reference_data = f'{street_name} {address_type}'
        field_mapping_template = (
            "'$type.FEATURE_ID $source.LocalId';"
            "'$type.HOUSE_NUMBER_FROM_LEFT $source.Fromleft';"
            "'$type.HOUSE_NUMBER_TO_LEFT $source.Toleft';"
            "'$type.HOUSE_NUMBER_FROM_RIGHT $source.Fromright';"
            "'$type.HOUSE_NUMBER_TO_RIGHT $source.Toright';"
            "'$type.STREET_NAME $source.Street';"
            "'$type.CITY_LEFT $source.City';"
            "'$type.CITY_RIGHT $source.City';"
            "'$type.REGION_LEFT $source.State';"
            "'$type.REGION_RIGHT $source.State';"
            "'$type.POSTAL_LEFT $source.LeftPostalCode';"
            "'$type.POSTAL_RIGHT $source.RightPostalCode';"
        )
        template_dict = {'type': address_type, 'source': street_name}
        t = Template(field_mapping_template)
        field_mapping = t.substitute(template_dict)

        arcpy.geocoding.CreateLocator(
            country_code=constants.COUNTY_CODE,
            primary_reference_data=reference_data,
            field_mapping=field_mapping,
            out_locator=self.locator,
            language_code=constants.LOCATOR_LANGUAGE_CODE,
            alternatename_tables=None,
            alternate_field_mapping=None,
            custom_output_fields=None,
            precision_type='GLOBAL_EXTRA_HIGH'
        )

        arcpy.env.workspace = None

    def run(self):
        self._init()
        self._create_locator()
