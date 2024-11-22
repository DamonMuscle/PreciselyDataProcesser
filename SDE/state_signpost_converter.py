import arcpy
from national_map import constants

from state_converter import StateConverter
from national_map_utility import NationalMapUtility

MAX_SIGNPOST_EDGES = 5

EDGE_POSITION_DICT = {
    'Y': {
        'FROM': 0,
        'TO': 1
    },
    'N': {
        'FROM': 1,
        'TO': 0
    }
}


def create_street_local_id_and_oid_geometry_lookup(street_feature_class):
    """
    :param street_feature_class:
    :return: Dict[LocalId] = (OBJECTID, SHAPE)
    """
    return {
        (item[0]): (item[1], item[2])
        for item in arcpy.da.SearchCursor(street_feature_class, ['LocalId', 'OID@', 'SHAPE@'])
    }


def create_street_id_and_sequence_lookup(signpost_destinations_table, signpost_id):
    results = []
    fields = ['StreetID', 'StreetSeq']
    where_clause = f"SignpostID = '{signpost_id}'"
    sql_clause = (None, 'GROUP BY StreetID, StreetSeq ORDER BY StreetID, StreetSeq')
    with arcpy.da.SearchCursor(signpost_destinations_table, fields, where_clause, sql_clause=sql_clause) as cursor:
        for row in cursor:
            street_id, sequence = row[0], row[1]
            results.append((street_id, sequence))

    return results


def create_connection_sequence_and_name_lookup(signpost_destinations_table, signpost_id):
    results = []
    fields = ['Connection', 'DestinationSeq', 'DestinationName']
    where_clause = f"SignpostID = '{signpost_id}'"
    sql_clause = (None, 'GROUP BY Connection, DestinationSeq, DestinationName '
                        'ORDER BY Connection, DestinationSeq, DestinationName')
    with arcpy.da.SearchCursor(signpost_destinations_table, fields, where_clause, sql_clause=sql_clause) as cursor:
        for row in cursor:
            connection, destination_set, destination_name = row[0], row[1], row[2]
            results.append((connection, destination_set, destination_name))

    return results


def create_sign_id_and_oid_lookup(signpost_feature_class):
    """
    :param signpost_feature_class:
    :return: Dict[SrcSignID] = OBJECTID
    """
    return {
        (item[0]): item[1]
        for item in arcpy.da.SearchCursor(signpost_feature_class, ['SrcSignID', 'OID@'])
    }


def create_signpost_feature(signpost_id, signpost_geometry, destination_lookup):
    exit_name = None
    feature: list = [signpost_geometry, exit_name]
    for i in range(MAX_SIGNPOST_EDGES):
        # 'Branch0', 'Branch0Dir', 'Branch0Lng', 'Toward0', 'Toward0Lng'
        empty_signpost = [None, None, None, None, None]
        feature.extend(empty_signpost)
    feature.append(signpost_id)

    for item in destination_lookup:
        connection, destination_seq, destination_name = item
        if connection == 1:
            # Branch
            index = destination_seq * 5 - 3  # {2, 7, 12, ...} = {n | n = 5k - 3 }
            feature[index] = destination_name
            feature[index + 2] = constants.US_LANGUAGE_CODE
        elif connection == 2:
            # Toward
            index = destination_seq * 5  # {5, 10, 15, ...} = {n | n = 5k }
            feature[index] = destination_name
            feature[index + 1] = constants.US_LANGUAGE_CODE
        elif connection == 3:
            exit_name = destination_name
            feature[1] = exit_name

    return feature


def add_signpost_fields(signpost_feature_class):
    NationalMapUtility.add_field(signpost_feature_class, 'ExitName', 'TEXT', 24)
    for i in range(MAX_SIGNPOST_EDGES):
        NationalMapUtility.add_field(signpost_feature_class, f'Branch{i}', 'TEXT', 180)
        NationalMapUtility.add_field(signpost_feature_class, f'Branch{i}Dir', 'TEXT', 5)
        NationalMapUtility.add_field(signpost_feature_class, f'Branch{i}Lng', 'TEXT', 2)
        NationalMapUtility.add_field(signpost_feature_class, f'Toward{i}', 'TEXT', 180)
        NationalMapUtility.add_field(signpost_feature_class, f'Toward{i}Lng', 'TEXT', 2)

    NationalMapUtility.add_field(signpost_feature_class, 'SrcSignID', 'TEXT', 36)


