import gc
import numpy as np
import pandas as pd
from pathlib import Path

def process_catch(filepath: Path) -> pd.DataFrame:
    """Process single CATCH excel export chunk."""
    columns_trip = [
        'today', 'deviceid', 'survey_real', 'survey_type', '_gps_latitude', '_gps_longitude',
        'data_collector', 'landing_site', 'landings', 'trip_info', 'boat_type', 'other_boat',
        'engine_yn', 'engine', 'gear_type', 'gear_type_other', 'fishing_ground_name',
        'fishing_location', 'fishing_ground_type', 'fishing_ground_depth', 'fishing_duration',
        'people', 'boats_landed', '_id', '_uuid', '_submission_time', '_tags', '_index'
    ]
    columns_catch = [
        'group_catch', 'species_catch', 'weight_catch', 'nb_buckets_catch',
        'wgt_buckets_catch', 'nb_ind_catch', 'wgt_ind_catch', '_submission__uuid'
    ]

    trips = pd.read_excel(filepath, sheet_name=0, engine='openpyxl', usecols=columns_trip)
    catch = pd.read_excel(filepath, sheet_name=1, engine='openpyxl', usecols=columns_catch)

    merged = trips.merge(catch, left_on='_uuid', right_on='_submission__uuid', how='left')
    del trips, catch
    gc.collect()

    merged = merged[merged['survey_real'] == 'real']
    merged = merged[merged['survey_type'] == 'catch']

    merged.loc[merged['gear_type_other'] == 'Handline', 'gear_type/pole_line'] = 1
    merged.loc[merged['gear_type_other'] == 'Handline', 'gear_type'] = 'hand_line'
    merged.loc[merged['gear_type'] == 'pole_line', 'gear_type'] = 'hand_line'
    merged = merged.rename(columns={'gear_type/pole_line': 'gear_type/hand_line'})

    merged['fishing_duration'] = merged['fishing_duration'].replace({'>3': 4})
    merged.loc[merged['fishing_duration'] == '>3', 'fishing_duration'] = 4
    merged.loc[merged['fishing_duration'].isna(), 'fishing_duration'] = 1

    merged['people'] = merged['people'].astype(float)
    return merged

def process_shark(filepath: Path) -> pd.DataFrame:
    """Process single SHARK excel export chunk."""
    columns_trip = [
        'start', 'end', 'today', 'survey_type', '_gps_latitude', '_gps_longitude', 'survey',
        'landing_site', 'market', 'surveyor', 'catch_info', 'boat_type', 'other_boat', 'engine',
        'fishing_location', 'fishing_start', 'fishing_end', 'targeted', 'last_catch_shark_ray',
        'release_shark_ray', 'nb_sharks_unsampled', 'nb_rays_unsampled',
        'nb_shark_like_rays_unsampled', 'market_info', 'shark_ray_vendors_nb', '_uuid'
    ]
    columns_catch = [
        'type', 'genus', 'species', 'local_name', 'sex', 'weight', 'disc_width', 'disc_length',
        'total_length', 'fork_length', 'precaudal_length', 'gear_type', 'gear_type/basket_traps',
        'gear_type/hook_line', 'gear_type/spear_gun', 'gear_type/beach_seines',
        'gear_type/ring_nets', 'gear_type/gill_nets_3', 'gear_type/gill_nets_6',
        'gear_type/longline', 'gear_type/reef_seine_set_net', 'gear_type/drift_net',
        'gear_type/other', 'gear_type_other', 'price_sold_for', 'price_sold_usd',
        '_submission__uuid'
    ]

    trip = pd.read_excel(filepath, sheet_name='SHARC', engine='openpyxl', usecols=columns_trip)
    catch = pd.read_excel(filepath, sheet_name='catch_details', engine='openpyxl', usecols=columns_catch)

    merged = trip.merge(catch, left_on='_uuid', right_on='_submission__uuid', how='left')
    del trip, catch
    gc.collect()

    merged['landing_site'] = merged['landing_site'].str.lower()
    merged['Scientific_name'] = merged['species']
    merged.loc[merged['type'] == 'Shark-like ray', 'type'] = 'Shark-like Ray'
    merged['type'] = merged['type'].str.capitalize()

    old_data_mask = merged['surveyor'] == 'old data from Collect'
    merged.loc[old_data_mask, 'Scientific_name'] = (
        merged.loc[old_data_mask, 'genus'].fillna('') + ' ' + merged.loc[old_data_mask, 'species'].fillna('')
    )

    merged['Scientific_name'] = merged['Scientific_name'].str.replace('  ', ' ')
    merged['Scientific_name'] = merged['Scientific_name'].str.capitalize()

    merged.loc[merged['_gps_longitude'] == '', ['_gps_longitude']] = np.nan
    merged.loc[merged['_gps_latitude'] == '', ['_gps_latitude']] = np.nan
    merged['_gps_latitude'] = merged['_gps_latitude'].astype(float)
    merged['_gps_longitude'] = merged['_gps_longitude'].astype(float)

    return merged

def process_restoration(filepath: Path) -> pd.DataFrame:
    """Process single RESTORATION excel export chunk."""
    gc.collect()
    return pd.read_excel(filepath, engine='openpyxl')

def transform_chunk(dataset: str, filepath: Path) -> pd.DataFrame:
    """Route dataset transformation by name."""
    if dataset == 'CATCH':
        return process_catch(filepath)
    elif dataset == 'SHARK':
        return process_shark(filepath)
    elif dataset == 'RESTORATION':
        return process_restoration(filepath)
    raise ValueError(f"Unknown dataset type: {dataset}")
