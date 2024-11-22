from string import Template
from arcgis.gis import GIS
import arcgisscripting as arcscript
import arcpy
import os
import xml.dom.minidom as DOM
import xml.etree.ElementTree as ET
import datetime
import logging
from logging.handlers import RotatingFileHandler


SCRIPT_VERSION = '20241021_1200'

#####################################################################
#region Global Parameters, Read from Configuration

converter_version = None
precisely_data_version = None
precisely_gdb_location = None

portal_url = None
portal_username = None
portal_password = None

server_admin_url = None
server_username = None
server_password = None

template_folder = None
network_dataset_template = None

out_GDB_folder_path = None
out_GDB_name = None
out_GDB = None

vector_tile_project_template_folder = None
mobile_map_package_project_template = None
blank_project_template = None
out_vector_tile_package_folder = None

out_locator_folder = None
out_locator_name = None
out_locator = None

gis_server_connection_file = None
out_dissolve_GDB = None

ADAPT_FOR_ROUTEFINDER_PLUS = None

out_log_folder = None
NATIONAL_LOG_LEVEL = None
NATIONAL_LOG_NAME = None
NATIONAL_LOG_FILE = None

SKIP_PROCESS = None

# Default Service Configuration
GEOCODE_SERVICE_CONFIGURATION = {
    'SERVICE_NAME': 'StreetGeocodeService',
    'MIN_INSTANCES': 5,
    'MAX_INSTANCES': 20,
    'WAIT_TIMEOUT': 600
}

MAP_SERVICE_CONFIGURATION = {
    'SERVICE_NAME': 'MapEditingOneService',
    'MIN_INSTANCES': 5,
    'MAX_INSTANCES': 20,
    'WAIT_TIMEOUT': 600
}

#endregion
#####################################################################
#region National Map Environment Variables

convert_to_web_mercator = True

SR_WEB_MERCATOR = arcpy.SpatialReference(3857)
SR_WGS_1984 = arcpy.SpatialReference(4326)
NATIONAL_SPATIAL_REFERENCE = SR_WEB_MERCATOR if convert_to_web_mercator else SR_WGS_1984

## arcpy environment variables
env_maintain_spatial_index = True
env_output_coordinate_system = NATIONAL_SPATIAL_REFERENCE
env_output_M_flag = 'Disabled'
env_output_Z_flag = 'Disabled'
env_overwrite_output = True
env_processor_type = 'CPU'
env_parallel_processing_factor = '80%'
env_workspace = ''
env_XY_tolerance = '0.0000000001 Degree'

## basic information

UNNAMED_STREET_NAME = '"Unnamed"'
RAMP_STREET_NAME = '"Ramp"'

SIGNPOST_DESTINATIONS_TABLE_SUFFIX = 'signpostdestinations'
SIGNPOST_FEATURE_SUFFIX = 'signposts'

US_STATES = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA', 'DE',
            'MD', 'DC', 'OH', 'WV', 'VA', 'NC', 'SC', 'MI', 'IN', 'KY',
            'TN', 'GA', 'AL', 'FL', 'MS', 'WI', 'IL', 'MN', 'IA', 'MO',
            'AR', 'LA', 'ND', 'SD', 'NE', 'KS', 'OK', 'TX', 'MT', 'WY',
            'CO', 'NM', 'ID', 'UT', 'AZ', 'WA', 'OR', 'NV', 'CA', 'AK',
            'HI']

VECTOR_CATEGORY = ['counties', 'waterbodies', 'rivers', 'railroads', 'landuse', 'landmarks',
                   'airports', 'postcodes', 'towns']
PORTAL_CONTENT_FOLDER = 'nationalmapsvectortile'


vector_project_name = {
    'MC': ['national_towns_project'],
    'PC': ['national_postcodes_project'],
    'Railroads': ['national_railroads_project'],
    'Streets': ['national_map_streets_project'],
    'Water': ['national_rivers_project',
              'national_waterbodies_project'],
    'Landmarks': ['national_landmarks_project',
                  'national_landmarks_polyline_project',
                  'national_landmarks_polygon_project']
}

out_dataset_name = 'RoutingND'
out_dataset_spatial_reference = NATIONAL_SPATIAL_REFERENCE

out_national_feature_class_prefix = 'national_map'
out_national_street_nodes = 'national_map_street_nodes'


national_map_streets = 'national_map_streets'
national_map_nodes = 'national_map_nodes'

out_turn_feature_class = 'national_map_turns'
out_turn_maximum_edges = 5

out_signposts_feature_class_name = 'national_signposts'
out_signposts_table_name = 'national_signposts_streets'
out_signposts_skip_table_name = 'national_signposts_skip'
out_signposts_maximum_edges = 5

national_map_restrictions = 'national_map_restrictions'
national_streets = 'national_streets'
national_streets_ID = None

batch_insert_turn_features_size = 50000
batch_insert_signpost_features_size = 5000

out_street_polygon_feature_class = 'national_street_polygon'

national_map_street_nodes = f'{out_national_street_nodes}_project' if convert_to_web_mercator else out_national_street_nodes
national_street_nodes = 'national_street_nodes'


out_server_file_name = 'arcgis_server_connection.ags'


SERVER_FOLDER_NAME = 'NationalMaps'

out_network_dataset = 'national_routing_ND'

out_junctions_name = 'Junctions'
out_street_railroads_intersector_name = 'STREETINTERSECTR'

out_map_service_project_name = 'national_map_service'

logger = None


MMPK_DATA_SOURCE = {
    'Map_Turn': out_turn_feature_class,
    'MAP_STREET': national_streets,
    'STREETINTERSECTR': out_street_railroads_intersector_name,
    'routing_ND_Junctions': f'{out_network_dataset}_Junctions',
    'StreetPolygon': out_street_polygon_feature_class,
    'national_routing_ND': out_network_dataset
}


#endregion
#####################################################################
# Debug Configuration

DEBUG_MODE = True

US_REGION = {
    'NORTH_EAST': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],  # 9
    'MID_EAST': ['DE', 'MD', 'DC', 'WV', 'VA', 'NC', 'KY', 'TN'],          # 8
    'SOURCE_EAST': ['SC', 'GA', 'AL', 'FL', 'MS', 'AR', 'LA', 'OK', 'TX'], # 9
    'MID_WEST': ['OH', 'MI', 'IN', 'WI', 'IL', 'MN', 'IA', 'MO'],          # 8
    'MOUNTAIN_PRAIRIE': ['ND', 'SD', 'NE', 'KS', 'MT', 'WY', 'CO', 'UT'],  # 8
    'SOURCE_WEST': ['NM', 'AZ', 'NV', 'CA', 'HI'],                         # 5
    'NORTH_WEST': ['ID', 'WA', 'OR', 'AK']                                 # 4
}

if DEBUG_MODE:
    # US_STATES = US_REGION['NORTH_EAST']  # 5 hours 51 minutes 53 seconds
    US_STATES = ['NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA']
    # US_STATES = ['RI']
    # US_STATES = ['NY']
    pass


#####################################################################
#region Configuration

def read_configuration():
    configuration_file = r'D:\GISWorkspace\Templates\National_Map_Configuration.xml'
    tree = ET.parse(configuration_file)
    root = tree.getroot()

    read_precisely_configuration(root)
    read_arcgis_configuration(root)
    read_templates_configuration(root)
    read_logging_configuration(root)
    read_outputs_configuration(root)
    read_adaptor_configuration(root)
    read_debug_configuration(root)


def read_precisely_configuration(root):
    global precisely_data_version, precisely_gdb_location
    precisely_element = root.find('Precisely')
    precisely_data_version = precisely_element.attrib['data-version']
    precisely_gdb_location = precisely_element.attrib['gdb-data-location']


def read_arcgis_configuration(root):
    global portal_url, portal_username, portal_password
    global server_admin_url, server_username, server_password
    environment_element = root.find('Environment')

    # Environment > ArcGIS
    arcgis_element = environment_element.find('ArcGIS')

    portal_element = arcgis_element.find('Portal')
    portal_url = portal_element.attrib['url']
    portal_username = portal_element.attrib['user-name']
    portal_password = portal_element.attrib['password']

    server_element = arcgis_element.find('Server')
    server_admin_url = server_element.attrib['admin-url']
    server_username = server_element.attrib['user-name']
    server_password = server_element.attrib['password']


def read_templates_configuration(root):
    global template_folder, network_dataset_template, vector_tile_project_template_folder
    global mobile_map_package_project_template, blank_project_template
    environment_element = root.find('Environment')
    converter_element = environment_element.find('Converter')

    # Environment > Converter > Templates
    templates_element = converter_element.find('Templates')
    template_folder = templates_element.attrib['location']
    
    nd_template_element = templates_element.find('NDTemplate')
    network_dataset_template_name = nd_template_element.attrib['name']
    network_dataset_template = fr'{template_folder}\{network_dataset_template_name}'
    
    vector_tile_element = templates_element.find('VectorTile')
    vector_tile_folder_name = vector_tile_element.attrib['folder-name']
    vector_tile_project_template_folder = fr'{template_folder}\{vector_tile_folder_name}'
    
    mobile_map_package_element = templates_element.find('MMPKTemplate')
    mobile_map_package_project_file = mobile_map_package_element.attrib['project-file']
    mobile_map_package_project_template = fr'{template_folder}\{mobile_map_package_project_file}'
    
    bland_project_element = templates_element.find('BlankTemplate')
    blank_project_file = bland_project_element.attrib['project-file']
    blank_project_template = fr'{template_folder}\{blank_project_file}'


def read_outputs_configuration(root):
    global converter_version
    global out_GDB_folder_path, out_GDB_name, out_GDB, out_vector_tile_package_folder
    global out_locator_folder, out_locator_name, out_locator
    global gis_server_connection_file
    global out_log_folder, NATIONAL_LOG_FILE
    global out_dissolve_GDB

    environment_element = root.find('Environment')
    converter_element = environment_element.find('Converter')
    converter_version = converter_element.attrib['version']
    
    # Environment > Converter > Outputs
    outputs_element = converter_element.find('Outputs')
    gdb_element = outputs_element.find('GDB')
    out_GDB_folder_path = gdb_element.attrib['location']
    name = gdb_element.attrib['name']
    GDB_name = f'{name}_{precisely_data_version}'
    GDB_with_version = gdb_element.attrib['with-version'].lower() == 'true'
    out_GDB_name = f'{GDB_name}_{converter_version}' if GDB_with_version else GDB_name
    out_GDB = fr'{out_GDB_folder_path}\{out_GDB_name}.gdb'
    
    vector_tile_element = outputs_element.find('VectorTile')
    vector_tile_folder_name = vector_tile_element.attrib['folder-name']
    out_vector_tile_package_folder = fr'{out_GDB_folder_path}\{vector_tile_folder_name}'

    locator_element = outputs_element.find('Locator')
    locator_folder = locator_element.attrib['folder-name']
    out_locator_folder = fr'{out_GDB_folder_path}\{locator_folder}'

    out_locator_name = locator_element.attrib['name']
    out_locator = fr'{out_locator_folder}\{out_locator_name}'
    
    gis_server_connection_file = fr'{out_GDB_folder_path}\{out_server_file_name}'
    out_log_folder = fr'{out_GDB_folder_path}\Logs'
    NATIONAL_LOG_FILE = fr'{out_log_folder}\{NATIONAL_LOG_NAME}.log'
    
    out_dissolve_GDB = f'{out_GDB_name}_Dissolved'


def read_adaptor_configuration(root):
    global ADAPT_FOR_ROUTEFINDER_PLUS
    adaptor_element = root.find('Adaptor')
    support_routefinder_plus = adaptor_element.attrib['support-routefinder-plus']
    ADAPT_FOR_ROUTEFINDER_PLUS = support_routefinder_plus.lower() == 'true'


def read_logging_configuration(root):
    global NATIONAL_LOG_LEVEL, NATIONAL_LOG_NAME
    logging_element = root.find('Logging')

    logging_level_element = logging_element.find('Level')
    NATIONAL_LOG_LEVEL = logging_level_element.text.upper()

    logging_file_name_element = logging_element.find('FileName')
    NATIONAL_LOG_NAME = logging_file_name_element.text


def read_debug_configuration(root):
    global DEBUG_MODE, SKIP_PROCESS
    debug_mode_element = root.find('DebugMode')
    debug_activate = debug_mode_element.attrib['activate']
    DEBUG_MODE = debug_activate.lower() == 'true'
    SKIP_PROCESS = {}

    if DEBUG_MODE:
        progresses_element = debug_mode_element.find('Processes')
        for progress_element in progresses_element.findall('Process'):
            progress_name = progress_element.get('name')
            progress_skip = progress_element.get('skip').lower() == 'true'
            SKIP_PROCESS[progress_name] = progress_skip


