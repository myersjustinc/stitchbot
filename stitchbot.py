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


class DriveFolder(object):
    def __init__(self, folder_name):
        self.folder_name = folder_name

        self.logger = logger.getChild('DriveFolder')

        self.service = self._get_drive_service(self._get_access_token())

        self.folder = self.ensure_folder()
        self.log(
            logging.INFO, '__init__',
            'Saving to folder ID {0}'.format(self.folder['id']))

    def log(self, level, method_name, message, *args, **kwargs):
        child_logger = self.logger.getChild(method_name)
        child_logger.log(level, message, *args, **kwargs)

    def upload_files(self, local_filenames):
        for file_name in local_filenames:
            self.log(
                logging.INFO, 'upload_files', 'Saving {0}'.format(file_name))

            self.remove_file_if_exists(file_name, 'application/pdf')
            remote_file = self.upload_file(file_name, 'application/pdf')
            self.move_to_parent(remote_file)

            self.log(
                logging.INFO, 'upload_files',
                'Done with {0}'.format(file_name))

    def list_items(self):
        # Use the cached version of this list if available.
        if hasattr(self, '_items'):
            self.log(logging.INFO, 'list_items', 'Using cached list of items')
            return self._items

        # Get a list of all items this application has stored, traversing
        # paginated results as necessary.
        items = []
        resource = self.service.files()
        request = resource.list()
        while request is not None:
            page = request.execute()
            items.extend(page['items'])
            request = resource.list_next(request, page)

        # Cache and return the list.
        self.log(logging.INFO, 'list_items', 'Caching list of items')
        self._items = items
        return items

    def ensure_folder(self):
        # Look for a folder with the given name. If we find it, return it.
        folder_type = 'application/vnd.google-apps.folder'
        for item in self.list_items():
            if (
                    item['mimeType'] == folder_type and
                    item['title'] == self.folder_name):
                return item

        # If we're here, we haven't found one. Create one and return it.
        folder = self.service.files().insert(body={
            'title': self.folder_name, 'mimeType': folder_type}).execute()
        return folder

    def remove_file_if_exists(self, file_name, mime_type):
        base_name = os.path.basename(file_name)
        for item in self.list_items():
            if item['title'] == base_name and item['mimeType'] == mime_type:
                self.service.files().delete(fileId=item['id']).execute()
                self.log(
                    logging.INFO, 'remove_file_if_exists',
                    'Removed existing {0}'.format(base_name))
                return True
        return False

    def upload_file(self, file_name, mime_type):
        media_body = MediaFileUpload(
            file_name, mimetype=mime_type, resumable=True)
        base_name = os.path.basename(file_name)
        body = {
            'description': base_name,
            'title': base_name,
            'mimeType': mime_type
        }
        response = self.service.files().insert(
            body=body, media_body=media_body).execute()
        self.log(logging.INFO, 'upload_file', 'Uploaded {0}'.format(file_name))
        return response

    def move_to_parent(self, file_to_move):
        file_to_move['parents'] = [self.folder]
        response = self.service.files().update(
            fileId=file_to_move['id'], body=file_to_move).execute()
        self.log(
            logging.INFO, 'upload_files',
            'Moved {0}'.format(file_to_move['title']))
        return response

    def _get_access_token(self):
        r = requests.post(
            'https://www.googleapis.com/oauth2/v3/token',
            data={
                'client_id': os.environ['GOOGLE_CLIENT_ID'],
                'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
                'grant_type': 'refresh_token',
                'refresh_token': os.environ['GOOGLE_REFRESH_TOKEN'],
            })
        return r.json()['access_token']

    def _get_drive_service(self, access_token):
        http = AccessTokenCredentials(
            access_token, 'stitchbot/1.0').authorize(Http())
        service = build('drive', 'v2', http=http)
        return service


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
    local_filenames = StitchBot(output_path).scrape()
    DriveFolder('Stitchbot patterns').upload_files(local_filenames)


if __name__ == '__main__':
    main(*sys.argv[1:])
