#!/usr/bin/env python
import logging
from operator import itemgetter
import os
import re
import sys

from robobrowser import RoboBrowser


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)


class StitchBot(object):
    def __init__(self, output_path, username=None, password=None):
        self.browser = RoboBrowser(history=True)
        self.output_path = output_path

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
        self.download_pattern()

        self.log(logging.INFO, 'scrape', 'Scrape complete')

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
        for url in download_urls:
            self.download_pattern_file(url)

        self.log(logging.INFO, 'download_pattern', 'Downloaded pattern')

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

        self.save_pattern(self.browser.response)

        self.log(
            logging.INFO, 'download_pattern_file',
            'Downloaded pattern file at {0}'.format(url))

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

    def get_filename(self, headers, default_filename='pattern.pdf'):
        filename_match = re.search(
            r'filename="?([^"]+)"?', headers.get('Content-Disposition', ''))
        if not filename_match:
            return default_filename

        return filename_match.group(1)


def main(output_path=None, *args):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), 'output')

    StitchBot(output_path).scrape()


if __name__ == '__main__':
    main(*sys.argv[1:])