#endregion
#####################################################################
#region Environments

def setup_environment():
    logger.info('\n======================================== Started ========================================\n')

    message = f'0. setup_environment version: {converter_version}'
    show_message(message)

    arcpy.env.maintainSpatialIndex = env_maintain_spatial_index
    arcpy.env.outputCoordinateSystem = env_output_coordinate_system
    arcpy.env.outputMFlag = env_output_M_flag
    arcpy.env.outputZFlag = env_output_Z_flag
    arcpy.env.overwriteOutput = env_overwrite_output
    arcpy.env.processorType = env_processor_type
    arcpy.env.parallelProcessingFactor = env_parallel_processing_factor
    arcpy.env.XYTolerance = env_XY_tolerance

#endregion
#####################################################################
#region Processing Functions

def create_out_GDB():
    if is_skip_process('create_out_GDB'):
        return
    
    ensure_folder_exists(out_GDB_folder_path)

    if arcpy.Exists(out_GDB):
        arcpy.management.Delete(out_GDB)

    arcpy.management.CreateFileGDB(out_GDB_folder_path, out_GDB_name)


def combine_state_data_to_national():
    process_name = 'combine_state_data_to_national'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'1. {process_name}'
    show_message(message)

    set_arcpy_workspace(out_GDB)

    generate_national_feature_class('streets')
    generate_national_feature_class('restrictions')
    generate_national_feature_class('nodes')

    arcpy.ResetProgressor()
    stop_log_process(process_name)


def process_national_data():
    process_name = 'process_national_data'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'2. {process_name}'
    show_message(message)

    set_arcpy_workspace(out_GDB)

    process_national_streets()
    process_national_nodes()

    arcpy.ResetProgressor()
    if convert_to_web_mercator:
        project_national_data()

    arcpy.ResetProgressor()
    stop_log_process(process_name)


def prepare_routing_dataset():
    process_name = 'prepare_routing_dataset'
    if is_skip_process(process_name):
        return
    
    start_log_process(process_name)

    message = f'3. {process_name}'
    show_message(message)
    
    set_arcpy_workspace(out_GDB)

    create_feature_dataset(out_GDB, out_dataset_name, out_dataset_spatial_reference)

    streets_feature_class = get_project_name(national_map_streets) if convert_to_web_mercator else national_map_streets
    copy_national_streets(streets_feature_class)

    stop_log_process(process_name)


def process_national_restrictions():
    process_name = 'process_national_restrictions'
    if is_skip_process('process_national_restrictions'):
        return

    start_log_process(process_name)

    set_arcpy_workspace(out_GDB)

    count = query_count(national_map_restrictions)
    message = f'4. {process_name}, feature_count: {count}'
    show_message(message)
    
    if national_streets_ID == None:
        set_national_streets_ID()

    create_restrictions_turn_feature_class(out_GDB, out_dataset_name, out_turn_feature_class)

    extract_prohibited_turns(national_map_restrictions, out_turn_feature_class, national_streets)

    stop_log_process(process_name)


def process_national_signposts():
    process_name = 'process_national_signposts'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'5. {process_name}'
    show_message(message)

    if national_streets_ID == None:
        set_national_streets_ID()

    set_arcpy_workspace(out_GDB)

    create_national_signposts_feature_class()
    create_national_signposts_table()

    generate_national_signposts()

    add_signposts_table_index()
    
    rename_street_feature_id()

    arcpy.ResetProgressor()
    stop_log_process(process_name)


def process_vector_data():
    process_name = 'process_vector_data'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'6. {process_name}'
    show_message(message)
    
    set_arcpy_workspace(out_GDB)
    
    for category in VECTOR_CATEGORY:
        process_vector_by_category(category)

    county_code_dict = create_memory_county_code_dict()
    
    arcpy.ResetProgressor()

    create_national_landmarks()
    process_national_railroads()
    process_national_towns(county_code_dict)
    process_national_postcodes()
    process_national_waters()
    
    del county_code_dict

    arcpy.ResetProgressor()
    stop_log_process(process_name)


def process_locator():
    process_name = 'process_locator'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'7. {process_name}'
    show_message(message)

    create_street_address_locator()
    stop_log_process(process_name)


def process_network_dataset():
    process_name = 'process_network_dataset'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'8. {process_name}'
    show_message(message)

    prepare_network_data()
    create_and_build_network_dataset()
    dissolve_network_dataset()
    stop_log_process(process_name)
    

def process_mobile_map_package():
    process_name = 'process_mobile_map_package'
    if is_skip_process(process_name):
        return

    start_log_process(process_name)

    message = f'9. {process_name}'
    show_message(message)
    
    set_arcpy_workspace(out_GDB)

    create_t_junctions()
    create_street_intersect()
    generate_street_polygons()
    prepare_mobile_map_package_data()
    create_mobile_map_package()
    stop_log_process(process_name)


def clear_workspace():
    logger.info('\n======================================== Completed ========================================\n')

    close_logger()


#endregion
#####################################################################
#region Append State Data


def generate_national_feature_class(category):
    states = [state.lower() for state in US_STATES]
    
    is_streets_feature_class = category == 'streets'

    total_count = len(states)
    count = 0
    feature_count = 0
    func_name = ''
    set_progress_label(func_name, category, count, total_count, feature_count)
    
    # copy first state as national target data
    first_state = states[0]
    target_feature_class = copy_first_state_as_append_target(first_state, category)
    
    if is_streets_feature_class:
        progress = f'({count + 1}/{total_count})'
        temp_target_feature_class = process_street_state_and_county(first_state, target_feature_class, progress)
        arcpy.management.CopyFeatures(temp_target_feature_class, target_feature_class)
        arcpy.management.Delete(temp_target_feature_class)

    count += 1
    feature_count = query_count(target_feature_class)
    set_progress_label(func_name, category, count, total_count, feature_count)

    for state in states[1:]:
        state_gdb_file = get_state_gdb_file(state)
        if arcpy.Exists(state_gdb_file):
            append_inputs = fr'{state_gdb_file}/usa_{state}_{category}'
            temp_append_inputs = None
            if is_streets_feature_class:
                progress = f'({count + 1}/{total_count})'
                temp_append_inputs = process_street_state_and_county(state, append_inputs, progress)
                append_inputs = temp_append_inputs

            arcpy.management.Append(append_inputs, target_feature_class, 'TEST')
            
            if is_streets_feature_class and temp_append_inputs != None:
                arcpy.management.Delete(temp_append_inputs)

        count += 1
        feature_count = query_count(target_feature_class)
        set_progress_label(func_name, category, count, total_count, feature_count)


def get_progress_label(func_name, category, step_num, total_num, feature_count):
    return f'{func_name} {category} feature count: {feature_count} ({step_num}/{total_num})'


def set_progress_label(func_name, category, step_num, total_num, feature_count):
    label = get_progress_label(func_name, category, step_num, total_num, feature_count)
    set_arcpy_progressor_label(label)


def copy_first_state_as_append_target(first_state, category):
    state_gdb_file = get_state_gdb_file(first_state)
    copy_inputs = fr'{state_gdb_file}/usa_{first_state}_{category}'

    national_feature_class = f'{out_national_feature_class_prefix}_{category}'
    arcpy.management.CopyFeatures(copy_inputs, national_feature_class)

    return national_feature_class


def output_national_feature_count(feature_class):
    feature_count = query_count(feature_class)
    message = f'{feature_class} count: {feature_count}'
    show_message(message)


def process_street_state_and_county(state, feature_class, progress):
    label = f'- process_street_state_and_county: {state} {progress}'
    set_arcpy_progressor_label(label)

    state_gdb_file = get_state_gdb_file(state)
    towns_feature_class = fr'{state_gdb_file}/{state}towns'
    street_name = f'usa_{state}_streets'
    tmp_feature_class_spatial_join = fr'memory\{street_name}_sj'
    field_mapping = (
        f'STREET "STREET" true true false 100 Text 0 0,First,#,{feature_class},STREET,0,100;'
        f'STREET2 "STREET2" true true false 100 Text 0 0,First,#,{feature_class},STREET2,0,100;'
        f'STREET3 "STREET3" true true false 100 Text 0 0,First,#,{feature_class},STREET3,0,100;'
        f'STREET4 "STREET4" true true false 100 Text 0 0,First,#,{feature_class},STREET4,0,100;'
        f'FROMLEFT "FROMLEFT" true true false 4 Long 0 0,First,#,{feature_class},FROMLEFT,-1,-1;'
        f'TOLEFT "TOLEFT" true true false 4 Long 0 0,First,#,{feature_class},TOLEFT,-1,-1;'
        f'FROMRIGHT "FROMRIGHT" true true false 4 Long 0 0,First,#,{feature_class},FROMRIGHT,-1,-1;'
        f'TORIGHT "TORIGHT" true true false 4 Long 0 0,First,#,{feature_class},TORIGHT,-1,-1;'
        f'L_STRUCT "L_STRUCT" true true false 4 Long 0 0,First,#,{feature_class},L_STRUCT,-1,-1;'
        f'R_STRUCT "R_STRUCT" true true false 4 Long 0 0,First,#,{feature_class},R_STRUCT,-1,-1;'
        f'A1_LEFT "A1_LEFT" true true false 50 Text 0 0,First,#,{feature_class},A1_LEFT,0,50;'
        f'A1_RIGHT "A1_RIGHT" true true false 50 Text 0 0,First,#,{feature_class},A1_RIGHT,0,50;'
        f'LOCALITY_LEFT "LOCALITY_LEFT" true true false 50 Text 0 0,First,#,{feature_class},LOCALITY_LEFT,0,50;'
        f'LOCALITY_CODE_LEFT "LOCALITY_CODE_LEFT" true true false 50 Text 0 0,First,#,{feature_class},LOCALITY_CODE_LEFT,0,50;'
        f'LOCALITY_RIGHT "LOCALITY_RIGHT" true true false 50 Text 0 0,First,#,{feature_class},LOCALITY_RIGHT,0,50;'
        f'LOCALITY_CODE_RIGHT "LOCALITY_CODE_RIGHT" true true false 50 Text 0 0,First,#,{feature_class},LOCALITY_CODE_RIGHT,0,50;'
        f'PC_LEFT "PC_LEFT" true true false 10 Text 0 0,First,#,{feature_class},PC_LEFT,0,10;'
        f'PNAM_LEFT "PNAM_LEFT" true true false 50 Text 0 0,First,#,{feature_class},PNAM_LEFT,0,50;'
        f'PC_RIGHT "PC_RIGHT" true true false 10 Text 0 0,First,#,{feature_class},PC_RIGHT,0,10;'
        f'PNAM_RIGHT "PNAM_RIGHT" true true false 50 Text 0 0,First,#,{feature_class},PNAM_RIGHT,0,50;'
        f'FCODE "FCODE" true true false 4 Long 0 0,First,#,{feature_class},FCODE,-1,-1;'
        f'ROAD_CLASS "ROAD_CLASS" true true false 2 Text 0 0,First,#,{feature_class},ROAD_CLASS,0,2;'
        f'ROAD_TYPE "ROAD_TYPE" true true false 2 Text 0 0,First,#,{feature_class},ROAD_TYPE,0,2;'
        f'AREA_TYPE "AREA_TYPE" true true false 2 Text 0 0,First,#,{feature_class},AREA_TYPE,0,2;'
        f'LENGTH "LENGTH" true true false 8 Double 0 0,First,#,{feature_class},LENGTH,-1,-1;'
        f'SURFACE_TYPE "SURFACE_TYPE" true true false 4 Long 0 0,First,#,{feature_class},SURFACE_TYPE,-1,-1;'
        f'SPEED "SPEED" true true false 4 Long 0 0,First,#,{feature_class},SPEED,-1,-1;'
        f'SPEED_VERIFIED "SPEED_VERIFIED" true true false 4 Long 0 0,First,#,{feature_class},SPEED_VERIFIED,-1,-1;'
        f'SPEED_AMPEAK "SPEED_AMPEAK" true true false 8 Double 0 0,First,#,{feature_class},SPEED_AMPEAK,-1,-1;'
        f'SPEED_PMPEAK "SPEED_PMPEAK" true true false 8 Double 0 0,First,#,{feature_class},SPEED_PMPEAK,-1,-1;'
        f'SPEED_INTERPEAK "SPEED_INTERPEAK" true true false 8 Double 0 0,First,#,{feature_class},SPEED_INTERPEAK,-1,-1;'
        f'SPEED_NIGHT "SPEED_NIGHT" true true false 8 Double 0 0,First,#,{feature_class},SPEED_NIGHT,-1,-1;'
        f'SPEED_SEVENDAY "SPEED_SEVENDAY" true true false 8 Double 0 0,First,#,{feature_class},SPEED_SEVENDAY,-1,-1;'
        f'ONEWAY "ONEWAY" true true false 4 Long 0 0,First,#,{feature_class},ONEWAY,-1,-1;'
        f'ROUGHRD "ROUGHRD" true true false 4 Long 0 0,First,#,{feature_class},ROUGHRD,-1,-1;'
        f'TOLL "TOLL" true true false 4 Long 0 0,First,#,{feature_class},TOLL,-1,-1;'
        f'START_NODE "START_NODE" true true false 36 Text 0 0,First,#,{feature_class},START_NODE,0,36;'
        f'END_NODE "END_NODE" true true false 36 Text 0 0,First,#,{feature_class},END_NODE,0,36;'
        f'ROUTE_NUM "ROUTE_NUM" true true false 10 Text 0 0,First,#,{feature_class},ROUTE_NUM,0,10;'
        f'LEVEL_BEG "LEVEL_BEG" true true false 4 Long 0 0,First,#,{feature_class},LEVEL_BEG,-1,-1;'
        f'LEVEL_END "LEVEL_END" true true false 4 Long 0 0,First,#,{feature_class},LEVEL_END,-1,-1;'
        f'MAX_HEIGHT "MAX_HEIGHT" true true false 8 Double 0 0,First,#,{feature_class},MAX_HEIGHT,-1,-1;'
        f'MAX_WIDTH "MAX_WIDTH" true true false 8 Double 0 0,First,#,{feature_class},MAX_WIDTH,-1,-1;'
        f'MAX_WEIGHT "MAX_WEIGHT" true true false 8 Double 0 0,First,#,{feature_class},MAX_WEIGHT,-1,-1;'
        f'FEATURE_ID "FEATURE_ID" true true false 36 Text 0 0,First,#,{feature_class},FEATURE_ID,0,36;'
        f'City "City" true true false 100 Text 0 0,First,#,{towns_feature_class},Name,0,99;'
        f'State "State" true true false 2 Text 0 0,First,#,{towns_feature_class},A1_Abbrev,0,1'
    )
    arcpy.analysis.SpatialJoin(
        target_features=feature_class,
        join_features=towns_feature_class,
        out_feature_class=tmp_feature_class_spatial_join,
        join_operation='JOIN_ONE_TO_ONE',
        join_type='KEEP_ALL',
        field_mapping=field_mapping,
        match_option='WITHIN'
    )
    arcpy.management.DeleteField(tmp_feature_class_spatial_join, ['Join_Count', 'TARGET_FID'])

    return tmp_feature_class_spatial_join


