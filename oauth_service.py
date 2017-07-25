import json
import os

from flask import Flask, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.config.from_object('config.default.DefaultConfig')
app.config.from_pyfile('oauth_config.py', silent=True)


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@app.route("/")
def reroute_to_auth():
    return redirect(url_for("authenticate_to_foursquare"))


@app.route("/foursquare/auth")
def authenticate_to_foursquare():
    fs_auth_url = 'https://foursquare.com/oauth2/authenticate'

    fs_session = OAuth2Session(
        app.config['FS_CLIENT_ID'], redirect_uri=app.config['FS_REDIRECT_URL'])
    auth_url, state = fs_session.authorization_url(fs_auth_url)
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route("/foursquare/oauth_redirect")
def store_from_redirect():
    fs_token_url = 'https://foursquare.com/oauth2/access_token'

    fs_session = OAuth2Session(
        app.config['FS_CLIENT_ID'], state=session['oauth_state'],
        redirect_uri=app.config['FS_REDIRECT_URL'])

    token = fs_session.fetch_token(
        fs_token_url, client_secret=app.config['FS_CLIENT_SECRET'],
        authorization_response=request.url)

    with open("oauth_token.json", "w") as token_file:
        json.dump(token, token_file, indent=2)

    return "Successfully stored token to oauth_token"
