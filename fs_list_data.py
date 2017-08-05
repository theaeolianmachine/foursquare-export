import functools
import json
import os.path

import numpy as np
import pandas as pd
from pandas import DataFrame


import fs_api


def cache_as_json(json_fname):
    def decorate(func):
        @functools.wraps(func)
        def read_or_store_as_json(*args, **kwargs):
            if os.path.exists(json_fname):
                return read_from_json(json_fname)
            else:
                data = func(*args, **kwargs)
                write_to_json(data, json_fname)
                return data
        return read_or_store_as_json
    return decorate


def cache_df_as_json(json_fname):
    def decorate(func):
        @functools.wraps(func)
        def read_or_store_df_as_json(*args, **kwargs):
            if os.path.exists(json_fname):
                return pd.read_json(json_fname)
            else:
                data_frame = func(*args, **kwargs)
                data_frame.to_json(json_fname)
                return data_frame
        return read_or_store_df_as_json
    return decorate


@cache_as_json('user_lists.json')
def retrieve_user_lists(fs_session, user_id):
    return fs_session.user_lists(user_id)


@cache_df_as_json('list_items.json')
def retrieve_fs_lists(fs_session, user_id, list_ids):
    list_items = []
    for list_id in list_ids:
        list_items.append(retrieve_fs_list(fs_session, list_id))
    list_items.append(
        retrieve_fs_list(fs_session, '{}/todos'.format(user_id)))

    list_items_df = pd.concat(list_items, ignore_index=True)
    return list_items_df


def retrieve_fs_list(fs_session, list_id):
    limit = 200
    offset = 0
    list_pages = []

    list_json = fs_session.fs_list(list_id, offset=offset)
    list_items = list_json['response']['list']['listItems']
    list_size = list_items['count']

    list_pages.append(DataFrame(list_items['items']))
    remaining_in_list = list_size - limit

    while remaining_in_list > 0:
        offset += limit
        list_json = fs_session.fs_list(list_id, offset=offset)
        list_items = list_json['response']['list']['listItems']
        list_pages.append(DataFrame(list_items['items']))
        remaining_in_list -= limit

    list_df = pd.concat(list_pages, ignore_index=True)
    return list_df


@cache_df_as_json('venues.json')
def clean_venues(list_items_df):
    venues_df = DataFrame(
        list_items_df['venue'].dropna().tolist(),
        columns=(
            'categories', 'closed', 'id', 'location', 'name', 'price',
            'rating'))

    # Remove duplicate venues
    venues_df.drop_duplicates('id', inplace=True)
    # Set index as the venue ID
    venues_df.set_index('id', drop=False, inplace=True)

    # Remove closed venues
    venues_df.closed = venues_df.closed.fillna(False).astype(np.bool)
    venues_df = venues_df[~venues_df.closed]
    venues_df.drop('closed', axis=1, inplace=True)

    # Convert category dicts to the names of the categories
    venues_df.categories = venues_df.categories.map(lambda l: l[0].get('name'))
    venues_df.rename(columns={'categories': 'category'}, inplace=True)

    # Convert location info
    venues_df.loc[:, 'address'] = venues_df.location.dropna().map(
        lambda d: '\n'.join(d.get('formattedAddress')))
    venues_df.loc[:, 'lat'] = venues_df.location.dropna().map(
        lambda d: d.get('lat'))
    venues_df.loc[:, 'lng'] = venues_df.location.dropna().map(
        lambda d: d.get('lng'))
    venues_df.loc[:, 'city'] = venues_df.location.dropna().map(
        lambda d: d.get('city'))
    venues_df.loc[:, 'state'] = venues_df.location.dropna().map(
        lambda d: d.get('state'))
    venues_df.loc[:, 'postal_code'] = venues_df.location.dropna().map(
        lambda d: d.get('postalCode'))
    venues_df.loc[:, 'city_state'] = venues_df.apply(
        lambda r: '{}, {} {}'.format(r['city'], r['state'], r['postal_code']),
        axis=1)
    venues_df.drop('location', axis=1, inplace=True)

    # Convert prices to a series of $'s based on the price tier, a la Yelp ($,
    # $$, $$$, $$$$)
    venues_df.price = venues_df.price.dropna().map(
        lambda d: '$' * d['tier'] if 'tier' in d else None)
    venues_df.price = venues_df.price.fillna('?')

    return venues_df


def read_from_json(fname):
    with open(fname) as fobj:
        return json.load(fobj)


def write_to_json(data, fname):
    with open(fname, 'w') as fobj:
        json.dump(data, fobj, indent=2, sort_keys=True)


def main():
    token_json = read_from_json('oauth_token.json')
    fs_config = read_from_json('fs_list_data_config.json')
    fs_session = fs_api.FoursquareSession(token_json['access_token'])
    user_lists_response = retrieve_user_lists(fs_session, fs_config['user_id'])
    user_lists_df = DataFrame(
        user_lists_response['response']['lists']['items'])
    list_ids = user_lists_df['id']
    list_items_df = retrieve_fs_lists(
        fs_session, fs_config['user_id'], list_ids)
    clean_venues(list_items_df)


if __name__ == '__main__':
    main()
