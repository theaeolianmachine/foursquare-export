import datetime
import os.path
import subprocess

# from pandas import DataFrame
import pandas as pd
import requests

import fs_api
from common import read_from_json, write_to_json


def copy_to_clipboard(text):
    subprocess.run(['pbcopy'], input=text.encode())


def venue_url(venue_id):
    return 'https://www.foursquare.com/v/{}'.format(venue_id)


def venue_info_str(venue):
    venue_str = (
        'Categorizing: {venue_name}\n\nCategory: {category}\n'
        'City, State: {city_state}\nPrice: {price}\nRating: {rating}\n'
        'URL: {url}'
    ).format(
        venue_name=venue['name'], category=venue['category'],
        city_state=venue['city_state'], price=venue['price'],
        rating=venue['rating'],
        url=venue_url(venue['id']))

    return venue_str


def choices_str(choices_to_lists):
    choices_str = '\n'.join(
        '{choice_num}) {name}'.format(
            choice_num=choice, name=choices_to_lists[choice]['name'])
        for choice in choices_to_lists
    )

    return choices_str


def parse_choice(choice_str, choices_to_lists):
    while True:
        if choice_str == "" or choice_str.lower().startswith('s'):
            return 'SKIP'
        elif choice_str.lower().startswith('q'):
            return 'QUIT'
        try:
            numeric_choice = int(choice_str)
        except ValueError:
            print(
                'Your choice was neither skip nor a valid number. Please '
                're-enter your choice.')
        else:
            if numeric_choice not in choices_to_lists:
                print(
                    'Your choice was not in the range of valid choices '
                    'Please re-enter your choice.')
            else:
                return choices_to_lists[numeric_choice]['id']


def get_venues_json(fname):
    if os.path.exists(fname):
        return set(read_from_json(fname))
    else:
        return set()


def save_venues_json(fname, new_venues):
    if os.path.exists(fname):
        old_venues = set(read_from_json(fname))
        new_venues = new_venues | old_venues
    write_to_json(list(new_venues), fname)


def get_skipped_venues():
    return get_venues_json('skipped_venues.json')


def get_categorized_venues():
    return get_venues_json('categorized_venues.json')


def save_skipped_venues(new_venues):
    save_venues_json('skipped_venues.json', new_venues)


def save_categorized_venues(new_venues):
    save_venues_json('categorized_venues.json', new_venues)


def main():
    fs_session = fs_api.FoursquareSession(
        read_from_json('oauth_token.json')['access_token'])
    venues_df = pd.read_json('venues.json')
    user_lists = read_from_json('fs_lists.json')['lists']
    choices_to_lists = {
        i + 1: item for i, item in enumerate(user_lists)
    }
    options_str = choices_str(choices_to_lists)
    categorized_venues = get_categorized_venues()
    skipped_venues = get_skipped_venues()
    completed_venues = categorized_venues | skipped_venues

    if completed_venues:
        venues_df = venues_df[~venues_df['id'].isin(completed_venues)]

    try:
        for i, index in enumerate(venues_df.index):
            current_venue = venues_df.loc[index]
            copy_to_clipboard(venue_url(current_venue['id']))
            print(
                'Processing venue #{}/{}'.format(i + 1, venues_df.index.size))
            print(venue_info_str(current_venue))
            print('\nChoices:')
            print(options_str)
            print('s) Skip?')
            print('q) Quit?')
            print('\nWhat would you like to do with this venue?')
            choice = input('--> ')
            choice_result = parse_choice(choice, choices_to_lists)
            if choice_result == 'SKIP':
                print('Skipping over {}...'.format(current_venue['name']))
                skipped_venues.add(current_venue['id'])
            elif choice_result == 'QUIT':
                print('Exiting and saving!')
                break
            else:
                print('Adding {} to list {}'.format(
                    current_venue['name'], choice_result))
                fs_session.add_to_list(choice_result, current_venue['id'])
                categorized_venues.add(current_venue['id'])
            print()
    except requests.HTTPError as ex:
        if ex.response.status_code == 403 and (
                    'X-RateLimit-Reset' in ex.response.headers):
                reset_time = datetime.datetime.from_timestamp(
                    ex.response.headers['X-RateLimit-Reset']).strftime(
                        '%Y-%m-%d %H:%M:S')
                print('Over rate limit, next reset time is: '
                      '{}'.format(reset_time))
        save_categorized_venues(categorized_venues)
        save_skipped_venues(skipped_venues)
    except Exception:
        save_categorized_venues(categorized_venues)
        save_skipped_venues(skipped_venues)
        raise
    else:
        print("Completed!")
        save_categorized_venues(categorized_venues)
        save_skipped_venues(skipped_venues)


if __name__ == '__main__':
    main()
