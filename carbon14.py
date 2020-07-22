#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Carbon14
# Copyright 2017-2020 Andrea Lazzarotto
#
# Carbon14 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Carbon14 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Carbon14. If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function

import argparse
import logging
import pytz
import requests
import sys
import tzlocal
from colorama import Fore
from colorama import init
from colorama import Style
from datetime import datetime
from email.utils import parsedate
from lxml import etree
from six.moves.urllib.parse import urljoin
from six.moves.urllib.parse import urlparse

local_timezone = tzlocal.get_localzone()

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}


def log(message):
    print('{}{}'.format(Style.DIM, message), file=sys.stderr)


def warning(message):
    print('{}{}'.format(Fore.YELLOW, message), file=sys.stderr)


def error(message):
    print('{}{}'.format(Style.BRIGHT + Fore.RED, message), file=sys.stderr)


def localize(utc):
    return utc.replace(tzinfo=pytz.utc).astimezone(local_timezone)


def readable_date(value):
    return value.strftime('%Y-%m-%d %H:%M:%S')


class Result(object):
    def __init__(self, timestamp, absolute, internal):
        self.timestamp = timestamp
        self.absolute = absolute
        self.internal = internal


class Analysis(object):
    def __init__(self, url, author, tor):
        self.url = url
        self.tor = tor
        self.author = author
        self.images = []
        self.end = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0'
        })
        if(tor):
            self.session.proxies.update(proxies)

    def handle_image(self, address, requested):
        if address is None or address in requested:
            return
        requested.add(address)
        log('Working on image {}'.format(address))
        absolute = urljoin(self.url, address)
        try:
            headers = self.session.get(absolute, stream=True).headers
            parsed = parsedate(headers['Last-Modified'])
            timestamp = datetime(*parsed[:6], tzinfo=pytz.utc)
        except:
            warning('Cannot fetch date for this image')
            return
        internal = urlparse(self.url).netloc == urlparse(absolute).netloc
        self.images.append(Result(timestamp, absolute, internal))

    def run(self):
        self.start = datetime.now(tz=pytz.utc)
        log('Fetching page {}'.format(self.url))
        try:
            self.request = self.session.get(self.url)
        except:
            error('Error fetching page!')
            return

        html = etree.HTML(self.request.text)

        # Extract page title
        titles = html.cssselect('title')
        self.title = titles[0].text if len(titles) else None

        # Loop through all images
        images = html.cssselect('img')
        requested = set()
        for image in images:
            if 'src' not in image.attrib:
                continue
            address = image.attrib['src']
            if address.startswith('data:'):
                continue
            self.handle_image(address, requested)
        opengraph = html.cssselect('meta[property="og:image"]')
        for image in opengraph:
            address = image.attrib['content']
            self.handle_image(address, requested)

        self.end = datetime.now(tz=pytz.utc)
        self.images.sort(key=lambda i: i.timestamp)

    def report_section(self, title, selector):
        print('\n{}# {}\n'.format(Fore.RED, title))
        filtered = list(filter(selector, self.images))
        if not len(filtered):
            print('Nothing found.')
            return

        print('{}{}'.format(Style.DIM, '-'*80))
        labels = ('Date (UTC)', 'Date ({})'.format(local_timezone), 'URL')
        print('{}{:20} {:20} {}'.format(Style.BRIGHT, *labels))
        print('{}{} {} {}'.format(Style.DIM, '-'*20, '-'*20, '-'*38))
        for result in filtered:
            print('{:20} {:20} <{}>\n'.format(
                readable_date(result.timestamp),
                readable_date(localize(result.timestamp)),
                result.absolute
            ))
        print('{}{}'.format(Style.DIM, '-'*80))


    def report(self):
        # Preamble
        print('---')
        print(r'title: {}Carbon14 web page analysis'.format(Fore.MAGENTA))
        if self.author:
            print(r'author: {}{}'.format(Fore.MAGENTA, self.author))
        print(r'date: {}{}'.format(Fore.MAGENTA, self.start.strftime('%Y-%m-%d')))
        print('---')
        print('\n{}# General information\n'.format(Fore.RED))
        started = localize(self.start)
        ended = localize(self.end)
        metadata = [
            ('Page URL', '<{}>'.format(self.url)),
            ('Page title', self.title),
            ('Analysis started', '{} ({})'.format(readable_date(started), started.tzinfo)),
            ('Analysis ended', '{} ({})'.format(readable_date(ended), ended.tzinfo))
        ]
        for label, value in metadata:
            print(u'- {}**{}:**{} {}'.format(Style.BRIGHT + Fore.CYAN, label, Style.RESET_ALL, value))

        # Format HTTP headers as code
        headers = '\n'.join('    {}: {}'.format(label, self.request.headers[label]) for label in self.request.headers)
        print(u'\n{}# HTTP headers\n'.format(Fore.RED))
        print(headers)

        # Sections
        self.report_section('Internal images', lambda x: x.internal)
        self.report_section('External images', lambda x: not x.internal)
        self.report_section('All images', lambda x: True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Date images on a web page.')
    parser.add_argument('url', help='URL of the page')
    parser.add_argument('-a', '--author', metavar='name', help='author to be included in the report')
    parser.add_argument('-t', '--tor', help='use Carbon14 to analyze an hidden service',action="store_true")
    args = parser.parse_args()

    # Prepare colorama
    init(autoreset=True)

    analysis = Analysis(args.url, args.author, args.tor)
    analysis.run()
    if analysis.end:
        analysis.report()
