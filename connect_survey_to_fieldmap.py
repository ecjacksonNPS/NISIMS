from arcgis.features import FeatureLayer
from arcgis.gis import GIS

def update_parent_global_id(species_layer, location_layer):
    """
    Updates the ParentGlobalID in the species layer based on matching record_id in the location layer.

    :param species_layer: FeatureLayer object for the species layer (survey123)
    :param location_layer: FeatureLayer object for the location layer (fieldmaps)
    """
    # Step 1: Select all records from species where ParentGlobalID is null
    species_query = "ParentGlobalID IS NULL"
    species_features = species_layer.query(where=species_query)

    # Step 2 & 3: For each selected species record, find matching location record
    for species_feature in species_features.features:
        record_id = species_feature.attributes['record_id']
        
        # Query location layer for matching record_id
        location_query = f"record_id = '{record_id}'"
        location_features = location_layer.query(where=location_query)

        # Step 4: If matching location found, update ParentGlobalID in species
        if location_features.features:
            location_global_id = location_features.features[0].attributes['GlobalID']
            
            # Prepare update dictionary
            update_dict = {
                'attributes': {
                    'OBJECTID': species_feature.attributes['OBJECTID'],
                    'ParentGlobalID': location_global_id
                }
            }

            # Update the species feature
            result = species_layer.edit_features(updates=[update_dict])

            if 'updateResults' in result and result['updateResults'][0]['success']:
                print(f"Updated ParentGlobalID for species record {record_id}")
            else:
                print(f"Failed to update ParentGlobalID for species record {record_id}")
        else:
            print(f"No matching location found for species record {record_id}")

    print("ParentGlobalID update process completed.")

def main():
    gis = GIS('Pro')
    
    # Replace these item IDs with your actual layer IDs
    species_item_id = 'your_species_layer_id'
    location_item_id = 'your_location_layer_id'

    species_layer = FeatureLayer.fromitem(gis.content.get(species_item_id))
    location_layer = FeatureLayer.fromitem(gis.content.get(location_item_id))

    update_parent_global_id(species_layer, location_layer)

if __name__ == '__main__':
    main()