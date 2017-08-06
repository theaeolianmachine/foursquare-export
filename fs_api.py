import datetime
import requests


class FoursquareSession:
    BASE_URL = 'https://api.foursquare.com/v2'
    API_VERSION_DATE = datetime.date(2017, 5, 9).strftime('%Y%m%d')

    def __init__(self, oauth_token):
        self.session = requests.Session()
        self.oauth_token = oauth_token

        self.session.params.update({
            'oauth_token': self.oauth_token,
            'v': self.API_VERSION_DATE
        })

    def _check_rate_limits(self, response):
        calls_remaining = int(response.headers['X-RateLimit-Remaining'])
        if calls_remaining < 10:
            print("Warning: {} calls remaining to Foursquare API.".format(
                calls_remaining))

    def _get_endpoint(self, endpoint, params=None):
        if params is None:
            params = {}
        response = self.session.get(endpoint, params=params)
        self._check_rate_limits(response)
        response.raise_for_status()

        return response.json()

    def _post_endpoint(self, endpoint, params=None):
        if params is None:
            params = {}
        response = self.session.post(endpoint, params=params)
        self._check_rate_limits(response)
        response.raise_for_status()

        return response.json()

    def user_lists(self, user_id):
        endpoint = '{base_url}/users/{user_id}/lists'.format(
            base_url=self.BASE_URL, user_id=user_id)
        params = {
            'group': 'created'
        }

        return self._get_endpoint(endpoint, params)

    def fs_list(self, list_id, limit=200, offset=0):
        endpoint = '{base_url}/lists/{list_id}/'.format(
            base_url=self.BASE_URL, list_id=list_id)
        params = {
            'limit': limit,
            'offset': offset
        }

        return self._get_endpoint(endpoint, params)

    def add_to_list(self, list_id, venue_id):
        endpoint = '{base_url}/lists/{list_id}/additem'.format(
            base_url=self.BASE_URL, list_id=list_id)
        params = {
            'venueId': venue_id
        }
        return self._post_endpoint(endpoint, params)

    def delete_from_list(self, list_id, venue_id):
        endpoint = '{base_url}/lists/{list_id}/deleteitem'.format(
            base_url=self.BASE_URL, list_id=list_id)
        params = {
            'venueId': venue_id
        }
        return self._post_endpoint(endpoint, params)
