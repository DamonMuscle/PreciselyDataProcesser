import os
import arcpy

SR_WEB_MERCATOR = arcpy.SpatialReference(3857)
SR_WGS_1984 = arcpy.SpatialReference(4326)


US_LANGUAGE_CODE = 'EN'
US_STATES = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA', 'DE',
             'MD', 'DC', 'OH', 'WV', 'VA', 'NC', 'SC', 'MI', 'IN', 'KY',
             'TN', 'GA', 'AL', 'FL', 'MS', 'WI', 'IL', 'MN', 'IA', 'MO',
             'AR', 'LA', 'ND', 'SD', 'NE', 'KS', 'OK', 'TX', 'MT', 'WY',
             'CO', 'NM', 'ID', 'UT', 'AZ', 'WA', 'OR', 'NV', 'CA', 'AK',
             'HI']
COUNTY_CODE = 'USA'
LOCATOR_LANGUAGE_CODE = 'ENG'


TEMP_MEMORY_LAYER = os.path.join('memory', 'layer')

OUT_FORMAT = {
    'SDE': 'SDE',
    'FILE_GDB': 'FILEGDB'
}

GDB_ITEMS_DICT = {
    'NATIONAL': {
        'DATASET': {
            'name': 'RoutingND',
            'node_name': 'national_street_nodes',
            'signpost_name': 'national_signposts',
            'street_name': 'national_streets',
            'turn_name': 'national_turns'
        },
        'counties_name': 'national_counties',
        'landmark_name': 'national_landmarks',
        'landmark_polyline_name': 'national_landmarks_polyline',
        'landmark_polygon_name': 'national_landmarks_polygon',
        'postcode_name': 'national_postcodes',
        'railroad_name': 'national_railroads',
        'river_name': 'national_rivers',
        'town_name': 'national_towns',
        'waterbody_name': 'national_waterbodies',
        'restriction_name': 'national_restrictions',
        'signpost_table_name': 'national_signposts_streets',
        't_junction_name': 'Junctions',
        'street_railroad_intersect_name': 'STREETINTERSECTR',
        'street_polygon_name': 'national_street_polygon'
    },
    'STATE': {
        'street_name': 'streets',
        'node_name': 'street_nodes',
        'counties_name': 'counties',
        'landmark_name': 'landmarks',
        'landmark_polyline_name': 'landmarks_polyline',
        'landmark_polygon_name': 'landmarks_polygon',
        'postcode_name': 'postcodes',
        'railroad_name': 'railroads',
        'river_name': 'rivers',
        'town_name': 'towns',
        'waterbody_name': 'waterbodies',
        'restriction_name': 'restrictions',
        'signpost_name': 'signposts',
        'signpost_table_name': 'signposts_streets'
    }
}

NATIONAL_NETWORK_DATASET_NAME = 'national_routing_ND'
DEFAULT_GEODATABASE_SCHEMA = 'DBO'

MMPK_DATA_SOURCE = {
    'Map_Turn': GDB_ITEMS_DICT['NATIONAL']['DATASET']['turn_name'],
    'MAP_STREET': GDB_ITEMS_DICT['NATIONAL']['DATASET']['street_name'],
    'STREETINTERSECTR': GDB_ITEMS_DICT['NATIONAL']['street_railroad_intersect_name'],
    'routing_ND_Junctions': f'{NATIONAL_NETWORK_DATASET_NAME}_Junctions',
    'StreetPolygon': GDB_ITEMS_DICT['NATIONAL']['street_polygon_name'],
    'national_routing_ND': NATIONAL_NETWORK_DATASET_NAME
}
