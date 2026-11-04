from arcgis.gis import GIS
import arcpy
import os
import datetime


def create_local_feature_class(featureset_dict, output_path, output_name):
    """
    Creates a local feature class from a featureset dictionary.

    :param featureset_dict: Dictionary created by the to_dict() function of a FeatureSet
    :param output_path: Path where the feature class will be created
    :param output_name: Name of the output feature class
    :return: Path to the created feature class
    """
    # Ensure the output path exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Full path for the output feature class
    output_fc = os.path.join(output_path, output_name)

    # Get the spatial reference from the dictionary
    spatial_reference = arcpy.SpatialReference(featureset_dict['spatialReference']['wkid'])

    # Create the feature class
    arcpy.management.CreateFeatureclass(
        out_path=output_path,
        out_name=output_name,
        geometry_type=featureset_dict['geometryType'].replace('esriGeometry', '').upper(),
        spatial_reference=spatial_reference
    )

    # Add fields to the feature class
    for field in featureset_dict['fields']:
        if field['name'] not in ['Shape', 'objectid'] and field['type'] not in ['esriFieldTypeOID']:  # Skip these fields as they are automatically created
            arcpy.management.AddField(
                in_table=output_fc,
                field_name=field['name'].replace('objectid', 'objectid_Original'),
                field_type=field['type'].replace('esriFieldTypeOID', 'INTEGER').replace('esriFieldType', '').upper(),
                field_precision=field.get('precision'),
                field_scale=field.get('scale'),
                field_length=field.get('length'),
                field_alias=field.get('alias'),
                field_is_nullable='NULLABLE',
                field_is_required=field.get('required', 'NON_REQUIRED')
            )
    arcpy.management.AddField(output_fc, 'objectid_Original', 'LONG')

    # Prepare the list of fields for the insert cursor
    fields = [f['name'] for f in featureset_dict['fields'] if 'objectid' not in f['name']]
    fields.append('objectid_Original')
    fields.append('SHAPE@')
    field_types = [f['type'] for f in featureset_dict['fields'] if f['name'] not in ['objectid']]

    with arcpy.da.InsertCursor(output_fc, fields) as cursor:
        for feature in featureset_dict['features']:
            row = [feature['attributes'].get(field, None) for field in fields if field not in ['objectid_Original', 'SHAPE@']]
            row.append(feature['attributes']['objectid'])
            row.append(None)
            for i in range(len(field_types)):
                field_type = field_types[i]
                if field_type == 'esriFieldTypeDate':
                    if row[i] is not None and isinstance(row[i], int):
                        if row[i] > 0:
                            row[i] = datetime.datetime.fromtimestamp(row[i] / 1000)
                        else:
                            row[i] = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=(row[i] / 1000))
            if 'geometry' in feature:
                geometry = None
                if featureset_dict['geometryType'] == 'esriGeometryPolyline':
                    geometry = arcpy.Polyline(arcpy.Array([arcpy.Point(*coords) for path in feature['geometry']['paths'] for coords in path]), spatial_reference)
                elif featureset_dict['geometryType'] == 'esriGeometryPolygon':
                    geometry = arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in feature['geometry']['rings'][0]]), spatial_reference)
                elif featureset_dict['geometryType'] == 'esriGeometryPoint':
                    geometry = arcpy.PointGeometry(arcpy.Point(feature['geometry']['x'], feature['geometry']['y']), spatial_reference)
                row[-1] = geometry
            cursor.insertRow(row)

    print(f"Feature class created successfully at: {output_fc}")
    return output_fc


def main():
    gis = GIS('Pro')
    treatment_ids = ['b42c18447c094cb1b21a35eb64097edf', '200175712a6c4ffeb35128ebfedb5071', '92390218230447539623e14f8d31c605']
    weed_ids = ['cecd23513e404abd8fd402cd28e43d1b', '3ce8b068969e495bae51c7393a6aa716', '3a1b5f1b9b6a485bad66722286d49703']
    prefixes = ['treatment', 'weed']
    id_matrix = [treatment_ids, weed_ids]
    suffixes = ['_points', '_lines', '_polygons']

    scratch_gdb = os.path.join('c:/temp', 'nps_scratch.gdb')
    if not os.path.exists('c:/temp'):
        os.makedirs('c:/temp')
    if arcpy.Exists(scratch_gdb):
        arcpy.Delete_management(scratch_gdb)
    arcpy.CreateFileGDB_management('c:/temp', 'nps_scratch.gdb')
    arcpy.env.workspace = scratch_gdb

    for n in range(2):
        for i in range(3):
            hosted_layer = gis.content.get(id_matrix[n][i]).layers[0].query("1=1").to_dict()
            create_local_feature_class(hosted_layer, scratch_gdb, f'{prefixes[n]}{suffixes[i]}')
            if i < 2:
                arcpy.AddField_management(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'), 'buffer_distance_concat', 'TEXT')
                arcpy.CalculateField_management(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'), 'buffer_distance_concat', 'str(!BUFFER_M!) + " Meters"', 'PYTHON_9.3')
                if i == 0:
                    arcpy.analysis.Buffer(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'), os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}_buffer'), 'buffer_distance_concat')
                    arcpy.Delete_management(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'))
                elif i == 1:
                    directions = ['LEFT', 'RIGHT', 'FULL']
                    for direction in directions:
                        dir_query = f"BUFDIR = '{direction}'"
                        print(dir_query)
                        arcpy.SelectLayerByAttribute_management(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'), 'NEW_SELECTION', dir_query)
                        arcpy.analysis.Buffer(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'), os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}_{direction}_buffer'), 'buffer_distance_concat', direction)  # add , direction to end for prod
                    arcpy.Delete_management(os.path.join(scratch_gdb, f'{prefixes[n]}{suffixes[i]}'))
        merge_list = []
        for fc in arcpy.ListFeatureClasses():
            if prefixes[n] in fc:
                merge_list.append(fc)
        arcpy.Merge_management(merge_list, os.path.join(scratch_gdb, f'{prefixes[n]}_merged'))
        print(os.path.join(scratch_gdb, f'{prefixes[n]}_merged'))


if __name__ == '__main__':
    main()