#endregion
#####################################################################
#region Update State Streets


def process_national_streets():
    count = arcpy.management.GetCount(national_map_streets)
    message = f'- process_national_streets, feature_count: {count}'
    show_message(message)
    
    # Exclude local roads
    streets_exclude_local_unimportant_roads(national_map_streets)
    
    # Exclude local nodes
    streets_exclude_local_unimportant_nodes(national_map_streets, national_map_nodes)

    # STREET
    streets_street(national_map_streets)
    
    # ADDRESS_RANGE
    streets_address_range(national_map_streets)

    # ROAD_CLASS
    streets_road_class(national_map_streets)
    
    # Hierarchy
    streets_hierarchy(national_map_streets)
    
    # ONEWAY
    streets_oneway(national_map_streets)
    
    # WALK_TIME, LEFT_TIME, RIGHT_TIME
    streets_time(national_map_streets)
    
    # Traversable
    streets_traversable(national_map_streets)
    
    streets_add_field(national_map_streets)
    
    streets_rename_field(national_map_streets)

    if ADAPT_FOR_ROUTEFINDER_PLUS:
        streets_consistent_with_plus(national_map_streets)


def streets_exclude_local_unimportant_roads(national_map_streets):
    message = f'-- streets_exclude_local_unimportant_roads'
    show_message(message)

    memory_streets_layer = fr'memory\{national_map_streets}_lyr'
    arcpy.management.MakeFeatureLayer(national_map_streets, memory_streets_layer)
    where_clause_exclude_ferry = "ROAD_CLASS = 'H'"
    arcpy.management.SelectLayerByAttribute(memory_streets_layer,
                                            where_clause=where_clause_exclude_ferry)

    arcpy.management.DeleteFeatures(memory_streets_layer)

    arcpy.management.Delete(memory_streets_layer)
    
    count = arcpy.management.GetCount(national_map_streets)
    message = f'-- process streets feature_count: {count}'
    set_arcpy_progressor_label(message)


def streets_exclude_local_unimportant_nodes(national_map_streets, national_map_nodes):
    message = f'-- streets_exclude_local_unimportant_nodes'
    show_message(message)

    memory_nodes_layer = fr'memory\{national_map_nodes}_lyr'
    arcpy.management.MakeFeatureLayer(national_map_nodes, memory_nodes_layer)

    arcpy.management.SelectLayerByLocation(
        in_layer=memory_nodes_layer,
        overlap_type='INTERSECT',
        select_features=national_map_streets,
        search_distance=None,
        selection_type='NEW_SELECTION',
        invert_spatial_relationship='INVERT'
    )
    arcpy.management.DeleteFeatures(memory_nodes_layer)

    arcpy.management.Delete(memory_nodes_layer)


def streets_street(streets_feature_class):
    field_name = 'STREET'
    message = f'-- process field: {field_name}'
    show_message(message)

    set_arcpy_progressor_label(f'calculate streets: {RAMP_STREET_NAME}')
    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause=f"{field_name} = '' AND (MOD(FCODE, 1000) = 10 OR MOD(FCODE, 1000) = 510)")
    arcpy.management.CalculateField(memory_streets_layer, field_name, RAMP_STREET_NAME)
    arcpy.management.Delete(memory_streets_layer)

    set_arcpy_progressor_label(f'calculate streets: {UNNAMED_STREET_NAME}')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause=f"{field_name} = ''")
    arcpy.management.CalculateField(memory_streets_layer, field_name, UNNAMED_STREET_NAME)
    arcpy.management.Delete(memory_streets_layer)


def streets_address_range(streets_feature_class):
    field_names = ['FROMLEFT', 'TOLEFT', 'FROMRIGHT', 'TORIGHT']
    message = f"-- process field: {', '.join(field_names)}"
    show_message(message)

    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'

    for field_name in field_names:
        set_arcpy_progressor_label(f'calculate {field_name}')
        arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause=f'{field_name} < 0')
        arcpy.management.CalculateField(memory_streets_layer, field_name, 0)
        arcpy.management.Delete(memory_streets_layer)


def streets_road_class(streets_feature_class):
    field_name = 'RoadClass'
    message = f'-- process field: {field_name}'
    show_message(message)

    add_field(streets_feature_class, field_name, 'SHORT')

    ## Default
    set_arcpy_progressor_label(f'calculate default {field_name} = 1')
    arcpy.management.CalculateField(streets_feature_class, field_name, 1)
    
    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'
    ## Highways
    set_arcpy_progressor_label(f'calculate Highways')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="ROAD_CLASS IN ('M','N','G','I')")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 2)
    arcpy.management.Delete(memory_streets_layer)
    
    ## Maj Roads
    set_arcpy_progressor_label(f'calculate Maj Roads')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="ROAD_CLASS IN ('S','T','P','Q')")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 6)
    arcpy.management.Delete(memory_streets_layer)
    
    ## Pedestrian
    set_arcpy_progressor_label(f'calculate Pedestrian')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="FCODE IN (26014,27014,27514,28014,28015,29016,28515,29116,29216) AND ROAD_CLASS = 'Z'")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 10)
    arcpy.management.Delete(memory_streets_layer)

    ## Ramps
    set_arcpy_progressor_label(f'calculate Ramps')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause='MOD(FCODE, 1000) = 10 OR MOD(FCODE, 1000) = 510')
    arcpy.management.CalculateField(memory_streets_layer, field_name, 3)
    arcpy.management.Delete(memory_streets_layer)

    ## Roundabouts
    set_arcpy_progressor_label(f'calculate Roundabouts')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause='MOD(FCODE, 1000) = 4')
    arcpy.management.CalculateField(memory_streets_layer, field_name, 5)
    arcpy.management.Delete(memory_streets_layer)

    ## Stairs
    set_arcpy_progressor_label(f'calculate Stairs')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause='FCODE = 28019')
    arcpy.management.CalculateField(memory_streets_layer, field_name, 12)
    arcpy.management.Delete(memory_streets_layer)


def streets_hierarchy(streets_feature_class):
    field_name = 'Hierarchy'
    message = f'-- process field: {field_name}'
    show_message(message)

    add_field(streets_feature_class, field_name, 'SHORT')

    ## Default
    set_arcpy_progressor_label(f'calculate DEFAULT {field_name}')
    arcpy.management.CalculateField(streets_feature_class, field_name, 5)

    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'

    ## ROAD_LEVEL
    set_arcpy_progressor_label(f'calculate {field_name} = 1')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="ROAD_CLASS IN ('M','N','G','I')")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 1)
    arcpy.management.Delete(memory_streets_layer)

    set_arcpy_progressor_label(f'calculate {field_name} = 2')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="ROAD_CLASS IN ('P','Q')")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 2)
    arcpy.management.Delete(memory_streets_layer)

    set_arcpy_progressor_label(f'calculate {field_name} = 3')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="ROAD_CLASS IN ('S','T')")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 3)
    arcpy.management.Delete(memory_streets_layer)

    set_arcpy_progressor_label(f'calculate {field_name} = 4')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause="ROAD_CLASS IN ('C','F')")
    arcpy.management.CalculateField(memory_streets_layer, field_name, 4)
    arcpy.management.Delete(memory_streets_layer)


def streets_oneway(streets_feature_class):
    message = '-- process field: ONEWAY'
    show_message(message)

    add_field(streets_feature_class, 'Speedleft', 'LONG')

    add_field(streets_feature_class, 'Speedright', 'LONG')
        
    ## Default
    set_arcpy_progressor_label('calculate DEFAULT SPEED')
    arcpy.management.CalculateField(streets_feature_class, 'Speedleft', '!SPEED!')
    arcpy.management.CalculateField(streets_feature_class, 'Speedright', '!SPEED!')
    
    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'
    ## FT
    set_arcpy_progressor_label('calculate Speedleft')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='ONEWAY = 2')
    arcpy.management.CalculateField(memory_streets_layer, 'Speedleft', 0)
    arcpy.management.Delete(memory_streets_layer)
    
    ## TF
    set_arcpy_progressor_label('calculate Speedright')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='ONEWAY = 3')
    arcpy.management.CalculateField(memory_streets_layer, 'Speedright', 0)
    arcpy.management.Delete(memory_streets_layer)


def streets_time(streets_feature_class):
    message = '-- process field: WALK_TIME, LEFT_TIME, RIGHT_TIME'
    show_message(message)
    
    add_field(streets_feature_class, 'WALK_TIME', 'DOUBLE')
    
    add_field(streets_feature_class, 'LEFT_TIME', 'DOUBLE')
    
    add_field(streets_feature_class, 'RIGHT_TIME', 'DOUBLE')
    
    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'
    
    set_arcpy_progressor_label('calculate WALK_TIME')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer)
    arcpy.management.CalculateField(memory_streets_layer, 'WALK_TIME', '!LENGTH! / 84')
    arcpy.management.Delete(memory_streets_layer)

    ## FT
    set_arcpy_progressor_label('calculate LEFT_TIME')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='Speedleft = 0')
    arcpy.management.CalculateField(memory_streets_layer, 'LEFT_TIME', 0)
    arcpy.management.Delete(memory_streets_layer)
    
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='Speedleft <> 0')
    arcpy.management.CalculateField(memory_streets_layer, 'LEFT_TIME', '(!LENGTH! / !Speedleft!) * 0.000621371192 * 60')
    arcpy.management.Delete(memory_streets_layer)

    ## TF
    set_arcpy_progressor_label('calculate RIGHT_TIME')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='Speedright = 0')
    arcpy.management.CalculateField(memory_streets_layer, 'RIGHT_TIME', 0)
    arcpy.management.Delete(memory_streets_layer)
    
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='Speedright <> 0')
    arcpy.management.CalculateField(memory_streets_layer, 'RIGHT_TIME', '(!LENGTH! / !Speedright!) * 0.000621371192 * 60')
    arcpy.management.Delete(memory_streets_layer)


