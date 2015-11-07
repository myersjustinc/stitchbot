#!/usr/bin/env python
import logging
from operator import itemgetter
import os
import re
import sys
import tempfile

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client.client import AccessTokenCredentials
import requests
from robobrowser import RoboBrowser


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)


def get_access_token(client_id, client_secret, refresh_token):
    r = requests.post(
        'https://www.googleapis.com/oauth2/v3/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        })
    return r.json()['access_token']


def get_drive_service():
    access_token = get_access_token(
        os.environ['GOOGLE_CLIENT_ID'],
        os.environ['GOOGLE_CLIENT_SECRET'],
        os.environ['GOOGLE_REFRESH_TOKEN'])
    http = AccessTokenCredentials(
        access_token, 'stitchbot/1.0').authorize(Http())
    service = build('drive', 'v2', http=http)
    return service


def ensure_parent(service, name='Stitchbot patterns'):
    # Look for a folder with the given name. If we find it, return its ID.
    folder_type = 'application/vnd.google-apps.folder'
    items_response = service.files().list().execute()
    for item in items_response['items']:
        if item['mimeType'] == folder_type and item['title'] == name:
            return item

    # If we're here, we haven't found one. Create one and return its ID.
    folder = service.files().insert(body={
        'title': name, 'mimeType': folder_type}).execute()
    return folder


def upload_file(service, file_name, mime_type):
    media_body = MediaFileUpload(file_name, mimetype=mime_type, resumable=True)
    base_name = os.path.basename(file_name)
    body = {
        'description': base_name,
        'title': base_name,
        'mimeType': mime_type
    }
    return service.files().insert(body=body, media_body=media_body).execute()


def move_to_parent(service, file_to_move, new_parent):
    file_to_move['parents'] = [new_parent]
    return service.files().update(
        fileId=file_to_move['id'], body=file_to_move).execute()


class StitchBot(object):
    def __init__(self, output_path=None, username=None, password=None):
        self.browser = RoboBrowser(history=True)
        self.output_path = output_path or tempfile.TemporaryDirectory().name

        self.username = username or os.environ['STITCHBOT_USERNAME']
        self.password = password or os.environ['STITCHBOT_PASSWORD']

        self.logger = logger.getChild('StitchBot')

    def log(self, level, method_name, message, *args, **kwargs):
        child_logger = self.logger.getChild(method_name)
        child_logger.log(level, message, *args, **kwargs)

    def scrape(self):
        self.log(logging.INFO, 'scrape', 'Starting scrape')

        self.log_in()
        self.navigate_to_free_pattern()
        scraped_filenames = self.download_pattern()

        self.log(logging.INFO, 'scrape', 'Scrape complete')

        return scraped_filenames

    def log_in(self):
        self.log(logging.INFO, 'log_in', 'Logging in')

        self.browser.open('http://dailycrossstitch.com/my-account/')
        form = self.browser.get_form(class_='login')
        form['username'] = self.username
        form['password'] = self.password
        self.browser.submit_form(form)

        self.log(logging.INFO, 'log_in', 'Logged in')

    def navigate_to_free_pattern(self):
        self.log(
            logging.INFO, 'navigate_to_free_pattern', 'Finding free pattern')

        self.browser.open('http://dailycrossstitch.com/')
        free_button = self.browser.find('a', class_='button', string='FREE')
        self.browser.follow_link(free_button)

        self.log(
            logging.INFO, 'navigate_to_free_pattern', 'Found free pattern')

    def download_pattern(self):
        self.log(logging.INFO, 'download_pattern', 'Downloading pattern')

        download_buttons = self.browser.find_all(
            'a', class_='single_add_to_cart_button')
        download_urls = list(map(itemgetter('href'), download_buttons))
        local_filenames = [
            self.download_pattern_file(url) for url in download_urls]

        self.log(logging.INFO, 'download_pattern', 'Downloaded pattern')

        return local_filenames

    def download_pattern_file(self, url):
        self.log(
            logging.INFO, 'download_pattern_file',
            'Downloading pattern file at {0}'.format(url))

        self.browser.open(url)
        download_script = self.browser.find(
            'script', string=re.compile(r'^\s*function startDownload'))
        if not download_script:
            return

        pdf_url_match = re.search(r'(http.+\.pdf)', download_script.string)
        if not pdf_url_match:
            return

        pdf_url = pdf_url_match.group(1)
        self.browser.open(pdf_url)

        output_filename = self.save_pattern(self.browser.response)

        self.log(
            logging.INFO, 'download_pattern_file',
            'Downloaded pattern file at {0}'.format(url))

        return output_filename

    def save_pattern(self, response):
        self.log(logging.INFO, 'save_pattern', 'Saving pattern')

        try:
            os.makedirs(self.output_path)
        except OSError:
            pass

        filename = self.get_filename(response.headers)
        output_filename = os.path.join(self.output_path, filename)
        with open(output_filename, 'wb') as output_file:
            output_file.write(response.content)

        self.log(
            logging.INFO, 'save_pattern',
            'Saved pattern to {0}'.format(output_filename))

        return output_filename

    def get_filename(self, headers, default_filename='pattern.pdf'):
        filename_match = re.search(
            r'filename="?([^"]+)"?', headers.get('Content-Disposition', ''))
        if not filename_match:
            return default_filename

        return filename_match.group(1)


def main(output_path=None, *args):
    child_logger = logger.getChild('main')

    local_filenames = StitchBot(output_path).scrape()

    # FIXME: Overwrite the same file if we already have it, rather than adding
    # multiple identically named copies of the same file.
    child_logger.info('Saving to Google Drive')
    service = get_drive_service()
    parent = ensure_parent(service)
    child_logger.info('Saving to parent ID {0}'.format(parent['id']))
    for file_name in local_filenames:
        child_logger.info('Saving {0}'.format(file_name))
        remote_file = upload_file(service, file_name, 'application/pdf')
        child_logger.info('Uploaded {0}'.format(file_name))
        move_to_parent(service, remote_file, parent)
        child_logger.info('Moved {0}'.format(file_name))
        child_logger.info('Done with {0}'.format(file_name))

    child_logger.info('Done')


if __name__ == '__main__':
    main(*sys.argv[1:])
