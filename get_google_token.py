#!/usr/bin/env python
import os
import sys
import webbrowser

from oauth2client.client import OAuth2WebServerFlow


def get_credentials(scopes):
    flow = OAuth2WebServerFlow(
        client_id=os.environ['GOOGLE_CLIENT_ID'],
        client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
        scope=' '.join(scopes),
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_uri = flow.step1_get_authorize_url()
    webbrowser.open(auth_uri)

    auth_code = input('Enter the authorization code you receive here: ')
    credentials = flow.step2_exchange(auth_code)

    return credentials


def main(*scopes):
    if not scopes:
        sys.stderr.write('You need to specify at least one scope.\n')
        sys.exit(1)

    credentials = get_credentials(scopes)
    refresh_token = credentials.refresh_token

    sys.stdout.write('Refresh token: {0}\n'.format(refresh_token))


if __name__ == '__main__':
    main(*sys.argv[1:])