def streets_traversable(streets_feature_class):
    field_name = 'Traversable'
    message = f'-- process field: {field_name}'
    show_message(message)

    add_field(streets_feature_class, field_name, 'SHORT')
    
    add_field(streets_feature_class, 'TraversableByVehicle', 'TEXT', field_length = 255)
    
    add_field(streets_feature_class, 'TraversableByWalkers', 'TEXT', field_length = 255)

    ## Default
    set_arcpy_progressor_label('calculate DEFAULT Traversable')
    arcpy.management.CalculateField(streets_feature_class, field_name, 1)

    set_arcpy_progressor_label('calculate Non-Traversable Segments')
    memory_streets_layer = fr'memory\{streets_feature_class}_lyr'
    ## Set Non-Traversable Segments
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer,
                                      where_clause='ONEWAY = 4 AND RoadClass IN (10, 12)')
    arcpy.management.CalculateField(memory_streets_layer, field_name, 0)
    arcpy.management.Delete(memory_streets_layer)

    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='ROUGHRD = 1')
    arcpy.management.CalculateField(memory_streets_layer, field_name, 0)
    arcpy.management.Delete(memory_streets_layer)
    
    ## TraversableByVehicle
    set_arcpy_progressor_label('calculate TraversableByVehicle')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='Traversable <> 1')
    arcpy.management.CalculateField(memory_streets_layer, 'TraversableByVehicle', '"F"')
    arcpy.management.Delete(memory_streets_layer)
    
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer, where_clause='Traversable = 1')
    arcpy.management.CalculateField(memory_streets_layer, 'TraversableByVehicle', '"T"')
    arcpy.management.Delete(memory_streets_layer)

    ## TraversableByWalkers
    set_arcpy_progressor_label('calculate TraversableByWalkers')
    arcpy.management.MakeFeatureLayer(streets_feature_class, memory_streets_layer)
    arcpy.management.CalculateField(memory_streets_layer, 'TraversableByWalkers', '"T"')
    arcpy.management.Delete(memory_streets_layer)


def streets_add_field(streets_feature_class):

    if add_field(streets_feature_class, 'PostedLeft', 'LONG'):
        # Default Value
        set_arcpy_progressor_label('calculate default value: PostedLeft')
        arcpy.management.CalculateField(streets_feature_class, 'PostedLeft', '!Speedleft!')

    if add_field(streets_feature_class, 'PostedRight', 'LONG'):
        # Default Value
        set_arcpy_progressor_label('calculate default value: PostedRight')
        arcpy.management.CalculateField(streets_feature_class, 'PostedRight', '!Speedright!')

    if add_field(streets_feature_class, 'fromtotofrom', 'TEXT', field_length = 5):
        # Default Value
        set_arcpy_progressor_label('calculate default value: fromtotofrom')
        arcpy.management.CalculateField(streets_feature_class, 'fromtotofrom', '!ONEWAY!')

    if add_field(streets_feature_class, 'WeightLimit', 'DOUBLE'):
        # Default Value
        set_arcpy_progressor_label('calculate default value: WeightLimit')
        arcpy.management.CalculateField(streets_feature_class, 'WeightLimit', '!MAX_WEIGHT!')

    if add_field(streets_feature_class, 'HeightClearance', 'DOUBLE'):
        # Default Value
        set_arcpy_progressor_label('calculate default value: HeightClearance')
        arcpy.management.CalculateField(streets_feature_class, 'HeightClearance', '!MAX_HEIGHT!')

    if add_field(streets_feature_class, 'LENGTH_GEO', 'DOUBLE'):
        # Default Value
        set_arcpy_progressor_label('calculate default value: LENGTH_GEO')
        arcpy.management.CalculateField(streets_feature_class, 'LENGTH_GEO', '!LENGTH!')

    if add_field(streets_feature_class, 'streettype', 'TEXT', field_length = 30):
        # Default Value
        set_arcpy_progressor_label('calculate default value: streettype')
        arcpy.management.CalculateField(streets_feature_class, 'streettype', '!FCODE!')

    if add_field(streets_feature_class, 'LeftPostalCode', 'TEXT', field_length = 10):
        # Default Value
        set_arcpy_progressor_label('calculate default value: LeftPostalCode')
        arcpy.management.CalculateField(streets_feature_class, 'LeftPostalCode', '!PC_LEFT![:5]')

    if add_field(streets_feature_class, 'RightPostalCode', 'TEXT', field_length = 10):
        # Default Value
        set_arcpy_progressor_label('calculate default value: RightPostalCode')
        arcpy.management.CalculateField(streets_feature_class, 'RightPostalCode', '!PC_RIGHT![:5]')

    if add_field(streets_feature_class, 'StateLeft', 'TEXT', field_length = 2):
        # Default Value
        set_arcpy_progressor_label('calculate default value: StateLeft')
        arcpy.management.CalculateField(streets_feature_class, 'StateLeft', '!LOCALITY_CODE_LEFT![0:2]')

    if add_field(streets_feature_class, 'StateRight', 'TEXT', field_length = 2):
        # Default Value
        set_arcpy_progressor_label('calculate default value: StateRight')
        arcpy.management.CalculateField(streets_feature_class, 'StateRight', '!LOCALITY_CODE_RIGHT![0:2]')

    if not is_field_exists(streets_feature_class, 'ProhibitCrosser'):
        # Default Value
        set_arcpy_progressor_label('calculate default value: ProhibitCrosser')
        arcpy.management.AddField(streets_feature_class, 'ProhibitCrosser', 'SHORT', field_is_nullable='NULLABLE')
        arcpy.management.AssignDefaultToField(streets_feature_class, 'ProhibitCrosser', '0', clear_value='DO_NOT_CLEAR')
        arcpy.management.CalculateField(streets_feature_class, 'ProhibitCrosser', 0)


def streets_rename_field(streets_feature_class):
    message = '-- streets_rename_field'
    show_message(message)

    field_mapping = [
        {'from': 'PC_LEFT', 'to': 'Postcode_Left'},
        {'from': 'PC_RIGHT', 'to': 'Postcode_Right'},
        {'from': 'PNAM_LEFT', 'to': 'PostcodeName_Left'},
        {'from': 'PNAM_RIGHT', 'to': 'PostcodeName_Right'},
        {'from': 'LEVEL_BEG', 'to': 'FromElevation'},
        {'from': 'LEVEL_END', 'to': 'ToElevation'}
    ]

    rename_fields(streets_feature_class, field_mapping)


def streets_consistent_with_plus(streets_feature_class):
    message = '-- streets_consistent_with_plus'
    show_message(message)

    add_field(streets_feature_class, 'GroupID', 'DOUBLE')
    add_field(streets_feature_class, 'Style', 'TEXT', 255)
    add_field(streets_feature_class, 'Cfcc', 'TEXT', 255)
    add_field(streets_feature_class, 'Lock', 'TEXT', 255)
    add_field(streets_feature_class, 'Fow', 'SHORT')
    add_editable_fields(streets_feature_class)

    field_mapping = [
        {'from': 'STREET', 'to': 'STREET1'},
        {'from': 'FROMLEFT', 'to': 'FROMLEFT1'},
        {'from': 'TOLEFT', 'to': 'TOLEFT1'},
        {'from': 'FROMRIGHT', 'to': 'FROMRIGHT1'},
        {'from': 'TORIGHT', 'to': 'TORIGHT1'},
        {'from': 'ONEWAY', 'to': 'ONEWAY1'}
    ]
    rename_fields(streets_feature_class, field_mapping)
    
    field_mapping = [
        {'from': 'STREET1', 'to': 'Street'},
        {'from': 'FROMLEFT1', 'to': 'Fromleft'},
        {'from': 'TOLEFT1', 'to': 'Toleft'},
        {'from': 'FROMRIGHT1', 'to': 'Fromright'},
        {'from': 'TORIGHT1', 'to': 'Toright'},
        {'from': 'ONEWAY1', 'to': 'Oneway'}
    ]
    rename_fields(streets_feature_class, field_mapping)


#endregion
#####################################################################
#region Update State Street Nodes


def process_national_nodes():
    count = arcpy.management.GetCount(national_map_nodes)
    message = f'- process_national_nodes, feature_count: {count}'
    show_message(message)

    memory_nodes_layer = fr'memory\{national_map_nodes}_lyr'
    arcpy.management.MakeFeatureLayer(national_map_nodes, memory_nodes_layer, where_clause="VALENCE > 2")
    arcpy.management.CopyFeatures(memory_nodes_layer, out_national_street_nodes)
    arcpy.management.Delete(memory_nodes_layer)


#endregion
#####################################################################
#region Projection


def project_national_data():
    message = '- project_national_data'
    show_message(message)

    project_to_web_mercator(national_map_streets)
    project_to_web_mercator(national_map_restrictions)
    project_to_web_mercator(out_national_street_nodes)


def get_project_name(feature_class):
    return f'{feature_class}_project'


def project_to_web_mercator(in_dataset):
    message = f'-- project_to_web_mercator: {in_dataset}'
    set_arcpy_progressor_label(message)

    out_dataset = get_project_name(in_dataset)
    arcpy.management.Project(in_dataset, out_dataset, SR_WEB_MERCATOR)


#endregion
#####################################################################
#region National Feature Dataset


def create_feature_dataset(out_dataset_path, out_name, spatial_reference):

    if is_feature_dataset_exists(out_name):
        return
    
    set_arcpy_workspace(out_dataset_path)

    message = f'- create_feature_dataset: {out_name}'
    show_message(message)

    arcpy.management.CreateFeatureDataset(out_dataset_path, out_name, spatial_reference)


def copy_national_streets(streets_feature_class):
    message = '- copy_national_streets'
    show_message(message)
    
    in_features = fr'{out_GDB}\{streets_feature_class}'
    out_feature_class = fr'{out_GDB}\{out_dataset_name}\{national_streets}'

    arcpy.management.CopyFeatures(in_features, out_feature_class)


def set_national_streets_ID():
    global national_streets_ID

    national_streets_path = fr'{out_GDB}\{out_dataset_name}\{national_streets}'
    national_streets_ID = arcpy.Describe(national_streets_path).DSID
    message = f'- {national_streets} FCID: {national_streets_ID}'
    show_message(message)


#endregion
#####################################################################
#region Restrictions


def create_restrictions_turn_feature_class(out_GDB, feature_dataset_name, out_feature_class_name):

    set_arcpy_workspace(out_GDB)

    if is_turn_feature_exists(feature_dataset_name, out_feature_class_name):
        arcpy.management.Delete(out_feature_class_name)

    message = f'-- create_restrictions_turn_feature_class: {out_feature_class_name}'
    show_message(message)
    
    out_turn_location = fr'{out_GDB}\{out_dataset_name}'
    arcpy.na.CreateTurnFeatureClass(out_turn_location, out_feature_class_name, out_turn_maximum_edges)

    add_field(out_feature_class_name, 'RestrictionID', 'TEXT', 36)
    add_field(out_feature_class_name, 'ProhibitedTurnFlag', 'SHORT')
    add_field(out_feature_class_name, 'RestrictedTurnFlag', 'SHORT')


def extract_prohibited_turns(restrictions_feature_class, turn_feature_class, streets_feature_class):
    message = '-- extract_prohibited_turns'
    show_message(message)

    prohibited_maneuver_layer = f'{restrictions_feature_class}_lyr'
    arcpy.management.MakeFeatureLayer(restrictions_feature_class, prohibited_maneuver_layer,
                                      where_clause="RESTRICTION_TYPE = '8I' AND VEHICLE_TYPE = 0")
    
    message = '--- setup memory_streets_dict'
    show_message(message)

    streets_oid_feature_id_dict = create_memory_streets_dict(streets_feature_class)
    
    message = '--- search for prohibited_maneuver_layer'
    show_message(message)

    batch_insert_turn_features = []
    
    prohibited_maneuver_fields = ['RESTRICTION_ID', 'SEQUENCE_NUM', 'FEATURE_ID', 'SHAPE@']
    with arcpy.da.SearchCursor(prohibited_maneuver_layer, 
                               prohibited_maneuver_fields,
                               sql_clause = (None, 'ORDER BY RESTRICTION_ID, SEQUENCE_NUM') ) as cursor:
        process_restriction_id = None
        restrictions = []
        for row in cursor:
            restriction_id, sequence_num, feature_id, geometry = row[0], row[1], row[2], row[3]
            
            item = (sequence_num, feature_id, geometry)

            if process_restriction_id == None or process_restriction_id == restriction_id:
                process_restriction_id = restriction_id
                restrictions.append(item)
            else:
                turn_feature_record = convert_restriction_to_prohibited_record(process_restriction_id, restrictions,
                                                                               streets_oid_feature_id_dict)
                if turn_feature_record != None:
                    batch_insert_turn_features.append(turn_feature_record)
                if len(batch_insert_turn_features) % batch_insert_turn_features_size == 0:
                    batch_insert_prohibited_turns(turn_feature_class, batch_insert_turn_features)
                    batch_insert_turn_features = []
                restrictions = []
                process_restriction_id = restriction_id
                restrictions.append(item)

        turn_feature_record = convert_restriction_to_prohibited_record(process_restriction_id, restrictions,
                                                                       streets_oid_feature_id_dict)
        if turn_feature_record != None:
            batch_insert_turn_features.append(turn_feature_record)
        batch_insert_prohibited_turns(turn_feature_class, batch_insert_turn_features)
        batch_insert_turn_features = []
        restrictions = []
        process_restriction_id = None

    arcpy.management.Delete(prohibited_maneuver_layer)
    del streets_oid_feature_id_dict