def add_signpost_table_fields(signpost_table):
    NationalMapUtility.add_field(signpost_table, 'SignpostID', 'LONG')
    NationalMapUtility.add_field(signpost_table, 'Sequence', 'LONG')
    NationalMapUtility.add_field(signpost_table, 'EdgeFCID', 'LONG')
    NationalMapUtility.add_field(signpost_table, 'EdgeFID', 'LONG')
    NationalMapUtility.add_field(signpost_table, 'EdgeFrmPos', 'DOUBLE')
    NationalMapUtility.add_field(signpost_table, 'EdgeToPos', 'DOUBLE')
    NationalMapUtility.add_field(signpost_table, 'SegmentID', 'TEXT', 36)
    NationalMapUtility.add_field(signpost_table, 'SrcSignID', 'TEXT', 36)


def get_signpost_oid(lookup, signpost_id):
    try:
        return lookup[signpost_id]
    except Exception as e:
        return None


def reverse_edge_end(edge_end):
    if edge_end == 'Y':
        result = 'N'
    else:
        result = 'Y'
    return result


class StateSignpostConverter(StateConverter):
    def __init__(self, data_settings, state_exporter, data):
        super().__init__(data_settings, state_exporter, data)
        self.unique_signpost_id = None
        self.street_local_id_oid_shape_lookup = None
        self._init_street_lookup()

    def __del__(self):
        super().__del__()
        del self.unique_signpost_id
        del self.street_local_id_oid_shape_lookup

    def _init_street_lookup(self):
        if self.street_local_id_oid_shape_lookup:
            return

        street_feature_class = self.data['state_street_feature_class']
        self.street_local_id_oid_shape_lookup = create_street_local_id_and_oid_geometry_lookup(street_feature_class)

    def _get_street_object_id_and_shape(self, local_id):
        try:
            return self.street_local_id_oid_shape_lookup[local_id]
        except Exception as e:
            return None

    def _create_signpost_feature_class(self):
        scratch_gdb = self.settings['scratch_geodatabase']
        signpost_name = 'temp_signposts'
        signpost_feature_class = arcpy.management.CreateFeatureclass(scratch_gdb, signpost_name,
                                                                     geometry_type='POLYLINE',
                                                                     spatial_reference=constants.SR_WGS_1984)
        add_signpost_fields(signpost_feature_class)
        self.data['state_signpost_feature_class'] = signpost_feature_class

    def _create_signpost_table(self):
        scratch_gdb = self.settings['scratch_geodatabase']
        signpost_table_name = constants.GDB_ITEMS_DICT['STATE']['signpost_table_name']
        signpost_table = arcpy.management.CreateTable(scratch_gdb, signpost_table_name)

        add_signpost_table_fields(signpost_table)
        self.data['state_signpost_table'] = signpost_table

    def _create_signpost_features(self):
        signpost_features = self._generate_signpost_features()
        print(f'_create_signpost_features: count - {len(signpost_features)}')

        feature_class = self.data['state_signpost_feature_class']
        fields = ['SHAPE@', 'ExitName']
        for i in range(MAX_SIGNPOST_EDGES):
            signpost_i = [f'Branch{i}', f'Branch{i}Dir', f'Branch{i}Lng', f'Toward{i}', f'Toward{i}Lng']
            fields.extend(signpost_i)
        fields.append('SrcSignID')

        with arcpy.da.InsertCursor(feature_class, fields) as cursor:
            for feature in signpost_features:
                cursor.insertRow(feature)

    def _get_unique_signpost_id(self):
        results = []
        signposts_name = f'{self.state}signposts'
        signposts_feature_class = self.exporter.get_precisely_feature_path(signposts_name)
        memory_layer = self.create_memory_layer()
        arcpy.management.MakeFeatureLayer(signposts_feature_class, memory_layer)

        fields = ['SignpostID']
        sql_clause = (None, 'GROUP BY SignpostID ORDER BY SignpostID')
        with arcpy.da.SearchCursor(memory_layer, fields, sql_clause=sql_clause) as cursor:
            process_signposts_id = None

            for row in cursor:
                signpost_id = row[0]
                if process_signposts_id == signpost_id:
                    message = f'duplicate signpost_id {signpost_id}'
                    print(message)
                    continue
                process_signposts_id = signpost_id
                results.append(signpost_id)

        self.dispose_memory_layer()
        return results

    def _generate_signpost_features(self):
        features = []

        table_name = f'{self.state}signpostdestinations'
        destinations_table = self.exporter.get_precisely_feature_path(table_name)

        for signpost_id in self.unique_signpost_id:
            street_lookup = create_street_id_and_sequence_lookup(destinations_table, signpost_id)
            if len(street_lookup) <= MAX_SIGNPOST_EDGES:
                signpost_geometry = self._generate_signpost_geometry(street_lookup)
                if signpost_geometry is not None:
                    destination_lookup = create_connection_sequence_and_name_lookup(destinations_table, signpost_id)
                    if len(destination_lookup) <= MAX_SIGNPOST_EDGES:
                        signpost_feature = create_signpost_feature(signpost_id, signpost_geometry, destination_lookup)
                        features.append(signpost_feature)
                    else:
                        pass
                    del destination_lookup
                else:
                    pass
            else:
                pass
            del street_lookup

        return features

    def _create_signpost_records(self):
        signpost_records = self._generate_signpost_table_records()
        print(f'_create_signpost_records: count - {len(signpost_records)}')

        table = self.data['state_signpost_table']
        fields = ['SignpostID', 'Sequence', 'EdgeFCID', 'EdgeFID', 'EdgeFrmPos', 'EdgeToPos', 'SegmentID', 'SrcSignID']
        with arcpy.da.InsertCursor(table, fields) as cursor:
            for record in signpost_records:
                cursor.insertRow(record)

    def _generate_signpost_table_records(self):
        results = []
        signpost_feature_class = self.data['state_signpost_feature_class']
        sign_id_and_oid_lookup = create_sign_id_and_oid_lookup(signpost_feature_class)

        table_name = f'{self.state}signpostdestinations'
        destinations_table = self.exporter.get_precisely_feature_path(table_name)

        for signpost_id in self.unique_signpost_id:
            signpost_feature_oid = get_signpost_oid(sign_id_and_oid_lookup, signpost_id)
            if signpost_feature_oid is None:
                continue

            street_lookup = create_street_id_and_sequence_lookup(destinations_table, signpost_id)
            if len(street_lookup) <= MAX_SIGNPOST_EDGES:
                records = self._generate_signpost_records(signpost_feature_oid, signpost_id, street_lookup)
                if len(records) > 0:
                    results[len(results):] = records
            else:
                pass
            del street_lookup

        return results

    def _export_state_signposts(self):
        self._create_signpost_feature_class()
        self._create_signpost_table()

        self.unique_signpost_id = self._get_unique_signpost_id()
        self._create_signpost_features()
        self._create_signpost_records()

    def _generate_signpost_geometry(self, street_id_and_sequence_lookup):
        union_geometry = None
        for item in street_id_and_sequence_lookup:
            street_id = item[0]
            street_oid_and_shape = self._get_street_object_id_and_shape(street_id)
            if street_oid_and_shape is None:
                continue

            street_geometry = street_oid_and_shape[1]

            if street_geometry is None:
                union_geometry = None
                break

            if union_geometry is None:
                union_geometry = street_geometry
            else:
                union_geometry = union_geometry | street_geometry
        return union_geometry

    def _generate_signpost_records(self, signpost_feature_oid, signpost_id, street_lookup):
        records = []

        edge_feature_class_id = -1
        street_count = len(street_lookup)
        for index in range(street_count):
            item = street_lookup[index]
            street_id, street_sequence = item[0], item[1]

            is_last_street: bool = index == street_count - 1

            result = self._get_street_object_id_and_shape(street_id)
            if result is None:
                continue
            edge_feature_id, street_geometry = result[0], result[1]

            if is_last_street:
                previous_item = street_lookup[index - 1]
                previous_street_id = previous_item[0]
                previous_result = self._get_street_object_id_and_shape(previous_street_id)
                if previous_result is None:
                    continue
                previous_geometry = previous_result[1]
                edge_end = NationalMapUtility.get_edge_end(street_geometry, previous_geometry)
                edge_end = reverse_edge_end(edge_end)
            else:
                next_item = street_lookup[index + 1]
                next_street_id = next_item[0]
                next_result = self._get_street_object_id_and_shape(next_street_id)
                if next_result is None:
                    continue
                next_geometry = next_result[1]
                edge_end = NationalMapUtility.get_edge_end(street_geometry, next_geometry)

            record = [signpost_feature_oid, street_sequence, edge_feature_class_id, edge_feature_id,
                      EDGE_POSITION_DICT[edge_end]['FROM'], EDGE_POSITION_DICT[edge_end]['TO'], street_id, signpost_id]
            records.append(record)

        return records

    def _project_state_signposts(self):
        out_features = self.data['state_signpost_feature_class']
        self.exporter.project_state_data(out_features, constants.GDB_ITEMS_DICT['STATE']['signpost_name'])

    def _clear_workspace(self):
        arcpy.management.Delete(self.data['state_signpost_feature_class'])

    def run(self):
        self._export_state_signposts()
        self._project_state_signposts()
        self._clear_workspace()