def create_memory_streets_dict(streets_feature_class):
    return {
        (record[0]): record[1]
        for record in arcpy.da.SearchCursor(streets_feature_class, ['FEATURE_ID', 'OID@'])
    }


def convert_restriction_to_prohibited_record(process_restriction_id, restrictions, streets_oid_feature_id_dict):
    record = None
    if len(restrictions) > out_turn_maximum_edges:
        # message = f'--- Skip restriction {process_restriction_id}, exceed max edges, count: {len(restrictions)}'
        # arcpy.AddWarning(message)
        pass
    else:
        prohibited_turn_feature = generate_prohibited_turn(process_restriction_id, restrictions,
                                                           streets_oid_feature_id_dict)
        record = prohibited_turn_feature

    return record


def generate_prohibited_turn(restriction_id, restrictions, streets_oid_feature_id_dict):

    edge_end = None
    union_geometry = None
    prohibited_turn_flag = 1
    restricted_turn_flag = 0
    feature = [union_geometry, edge_end,
               None, None, None,  # Edge1FCID, Edge1FID, Edge1Pos
               None, None, None,  # Edge2FCID, Edge2FID, Edge2Pos
               None, None, None,  # Edge3FCID, Edge3FID, Edge3Pos
               None, None, None,  # Edge4FCID, Edge4FID, Edge4Pos
               None, None, None,  # Edge5FCID, Edge5FID, Edge5Pos
               restriction_id, prohibited_turn_flag, restricted_turn_flag]

    FCID = national_streets_ID
    POS = 0.5
    
    first_geometry = None
    second_geometry = None
    
    for index, restriction in enumerate(restrictions):
        (sequence_num, feature_id, geometry) = restriction
        
        oid = None
        try:
            oid = streets_oid_feature_id_dict[feature_id]
        except:
            oid = None

        start_index = 2 + (sequence_num - 1) * 3
        feature[start_index] = FCID
        feature[start_index + 1] = oid
        feature[start_index + 2] = POS

        if index == 0:
            union_geometry = geometry
        else:
            union_geometry = union_geometry | geometry

        if index == 0:
            first_geometry = geometry
        elif index == 1:
            second_geometry = geometry

    if second_geometry == None:
        # dirty data
        return None

    edge_end = get_edge_end(first_geometry, second_geometry)

    feature[0] = union_geometry
    feature[1] = edge_end

    return feature


def get_edge_end(first_geometry, second_geometry):
    result = 'Y'
    first_start_point = first_geometry.firstPoint
    # first_end_point = first_geometry.lastPoint
    
    second_start_point = second_geometry.firstPoint
    second_end_point = second_geometry.lastPoint
    
    first_start_same_as_second_start = first_start_point.X == second_start_point.X and first_start_point.Y == second_start_point.Y
    first_start_same_as_second_end = first_start_point.X == second_end_point.X and first_start_point.Y == second_end_point.Y
    
    if first_start_same_as_second_start or first_start_same_as_second_end:
        result = 'N'
    
    return result


def batch_insert_prohibited_turns(turn_feature_class, turn_features):
    if len(turn_features) == 0:
        return
    
    message = f'--- batch_insert_prohibited_turns count: {len(turn_features)}'
    set_arcpy_progressor_label(message)
    
    
    fields = ['SHAPE@', 'Edge1End',
              'Edge1FCID', 'Edge1FID', 'Edge1Pos',
              'Edge2FCID', 'Edge2FID', 'Edge2Pos',
              'Edge3FCID', 'Edge3FID', 'Edge3Pos',
              'Edge4FCID', 'Edge4FID', 'Edge4Pos',
              'Edge5FCID', 'Edge5FID', 'Edge5Pos',
              'RestrictionID', 'ProhibitedTurnFlag', 'RestrictedTurnFlag']
    
    with arcpy.da.InsertCursor(turn_feature_class, fields) as cursor:
        for prohibited_turn_feature in turn_features:
            cursor.insertRow(prohibited_turn_feature)


#endregion
#####################################################################
#region Signposts


def create_national_signposts_feature_class():
    message = '- create_national_signposts_feature_class'
    show_message(message)

    out_path = fr'{out_GDB}\{out_dataset_name}'
    set_arcpy_workspace(out_path)

    arcpy.management.CreateFeatureclass(out_path, out_signposts_feature_class_name, 'POLYLINE')
    add_field(out_signposts_feature_class_name, 'ExitName', 'TEXT', 24)
    
    for i in range(10):
        add_field(out_signposts_feature_class_name, f'Branch{i}', 'TEXT', 180)
        add_field(out_signposts_feature_class_name, f'Branch{i}Dir', 'TEXT', 5)
        add_field(out_signposts_feature_class_name, f'Branch{i}Lng', 'TEXT', 2)
        add_field(out_signposts_feature_class_name, f'Toward{i}', 'TEXT', 180)
        add_field(out_signposts_feature_class_name, f'Toward{i}Lng', 'TEXT', 2)

    add_field(out_signposts_feature_class_name, 'SrcSignID', 'TEXT', 36)


def create_national_signposts_table():
    message = '- create_national_signposts_table'
    show_message(message)

    set_arcpy_workspace(out_GDB)
    arcpy.management.CreateTable(out_GDB, out_signposts_table_name)
    
    add_field(out_signposts_table_name, 'SignpostID', 'LONG')
    add_field(out_signposts_table_name, 'Sequence', 'LONG')
    add_field(out_signposts_table_name, 'EdgeFCID', 'LONG')
    add_field(out_signposts_table_name, 'EdgeFID', 'LONG')
    add_field(out_signposts_table_name, 'EdgeFrmPos', 'DOUBLE')
    add_field(out_signposts_table_name, 'EdgeToPos', 'DOUBLE')
    add_field(out_signposts_table_name, 'SegmentID', 'TEXT', 36)
    add_field(out_signposts_table_name, 'SrcSignID', 'TEXT', 36)


def create_national_skip_signposts_table():
    message = '- create_national_skip_signposts_table'
    show_message(message)
    
    set_arcpy_workspace(out_GDB)
    arcpy.management.CreateTable(out_GDB, out_signposts_skip_table_name)

    add_field(out_signposts_skip_table_name, 'SignpostID', 'TEXT', 36)
    add_field(out_signposts_skip_table_name, 'EdgesCount', 'LONG')


def generate_national_signposts():
    message = '- generate_national_signposts'
    show_message(message)
    
    states = [state.lower() for state in US_STATES]
    skip_signposts = []

    total_count = len(states)
    processing_count = 1
    for state in states:
        state_gdb_file = get_state_gdb_file(state)
        if arcpy.Exists(state_gdb_file):

            signpost_id_list = create_signpost_id_list(state_gdb_file, state)

            label = f'generate_state_signpost_features: {state.upper()}  ({processing_count}/{total_count})'
            set_arcpy_progressor_label(label)
            skip_features = generate_state_signpost_features(state_gdb_file, state, signpost_id_list)

            skip_signposts[len(skip_signposts):] = skip_features

            label = f'generate_state_signpost_table: {state.upper()}  ({processing_count}/{total_count})'
            set_arcpy_progressor_label(label)
            generate_state_signpost_table(state_gdb_file, state, signpost_id_list)
            del signpost_id_list
        processing_count += 1

    output_skip_signposts(skip_signposts)
    del skip_signposts


def output_skip_signposts(features):
    message = f'- output_skip_signposts, count: {len(features)}'
    show_message(message)

    create_national_skip_signposts_table()
    batch_insert_signposts_skips(out_signposts_skip_table_name, features)


def add_signposts_table_index():
    message = '- add_signposts_index'
    show_message(message)

    set_arcpy_workspace(out_GDB)

    index_fields = [('SignpostID', 'IDX_Signpost_Street_SignpostID'),
                    ('Sequence', 'IDX_Signpost_Street_Sequence'),
                    ('EdgeFCID', 'IDX_Signpost_Street_EdgeFCID'),
                    ('EdgeFID', 'IDX_Signpost_Street_EdgeFID')]
    for index_filed in index_fields:
        field_name, index_name = index_filed
        label = f'add index {index_name}'
        set_arcpy_progressor_label(label)
        arcpy.management.AddIndex(out_signposts_table_name, [field_name], index_name)


def generate_state_signpost_features(state_gdb_file, state, signpost_id_list):
    set_arcpy_workspace(state_gdb_file)

    in_street_feature_class = f'usa_{state}_streets'
    signpost_destinations_table = f'{state}{SIGNPOST_DESTINATIONS_TABLE_SUFFIX}'
    skip_features = []

    streets_feature_id_geometry_dict = create_memory_streets_geometry_dict(in_street_feature_class)

    batch_features = []

    for process_signposts_id in signpost_id_list:        
        signpost_features = []

        street_id_sequence_list = create_street_id_seq_list(signpost_destinations_table, process_signposts_id)
        destination_connection_sequence_list = create_destination_connection_sequence_list(signpost_destinations_table,
                                                                                           process_signposts_id)

        if len(street_id_sequence_list) > out_signposts_maximum_edges:
            skip_features.append((process_signposts_id, len(street_id_sequence_list)))
        else:
            signpost_geometry = generate_signpost_geometry(street_id_sequence_list, streets_feature_id_geometry_dict)
            signpost_feature = generate_signpost_feature(process_signposts_id, signpost_geometry,
                                                         destination_connection_sequence_list)
            if signpost_feature != None:
                batch_features.append(signpost_feature)

            if len(batch_features) % batch_insert_signpost_features_size == 0:
                batch_insert_signpost_features(out_signposts_feature_class_name, batch_features)
                batch_features = []
                set_arcpy_workspace(state_gdb_file)
                
        del street_id_sequence_list
        del destination_connection_sequence_list

    if len(batch_features) > 0:
        batch_insert_signpost_features(out_signposts_feature_class_name, batch_features)
        set_arcpy_workspace(state_gdb_file)

    del streets_feature_id_geometry_dict

    return skip_features


def generate_state_signpost_table(state_gdb_file, state, signpost_id_list):
    
    set_arcpy_workspace(state_gdb_file)
    
    in_street_feature_class = f'usa_{state}_streets'
    signpost_destinations_table = f'{state}{SIGNPOST_DESTINATIONS_TABLE_SUFFIX}'
    signpost_feature_class =  fr'{out_GDB}\{out_dataset_name}\{out_signposts_feature_class_name}'
    
    signpost_feature_oid_dict = create_memory_signpost_feature_oid_dict(signpost_feature_class)
    streets_oid_geometry_dict = create_memory_streets_oid_geometry_dict(in_street_feature_class)
    
    batch_records = []
    for process_signposts_id in signpost_id_list:
        try:
            signpost_feature_oid = signpost_feature_oid_dict[process_signposts_id]
        except:
            continue
        
        street_id_sequence_list = create_street_id_seq_list(signpost_destinations_table, process_signposts_id)
        if len(street_id_sequence_list) <= out_signposts_maximum_edges:
            records = generate_signpost_street_records(signpost_feature_oid, process_signposts_id,
                                                       street_id_sequence_list, streets_oid_geometry_dict)
            if len(records) > 0:
                batch_records[len(batch_records):] = records

            if len(batch_records) >= batch_insert_signpost_features_size:
                batch_insert_signposts_streets(out_signposts_table_name, batch_records)
                batch_records = []
                set_arcpy_workspace(state_gdb_file)

    if len(batch_records) > 0:
        batch_insert_signposts_streets(out_signposts_table_name, batch_records)
        set_arcpy_workspace(state_gdb_file)
    
    del signpost_feature_oid_dict
    del streets_oid_geometry_dict


def batch_insert_signpost_features(signposts_feature_class, signpost_features):
    if len(signpost_features) == 0:
        return

    out_path = fr'{out_GDB}\{out_dataset_name}'
    set_arcpy_workspace(out_path)
    
    fields = ['SHAPE@', 'ExitName',
              'Branch0', 'Branch0Dir', 'Branch0Lng', 'Toward0', 'Toward0Lng',
              'Branch1', 'Branch1Dir', 'Branch1Lng', 'Toward1', 'Toward1Lng',
              'Branch2', 'Branch2Dir', 'Branch2Lng', 'Toward2', 'Toward2Lng',
              'Branch3', 'Branch3Dir', 'Branch3Lng', 'Toward3', 'Toward3Lng',
              'Branch4', 'Branch4Dir', 'Branch4Lng', 'Toward4', 'Toward4Lng',
              'Branch5', 'Branch5Dir', 'Branch5Lng', 'Toward5', 'Toward5Lng',
              'Branch6', 'Branch6Dir', 'Branch6Lng', 'Toward6', 'Toward6Lng',
              'Branch7', 'Branch7Dir', 'Branch7Lng', 'Toward7', 'Toward7Lng',
              'Branch8', 'Branch8Dir', 'Branch8Lng', 'Toward8', 'Toward8Lng',
              'Branch9', 'Branch9Dir', 'Branch9Lng', 'Toward9', 'Toward9Lng',
              'SrcSignID']
    
    with arcpy.da.InsertCursor(signposts_feature_class, fields) as cursor:
        for signpost_feature in signpost_features:
            try:
                cursor.insertRow(signpost_feature)
            except:
                message = 'insert row error:'
                arcpy.AddWarning(message)
                
                if signpost_feature == None:
                    show_message("signpost_feature is None")
                else:
                    for item in signpost_feature:
                        show_message(item)
                continue


def generate_signpost_feature(signpost_id, signpost_geometry, destination_connection_sequence_list):
    
    LANGUAGE = 'en'
    exit_name = None
    if signpost_geometry == None:
        return None

    geometry = signpost_geometry.projectAs(SR_WEB_MERCATOR) if convert_to_web_mercator else signpost_geometry
    
    feature = [geometry, exit_name,
               None, None, None, None, None,  # 'Branch0', 'Branch0Dir', 'Branch0Lng', 'Toward0', 'Toward0Lng',
               None, None, None, None, None,
               None, None, None, None, None,
               None, None, None, None, None,
               None, None, None, None, None,
               None, None, None, None, None,  # 'Branch5', 'Branch5Dir', 'Branch5Lng', 'Toward5', 'Toward5Lng',
               None, None, None, None, None,  # 'Branch6', 'Branch6Dir', 'Branch6Lng', 'Toward6', 'Toward6Lng',
               None, None, None, None, None,
               None, None, None, None, None,
               None, None, None, None, None,  # 'Branch9', 'Branch9Dir', 'Branch9Lng', 'Toward9', 'Toward9Lng',
               signpost_id]
    
    for item in destination_connection_sequence_list:
        connection, destination_seq, destination_name = item

        index = 0
        if connection == 1:
            # Branch
            index = destination_seq * 5 - 3  # {2, 7, 12, ...} = {n | n = 5k - 3 }
            feature[index] = destination_name
            feature[index + 2] = LANGUAGE
            pass
        elif connection == 2:
            # Toward
            index = destination_seq * 5  # {5, 10, 15, ...} = {n | n = 5k }
            feature[index] = destination_name
            feature[index + 1] = LANGUAGE
        elif connection == 3:
            feature[1] = destination_name

    return feature


def generate_signpost_street_records(signpost_feature_id, src_sign_id, street_id_sequence_list, streets_oid_geometry_dict):
    
    records = []
    edge_FCID = national_streets_ID
    EDGE_POSITION_DICT = {
        'Y': {
            'FROM': 0,
            'TO': 1
        },
        'N': {
            'FROM': 1,
            'TO': 0
        },
    }
    
    street_count = len(street_id_sequence_list)
    for i in range(street_count):
        item = street_id_sequence_list[i]
        street_id, street_sequence = item[0], item[1]
        
        try:
            oid = streets_oid_geometry_dict[street_id][0]  # 'OID@'
        except:
            continue
        
        previous_geometry, geometry, next_geometry = None, None, None
        
        geometry = get_geometry_from_dict(street_id, streets_oid_geometry_dict)
        
        if geometry == None:
            continue
        
        if i < street_count - 1:
            next_item = street_id_sequence_list[i + 1]
            next_street_id = next_item[0]
            next_geometry = get_geometry_from_dict(next_street_id, streets_oid_geometry_dict)
            if next_geometry == None:
                continue

            edge_end = get_edge_end(geometry, next_geometry)
        else:
            previous_item = street_id_sequence_list[i - 1]
            previous_street_id = previous_item[0]
            previous_geometry = get_geometry_from_dict(previous_street_id, streets_oid_geometry_dict)
            if previous_geometry == None:
                continue

            edge_end = get_edge_end(geometry, previous_geometry)
            # Last segment gets flipped
            if edge_end == 'Y':
                edge_end = 'N'
            else:
                edge_end = 'Y'
    
        record = [signpost_feature_id,  # SignpostID
                  street_sequence,  # Sequence
                  edge_FCID,  # EdgeFCID
                  oid,  # EdgeFID
                  EDGE_POSITION_DICT[edge_end]['FROM'],  # EdgeFrmPos
                  EDGE_POSITION_DICT[edge_end]['TO'],  # EdgeToPos
                  street_id, # SegmentID
                  src_sign_id  # SrcSignID
                ]
        records.append(record)

    
    return records


def get_geometry_from_dict(street_id, streets_oid_geometry_dict):
    geometry = None
    
    try:
        geometry = streets_oid_geometry_dict[street_id][1]  # 'SHAPE@'
    except:
        return None

    return geometry


def batch_insert_signposts_streets(signposts_streets_table, signposts_streets_records):
    if len(signposts_streets_records) == 0:
        return
    
    set_arcpy_workspace(out_GDB)
    
    fields = ['SignpostID', 'Sequence', 'EdgeFCID', 'EdgeFID', 'EdgeFrmPos', 'EdgeToPos', 'SegmentID', 'SrcSignID']
    with arcpy.da.InsertCursor(signposts_streets_table, fields) as cursor:
        for record in signposts_streets_records:
            cursor.insertRow(record)


def batch_insert_signposts_skips(signposts_skip_table, signposts_skips_records):
    if len(signposts_skips_records) == 0:
        return
    
    set_arcpy_workspace(out_GDB)
    
    fields = ['SignpostID', 'EdgesCount']
    with arcpy.da.InsertCursor(signposts_skip_table, fields) as cursor:
        for record in signposts_skips_records:
            cursor.insertRow(record)


def generate_signpost_geometry(street_id_sequence_list, streets_feature_id_geometry_dict):
    union_geometry = None
    
    for item in street_id_sequence_list:
        street_id = item[0]

        street_geometry = None
        try:
            street_geometry = streets_feature_id_geometry_dict[street_id]
        except:
            # message = f'--- cannot find street geometry, street_id: {street_id}'
            # arcpy.AddWarning(message)
            return None
        
        if union_geometry == None:
            union_geometry = street_geometry
        else:
            union_geometry = union_geometry | street_geometry
            
    return union_geometry


def create_signpost_id_list(state_gdb_file, state):
    set_arcpy_workspace(state_gdb_file)

    signpost_id_list = []
    
    signposts_feature_class = f'{state}{SIGNPOST_FEATURE_SUFFIX}'

    signposts_layer = fr'memory\{signposts_feature_class}_lyr'
    arcpy.management.MakeFeatureLayer(signposts_feature_class, signposts_layer)
    
    signposts_fields = ['SignpostID']
    with arcpy.da.SearchCursor(signposts_layer,
                               signposts_fields,
                               sql_clause = (None, 'GROUP BY SignpostID ORDER BY SignpostID') ) as signpost_cursor:
        process_signposts_id = None

        for signpost_row in signpost_cursor:
            signpost_id = signpost_row[0]
            if process_signposts_id == signpost_id:
                message = f'--- duplicate signpost_id: {signpost_id}'
                show_message(message)
                continue
            signpost_id_list.append(signpost_id)
    
    arcpy.management.Delete(signposts_layer)

    return signpost_id_list


def create_street_id_seq_list(signpost_destinations_table, signposts_id):
    street_id_sequence_list = []
    signpost_destinations_table_fields = ['StreetID', 'StreetSeq']
    
    where_clause = f"SignpostID = '{signposts_id}'"
    with arcpy.da.SearchCursor(signpost_destinations_table,
                               signpost_destinations_table_fields,
                               where_clause,
                               sql_clause = (None, 'GROUP BY StreetID, StreetSeq ORDER BY StreetID, StreetSeq')) as signpost_destination_cursor:
        
        for signpost_destination_row in signpost_destination_cursor:
            street_id, street_sequence = signpost_destination_row[0], signpost_destination_row[1]
            street_id_sequence_list.append((street_id, street_sequence))
    
    return street_id_sequence_list


def create_destination_connection_sequence_list(signpost_destinations_table, signposts_id):
    
    result = []
    signpost_destinations_table_fields = ['Connection', 'DestinationSeq', 'DestinationName']
    
    where_clause = f"SignpostID = '{signposts_id}'"
    with arcpy.da.SearchCursor(signpost_destinations_table,
                                signpost_destinations_table_fields,
                                where_clause,
                                sql_clause = (None, 'GROUP BY Connection, DestinationSeq, DestinationName ORDER BY Connection, DestinationSeq, DestinationName')) as signpost_destination_cursor:
        
        for signpost_destination_row in signpost_destination_cursor:
            connection, destination_set, destination_name = signpost_destination_row[0], signpost_destination_row[1], signpost_destination_row[2]
            result.append((connection, destination_set, destination_name))

    return result


def create_memory_streets_geometry_dict(streets_feature_class):
    return {
        (record[0]): record[1]
        for record in arcpy.da.SearchCursor(streets_feature_class, ['FEATURE_ID', 'SHAPE@'])
    }


def create_memory_streets_oid_geometry_dict(streets_feature_class):
    return {
        (record[0]): (record[1], record[2])
        for record in arcpy.da.SearchCursor(streets_feature_class, ['FEATURE_ID', 'OID@', 'SHAPE@'])
    }


def create_memory_signpost_feature_oid_dict(signposts_feature_class):
    return {
        (record[0]): record[1]
        for record in arcpy.da.SearchCursor(signposts_feature_class, ['SrcSignID', 'OID@'])
    }


def rename_street_feature_id():
    # RENAME FEATURE_ID after restrictions and signposts
    streets_feature_class = get_project_name(national_map_streets) if convert_to_web_mercator else national_map_streets
    field_mapping = [
        {'from': 'FEATURE_ID', 'to': 'LocalId'}
    ]
    rename_fields(streets_feature_class, field_mapping)

    nd_street_feature_class = fr'{out_GDB}\{out_dataset_name}\{national_streets}'
    rename_fields(nd_street_feature_class, field_mapping)


#endregion
#####################################################################
#region Vector Tiles


def process_vector_by_category(category):
    message = f'- process category: {category}'
    set_arcpy_progressor_label(message)
    
    target_feature_class = f'national_{category.lower()}'
    tmp_target = fr'{out_GDB}\{target_feature_class}'
    
    arcpy.env.outputCoordinateSystem = SR_WGS_1984

    states = [state.lower() for state in US_STATES]
    for state in states:
        state_gdb_file = get_state_gdb_file(state)
        if arcpy.Exists(state_gdb_file):
            feature_class_name = f'{state}{category}'
            feature_class = fr'{state_gdb_file}\{feature_class_name}'
            
            if arcpy.Exists(feature_class):
                # copy and append to national feature class
                if arcpy.Exists(tmp_target):
                    arcpy.management.Append(feature_class, tmp_target, "TEST")
                else:
                    arcpy.management.CopyFeatures(feature_class, tmp_target)

    arcpy.env.outputCoordinateSystem = NATIONAL_SPATIAL_REFERENCE

    # There is no airports feature class in DC.
    if arcpy.Exists(tmp_target):
        project_feature_class = get_project_name(target_feature_class)
        out_project_feature_class = fr'{out_GDB}\{project_feature_class}'
        arcpy.management.Project(tmp_target, out_project_feature_class, SR_WEB_MERCATOR)

        arcpy.management.Delete(tmp_target)


def create_memory_county_code_dict():
    message = '- create_memory_county_code_dict'
    set_arcpy_progressor_label(message)

    national_counties = get_project_name('national_counties')
    return {
        (record[0]): record[1]
        for record in arcpy.da.SearchCursor(national_counties, ['A2_Code', 'Name'])
    }


def create_national_landmarks():
    message = '- create_national_landmarks'
    show_message(message)

    national_airports = 'national_airports_project'
    national_landuse = 'national_landuse_project'

    national_landmark_polygon = 'national_landmarks_polygon_project'

    arcpy.management.CopyFeatures(national_landuse, national_landmark_polygon)
    
    if arcpy.Exists(national_airports):
        arcpy.management.Append(national_airports, national_landmark_polygon, 'NO_TEST')

    national_landmark_polyline = 'national_landmarks_polyline_project'
    arcpy.management.CreateFeatureclass(out_GDB, national_landmark_polyline,
                                        geometry_type='POLYLINE',
                                        spatial_reference=SR_WEB_MERCATOR)
    
    add_field(national_landmark_polyline, 'Name', 'TEXT', 255)

    if ADAPT_FOR_ROUTEFINDER_PLUS:
        national_landmark_point = 'national_landmarks_project'
        landmark_layers = [national_landmark_point, national_landmark_polyline, national_landmark_polygon]
        for layer in landmark_layers:
            add_style_and_local_id_fields(layer)
            add_editable_fields(layer)


def process_national_railroads():
    message = '- process_national_railroads'
    show_message(message)

    national_railroads = get_project_name('national_railroads')
    field_mapping = [
        {'from': 'BeginGradeLevel', 'to': 'FromElevation'},
        {'from': 'EndGradeLevel', 'to': 'ToElevation'}
    ]
    rename_fields(national_railroads, field_mapping)

    if ADAPT_FOR_ROUTEFINDER_PLUS:
        add_style_and_local_id_fields(national_railroads)
        add_editable_fields(national_railroads)


def process_national_postcodes():
    message = '- process_national_postcodes'
    show_message(message)
    
    national_postcodes = get_project_name('national_postcodes')
    national_towns = get_project_name('national_towns')
    tmp_national_postcodes_spatial_join = f'{national_postcodes}_SJ'
    field_mapping=(
        f'FeatureID "FeatureID" true true false 36 Text 0 0,First,#,{national_postcodes},FeatureID,0,36;'
        f'PC_Name "PC_Name" true true false 50 Text 0 0,First,#,{national_postcodes},PC_Name,0,50;'
        f'PostalCode "PostalCode" true true false 10 Text 0 0,First,#,{national_postcodes},PostalCode,0,10;'
        f'CountryCode "CountryCode" true true false 3 Text 0 0,First,#,{national_postcodes},CountryCode,0,3;'
        f'miCode "miCode" true true false 4 Long 0 0,First,#,{national_postcodes},miCode,-1,-1;'
        f'SHAPE_Length "SHAPE_Length" false true true 8 Double 0 0,First,#,{national_postcodes},SHAPE_Length,-1,-1;'
        f'SHAPE_Area "SHAPE_Area" false true true 8 Double 0 0,First,#,{national_postcodes},SHAPE_Area,-1,-1;'
        f'City "City" true true false 100 Text 0 0,First,#,{national_towns},County,0,100;'
        f'State "State" true true false 2 Text 0 0,First,#,{national_towns},A1_Abbrev,0,2'
    )

    arcpy.analysis.SpatialJoin(
        target_features=national_postcodes,
        join_features=national_towns,
        out_feature_class=tmp_national_postcodes_spatial_join,
        field_mapping=field_mapping,
        match_option='CLOSEST'
    )

    arcpy.management.DeleteField(tmp_national_postcodes_spatial_join, ['Join_Count', 'TARGET_FID'])

    add_field(tmp_national_postcodes_spatial_join, 'Name', 'TEXT', 255)
    arcpy.management.CalculateField(tmp_national_postcodes_spatial_join, 'Name', '!PostalCode!')

    add_style_and_local_id_fields(tmp_national_postcodes_spatial_join)
    arcpy.management.CalculateField(tmp_national_postcodes_spatial_join, 'LocalId', '!PostalCode!')

    add_editable_fields(tmp_national_postcodes_spatial_join)

    arcpy.management.CopyFeatures(tmp_national_postcodes_spatial_join, national_postcodes)
    arcpy.management.Delete(tmp_national_postcodes_spatial_join)


def process_national_towns(county_code_dict):
    message = '- process_national_towns'
    show_message(message)

    national_towns = get_project_name('national_towns')

    add_county_state_fields(national_towns)
    add_style_and_local_id_fields(national_towns)
    add_editable_fields(national_towns)

    fields = ['A1_Abbrev', 'State', 'A2_Code', 'County']
    with arcpy.da.UpdateCursor(national_towns, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            row[3] = county_code_dict[row[2]]
            cursor.updateRow(row)


def process_national_waters():
    message = '- process_national_waters'
    show_message(message)
    
    national_water_polyline = 'national_rivers_project'
    national_water_polygon = 'national_waterbodies_project'
    water_layers = [national_water_polyline, national_water_polygon]
    for layer in water_layers:
        add_style_and_local_id_fields(layer)
        add_editable_fields(layer)


def add_editable_fields(layer):
    # keep consistent with plus
    add_field(layer, 'LastUpdated', 'DATE')
    add_field(layer, 'LastUpdatedBy', 'LONG')
    add_field(layer, 'CreatedOn', 'DATE')
    add_field(layer, 'CreatedBy', 'LONG')


def add_style_and_local_id_fields(layer):
    # keep consistent with plus
    add_field(layer, 'Style', 'TEXT', 255)
    add_field(layer, 'LocalId', 'TEXT', 255)


def add_county_state_fields(layer):
    # keep consistent with plus
    add_field(layer, 'County', 'TEXT', 255)
    add_field(layer, 'State', 'TEXT', 255)


#endregion
#####################################################################
#region Locator


def create_street_address_locator():

    set_arcpy_workspace(out_GDB)
    
    ensure_folder_exists(out_locator_folder)

    LANGUAGE = 'ENG'
    COUNTY = 'USA'
    streets_feature_class = get_project_name(national_map_streets) if convert_to_web_mercator else national_map_streets
    reference_data = f'{streets_feature_class} StreetAddress'
    street_feature_id = 'LocalId' if ADAPT_FOR_ROUTEFINDER_PLUS else 'FEATURE_ID'
    house_num_from_left = 'Fromleft' if ADAPT_FOR_ROUTEFINDER_PLUS else 'FROMLEFT'
    house_num_to_left = 'Toleft' if ADAPT_FOR_ROUTEFINDER_PLUS else 'TOLEFT'
    house_num_from_right = 'Fromright' if ADAPT_FOR_ROUTEFINDER_PLUS else 'FROMRIGHT'
    house_num_to_right = 'Toright' if ADAPT_FOR_ROUTEFINDER_PLUS else 'TORIGHT'
    street_name = 'Street' if ADAPT_FOR_ROUTEFINDER_PLUS else 'STREET'
    city_left = 'City' if ADAPT_FOR_ROUTEFINDER_PLUS else 'PostcodeName_Left'
    city_right = 'City' if ADAPT_FOR_ROUTEFINDER_PLUS else 'PostcodeName_Right'
    state_left = 'State' if ADAPT_FOR_ROUTEFINDER_PLUS else 'StateLeft'
    state_right = 'State' if ADAPT_FOR_ROUTEFINDER_PLUS else 'StateRight'

    field_mapping_template = f"'StreetAddress.FEATURE_ID $source.{street_feature_id}';\
        'StreetAddress.HOUSE_NUMBER_FROM_LEFT $source.{house_num_from_left}';\
        'StreetAddress.HOUSE_NUMBER_TO_LEFT $source.{house_num_to_left}';\
        'StreetAddress.HOUSE_NUMBER_FROM_RIGHT $source.{house_num_from_right}';\
        'StreetAddress.HOUSE_NUMBER_TO_RIGHT $source.{house_num_to_right}';\
        'StreetAddress.STREET_NAME $source.{street_name}';\
        'StreetAddress.CITY_LEFT $source.{city_left}';\
        'StreetAddress.CITY_RIGHT $source.{city_right}';\
        'StreetAddress.REGION_LEFT $source.{state_left}';\
        'StreetAddress.REGION_RIGHT $source.{state_right}';\
        'StreetAddress.POSTAL_LEFT $source.LeftPostalCode';\
        'StreetAddress.POSTAL_RIGHT $source.RightPostalCode';"
    template_dict = { 'source': streets_feature_class }
    t = Template(field_mapping_template)
    field_mapping = t.substitute(template_dict)

    arcpy.geocoding.CreateLocator(
        country_code = COUNTY,
        primary_reference_data = reference_data,
        field_mapping = field_mapping,
        out_locator = out_locator,
        language_code = LANGUAGE,
        alternatename_tables = None,
        alternate_field_mapping = None,
        custom_output_fields = None,
        precision_type = 'GLOBAL_EXTRA_HIGH'
    )

#endregion
#####################################################################
#region Build Network


def prepare_network_data():
    message = '- prepare_network_data'
    show_message(message)
    
    set_arcpy_workspace(out_GDB)

    out_feature_class = fr'{out_dataset_name}\{national_street_nodes}'
    label = f'copy feature {national_map_street_nodes} to {out_feature_class}'
    set_arcpy_progressor_label(label)

    arcpy.management.CopyFeatures(national_map_street_nodes, out_feature_class)
    arcpy.ResetProgressor()
    

def create_and_build_network_dataset():
    message = '- create_network_dataset'
    show_message(message)
    
    set_arcpy_workspace(out_GDB)
    output_feature_dataset = fr'{out_GDB}\{out_dataset_name}'
    output_network = arcpy.na.CreateNetworkDatasetFromTemplate(network_dataset_template, output_feature_dataset)

    message = '- build_network_dataset'
    show_message(message)

    arcpy.na.BuildNetwork(output_network)


def dissolve_network_dataset():
    message = '- dissolve_network_dataset'
    show_message(message)

    result = arcpy.management.CreateFileGDB(out_GDB_folder_path, out_dissolve_GDB)
    output_workspace_location = result.getOutput(0)
    
    in_network_dataset = fr'{out_GDB}\{out_dataset_name}\{out_network_dataset}'
    
    result = arcpy.na.DissolveNetwork(in_network_dataset, output_workspace_location)
    dissolve_network_dataset = result.getOutput(0)
    
    message = '- build dissolve_network_dataset'
    show_message(message)

    arcpy.na.BuildNetwork(dissolve_network_dataset)


def create_t_junctions():
    message = '- create_t_junctions'
    show_message(message)

    street_nodes = fr'{out_GDB}\{out_dataset_name}\{national_street_nodes}'
    streets_feature_class = get_project_name(national_map_streets) if convert_to_web_mercator else national_map_streets
    memory_out_feature_class = r'memory\temp_junctions'

    arcpy.analysis.SpatialJoin(target_features=street_nodes,
                               join_features=streets_feature_class,
                               out_feature_class=memory_out_feature_class,
                               join_operation='JOIN_ONE_TO_ONE',
                               join_type='KEEP_ALL',
                               field_mapping=f'ELEVATION "ELEVATION" true true false 4 Long 0 0,First,#,{national_street_nodes},ELEVATION,-1,-1',
                               match_option='INTERSECT',
                               search_radius='',
                               distance_field_name='')

    out_junctions = fr'{out_GDB}\{out_junctions_name}'
    arcpy.conversion.ExportFeatures(in_features=memory_out_feature_class,
                                    out_features=out_junctions,
                                    where_clause='Join_Count > 2',
                                    use_field_alias_as_name='NOT_USE_ALIAS',
                                    field_mapping=f'ELEVATION "ZELEV" true true false 4 Long 0 0,First,#,{memory_out_feature_class},ELEVATION,-1,-1',
                                    sort_field=None)

    arcpy.management.Delete(memory_out_feature_class)


def create_street_intersect():
    message = '- create_street_intersect'
    show_message(message)

    output_single_intersectors = False

    streets_feature_class = fr'{out_GDB}\{out_dataset_name}\{national_streets}'
    railroad_feature_class = fr'{out_GDB}\national_railroads_project'
    input_features = [streets_feature_class, railroad_feature_class]
    point_feature_class = fr'{out_GDB}\{out_street_railroads_intersector_name}_temp'
    arcpy.analysis.Intersect(input_features, point_feature_class, output_type='POINT')

    # keep consistent with plus, STREETINTERSECTR is multipoint and has identical features.
    out_intersect = fr'{out_GDB}\{out_street_railroads_intersector_name}'
    where_clause = 'FromElevation = ToElevation AND FromElevation_1 = ToElevation_1 AND FromElevation_1 = FromElevation AND ToElevation = ToElevation_1'
    arcpy.conversion.ExportFeatures(in_features=point_feature_class,
                                    out_features=out_intersect,
                                    where_clause=where_clause,
                                    use_field_alias_as_name='NOT_USE_ALIAS',
                                    sort_field=None)

    if output_single_intersectors:
        # backup the singlepart and no duplicate features as STREETINTERSECTR_S
        out_intersect_singlepart = fr'{out_GDB}\{out_street_railroads_intersector_name}_S'
        arcpy.management.MultipartToSinglepart(out_intersect, out_intersect_singlepart)
        arcpy.management.DeleteIdentical(out_intersect_singlepart, ['Shape'])

    arcpy.management.Delete(point_feature_class)
    # arcpy.management.Delete(out_intersect)


def prepare_mobile_map_package_data():
    message = '- prepare_mobile_map_package_data'
    show_message(message)
    
    dissolve_GDB = fr'{out_GDB_folder_path}\{out_dissolve_GDB}.gdb'
    
    in_features = [out_junctions_name, out_street_railroads_intersector_name, out_street_polygon_feature_class]
    for features in in_features:
        set_arcpy_progressor_label(f'-- copy {features}')
        inputs = fr'{out_GDB}\{features}'
        outputs = fr'{dissolve_GDB}\{features}'
        arcpy.management.CopyFeatures(inputs, outputs)


def generate_street_polygons():
    message = '- generate_street_polygons'
    show_message(message)

    set_arcpy_workspace(out_GDB)
    
    streets_feature_class = get_project_name(national_map_streets) if convert_to_web_mercator else national_map_streets
    arcpy.management.FeatureToPolygon(streets_feature_class, out_street_polygon_feature_class)


def create_mobile_map_package():
    message = '- create_mobile_map_package'
    show_message(message)
    
    out_map_package = fr'{out_GDB_folder_path}\{out_GDB_name}.mmpk'
    out_map_file = fr'{out_GDB_folder_path}\MMPK_map.mapx'
    out_mobile_map_package_project = fr'{out_GDB_folder_path}\NationalMapMMPK_out.aprx'
    update_mmpk_project_data_source(mobile_map_package_project_template, MMPK_DATA_SOURCE, out_mobile_map_package_project, out_map_file)

    in_locator = fr'{out_locator}.loc'
    if arcpy.Exists(in_locator):
        arcpy.management.CreateMobileMapPackage(
            in_map=out_map_file,
            output_file=out_map_package,
            in_locator=in_locator,
            extent='DEFAULT',
            title='NationalMap'
        )
    else:
        # process_locator has been skipped.
        arcpy.management.CreateMobileMapPackage(
            in_map=out_map_file,
            output_file=out_map_package,
            extent='DEFAULT',
            title='NationalMap without Locator'
        )


def update_mmpk_project_data_source(project_file, feature_class_dict, out_project_file, out_map_file):
    message = '-- update_mmpk_project_data_source'
    show_message(message)

    try:
        dissolve_GDB = fr'{out_GDB_folder_path}\{out_dissolve_GDB}.gdb'

        aprx = arcpy.mp.ArcGISProject(project_file)
        map = aprx.listMaps()[0]
        map.spatialReference = SR_WEB_MERCATOR
        
        layers = map.listLayers()
        layer_count = len(layers)
        
        for i in range(layer_count):
            layer = layers[i]
            layer_name = layer.name

            try:
                cp = layer.connectionProperties
                cp['connection_info']['database'] = dissolve_GDB
                cp['dataset'] = feature_class_dict[layer_name]
                layer.updateConnectionProperties(layer.connectionProperties, cp)
            except:
                message = f'-- updateConnectionProperties failed: {layer_name}'
                arcpy.AddWarning(message)
                continue

        map.exportToMAPX(out_map_file)
        aprx.saveACopy(out_project_file)

    except Exception as e:
        arcpy.AddWarning(e)
        return


#endregion
#####################################################################
#region Publish MapServer

def create_map_server_project():
    message = '- create_map_server_project'
    show_message(message)
    
    temp_aprx_path = fr'{out_GDB_folder_path}\{out_map_service_project_name}.aprx'
    if arcpy.Exists(temp_aprx_path):
        arcpy.management.Delete(temp_aprx_path)
    
    blank_aprx = arcpy.mp.ArcGISProject(blank_project_template)
    blank_aprx.saveACopy(temp_aprx_path)
    
    message = 'Add layers...'
    set_arcpy_progressor_label(message)
    
    temp_aprx = arcpy.mp.ArcGISProject(temp_aprx_path)
    temp_map = temp_aprx.listMaps()[0]
    temp_map.name = MAP_SERVICE_CONFIGURATION['SERVICE_NAME']
    
    enable_map_service_layer_id(temp_map)
    
    set_arcpy_workspace(out_GDB)
    
    map_server_sources = {
        'SIGNPOST_TABLE': out_signposts_table_name,  # national_signposts_streets
        'SIGNPOST_FEATURE': fr'{out_dataset_name}\{out_signposts_feature_class_name}',  # national_signposts
        'MAP_STREET': fr'{out_dataset_name}\{national_streets}',  # national_streets
        'MAP_R': vector_project_name['Railroads'][0],  # national_railroads_project
        'MAP_WTPOLYLINE': vector_project_name['Water'][0],  # national_rivers_project
        'MAP_WTPOLYGON': vector_project_name['Water'][1],  # national_waterbodies_project
        'MAP_PC': vector_project_name['PC'][0],  # national_postcodes_project
        'MAP_MC': vector_project_name['MC'][0],  # national_towns_project
        'MAP_LMPOLYLINE': vector_project_name['Landmarks'][1],  # national_landmarks_polyline_project
        'MAP_LMPOLYGON': vector_project_name['Landmarks'][2],  # national_landmarks_polygon_project
        'MAP_LMPOINT': vector_project_name['Landmarks'][0],  # national_landmarks_project
    }
    
    map_server_index = {
        'SIGNPOST_TABLE': 24,
        'SIGNPOST_FEATURE': 22,
        'MAP_STREET': 19,
        'MAP_R': 18,
        'MAP_WTPOLYLINE': 16,
        'MAP_WTPOLYGON': 15,
        'MAP_PC': 9,
        'MAP_MC': 7,
        'MAP_LMPOLYLINE': 6,
        'MAP_LMPOLYGON': 5,
        'MAP_LMPOINT': 4
    }
    
    for key in map_server_sources:
        source = fr'{out_GDB}\{map_server_sources[key]}' 
        message = f'Add: {source}'
        set_arcpy_progressor_label(message)

        if key == 'SIGNPOST_TABLE':
            table = arcpy.mp.Table(source)
            table.name = key
            set_map_service_table_id(table, map_server_index[key])
            temp_map.addTable(table)
        else:
            layer = temp_map.addDataFromPath(source)
            layer.name = key
            set_map_service_layer_id(layer, map_server_index[key])

    temp_aprx.save()
    arcpy.ResetProgressor()


def register_folder():
    message = '- register_folder'
    show_message(message)
    
    return

    connection_file = gis_server_connection_file
    datastore_type = 'FOLDER'
    folder_name = 'NationalMap'
    
    try:
        registered_folders = arcpy.ListDataStoreItems(connection_file, datastore_type)
        registered_folder_names = set(map(lambda i: i[0].lower(), registered_folders))
        if folder_name in registered_folder_names:
            arcpy.RemoveDataStoreItem(connection_file, datastore_type, folder_name)
        
        server_data_path = out_GDB_folder_path
        register_result = arcpy.AddDataStoreItem(connection_file, datastore_type, folder_name, server_data_path)
        if register_result == 'Success':
            message = f'-- register {folder_name} to DataStoreItem {register_result}'
            show_message(message)

    except Exception as e:
        arcpy.AddWarning(e)


def create_map_server():
    message = '- [SKIP] create_map_server'
    show_message(message)
    
    return
    
    out_sddraft = fr'{out_GDB_folder_path}\{out_map_service_project_name}.sddraft'
    out_sd = fr'{out_GDB_folder_path}\{out_map_service_project_name}.sd'
    
    temp_aprx_path = fr'{out_GDB_folder_path}\{out_map_service_project_name}.aprx'
    temp_aprx = arcpy.mp.ArcGISProject(temp_aprx_path)
    map = temp_aprx.listMaps()[0]
    
    server_type = 'STANDALONE_SERVER'
    service_type = 'MAP_SERVICE'
    service_name = MAP_SERVICE_CONFIGURATION['SERVICE_NAME']
    draft_value = map
    service_draft = arcpy.sharing.CreateSharingDraft(server_type, service_type, service_name, draft_value)

    service_draft.targetServer = gis_server_connection_file
    service_draft.serverFolder = SERVER_FOLDER_NAME
    service_draft.overwriteExistingService = True
    service_draft.summary = 'summary'
    service_draft.tags = 'NationalMap'
    service_draft.copyDataToServer = False
    service_draft.exportToSDDraft(out_sddraft)
    
    publish_sddraft = out_sddraft

    arcpy.StageService_server(publish_sddraft, out_sd)
    arcpy.UploadServiceDefinition_server(out_sd, gis_server_connection_file)


def enable_map_service_layer_id(map):
    # Allow assignment of unique numeric IDs for sharing web layers
    map_cim = map.getDefinition('V3')
    map_cim.useServiceLayerIDs = True
    map.setDefinition(map_cim)


def set_map_service_layer_id(layer, id):
    cim = layer.getDefinition('V2')
    cim.serviceLayerID = id
    layer.setDefinition(cim)


def set_map_service_table_id(table, id):
    cim_stancalone_table = table.getDefinition('V2')
    cim_stancalone_table.serviceTableID = id
    table.setDefinition(cim_stancalone_table)


def modify_map_service_definition_draft(sddraft):
    modified_sddraft = fr'{out_GDB_folder_path}\tmp_{out_map_service_project_name}.sddraft'

    doc = DOM.parse(sddraft)
    props = doc.getElementsByTagName('Props')[0]
    property_set_property = props.childNodes[0].childNodes

    for item in property_set_property:
        key_name = item.firstChild.firstChild.data
        if key_name == 'MinInstances':
            item.lastChild.firstChild.data = MAP_SERVICE_CONFIGURATION['MIN_INSTANCES']
        elif key_name == 'MaxInstances':
            item.lastChild.firstChild.data = MAP_SERVICE_CONFIGURATION['MAX_INSTANCES']
        elif key_name == 'WaitTimeout':
            item.lastChild.firstChild.data = MAP_SERVICE_CONFIGURATION['WAIT_TIMEOUT']

    xml_file = open(modified_sddraft, 'w')
    doc.writexml(xml_file)
    xml_file.close()

    return modified_sddraft


#endregion
#####################################################################
#region Utility Functions


def get_state_gdb_file(state):
    return fr'{precisely_gdb_location}/usa_{state}_navprem_{precisely_data_version}.gdb'


def query_count(feature_class_or_table):
    return arcpy.management.GetCount(feature_class_or_table)


def set_arcpy_workspace(workspace):
    arcpy.env.workspace = workspace

 
def is_field_exists(table_or_feature_class, field_name):
    result = False
    fields = arcpy.ListFields(table_or_feature_class)
    for field in fields:
        if field.name == field_name:
            result = True
            break
    return result


def is_turn_feature_exists(feature_dataset_name, out_turn_feature_class):
    result = False
    feature_classes = arcpy.ListFeatureClasses('*', 'Polyline', feature_dataset_name)
    for name in feature_classes:
        if name == out_turn_feature_class:
            result = True
            break

    return result


def is_feature_dataset_exists(feature_dataset_name):
    result = False
    feature_datasets = arcpy.ListDatasets('*', 'Feature')
    if feature_datasets == None:
        return result

    for dataset in feature_datasets:
        if dataset == feature_dataset_name:
            result = True
            break

    return result


def is_skip_process(name):
    result = DEBUG_MODE and SKIP_PROCESS[name]
    if result:
        message = f'- *DEBUG_MODE* SKIP_PROCESS {name}'
        show_message(message)
    return result


def add_field(in_table, field_name, field_type, field_length = None):
    result = False
    if not is_field_exists(in_table, field_name):
        arcpy.management.AddField(in_table, field_name, field_type, field_length = field_length)
        result = True

    return result


def rename_fields(feature_class, field_mapping):

    for item in field_mapping:
        if not is_field_exists(feature_class, item['to']) and is_field_exists(feature_class, item['from']):
            message = f"--- Rename {item['from']} -> {item['to']}"
            set_arcpy_progressor_label(message)
            arcpy.management.AlterField(feature_class,
                                        field=item['from'],
                                        new_field_name=item['to'],
                                        new_field_alias=item['to'])


def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)


#endregion
#####################################################################
#region Logging

def national_logger_settings():
    global logger

    ensure_folder_exists(out_log_folder)

    logger = logging.getLogger(__name__)

    file_handler = RotatingFileHandler(NATIONAL_LOG_FILE, mode='a', maxBytes=10_100_000, encoding='utf-8')

    formatter = logging.Formatter(
        '{asctime}\t{levelname}:\t{name}:\t{message}',
        style='{',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.setLevel(NATIONAL_LOG_LEVEL)


def start_log_process(process_name):
    logger.info(f'START {process_name}')


def stop_log_process(process_name):
    logger.info(f'STOP {process_name}')


def show_message(message):
    arcpy.AddMessage(message)
    logger.info(message)


def set_arcpy_progressor_label(label):
    arcpy.SetProgressorLabel(label)
    logger.debug(label)


def close_logger():
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.close()


#endregion
#####################################################################
# Main Function

def main():
    read_configuration()
    national_logger_settings()
    setup_environment()
    create_out_GDB()
    combine_state_data_to_national()
    process_national_data()
    prepare_routing_dataset()
    process_national_restrictions()
    process_national_signposts()
    process_vector_data()
    process_locator()
    process_network_dataset()
    process_mobile_map_package()
    clear_workspace()


if __name__ == '__main__':
    main()


#####################################################################
