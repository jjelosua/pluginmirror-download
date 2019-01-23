#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import re
import requests
from bs4 import BeautifulSoup
import datetime
from time import sleep
from csvkit.py2 import CSVKitDictReader, CSVKitDictWriter

HEADER = ["plugin_name", "plugin_page", "mirror_status", "repository_url"]
INITIAL_URL = "http://www.pluginmirror.com/plugins"
cwd = os.path.dirname(__file__)
OUTPUT_PATH = os.path.join(cwd, 'data')
DATA_FILE = 'pluginmirror_list'


def make_request(url, headers=None):
    """
    make an http request
    """
    r = None
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        raise e
    return r


def scrape_pluginmirror_page(pagenum, cache):
    """
    """
    plugins = []
    url = "%s?page=%s&sort=created&direction=asc" % (INITIAL_URL, pagenum)
    r = make_request(url)
    # If we receive a too many requests status code sleep for 5 minutes since
    # the site does not provide a Retry-after header and retry one more time
    if r.status_code == 429:
        sleep(5*60)
        r = make_request(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    rows = soup.find('div', class_='large-9').select("div[class='row']")
    for row in rows:
        plugin = {}
        link = row.find('div', class_='large-9').find('a')
        plugin['plugin_name'] = link.text.strip()
        plugin['plugin_page'] = '%s%s' % ('http://www.pluginmirror.com', link['href'])
        repo = row.find('div', class_='large-3').find('a', class_="button")
        if repo['href'].startswith('javascript'):
            plugin['mirror_status'] = 'ko'
        else:
            plugin['repository_url'] = repo['href']
            plugin['mirror_status'] = 'ok'
        if plugin_page in cache:
            continue
        plugins.append(plugin)
    return plugins


def get_total_number_of_pages():
    """
    Get the last page from the plugins pagination section
    """
    r = make_request(INITIAL_URL)
    soup = BeautifulSoup(r.content, 'html.parser')
    pages = soup.find('ul', class_='pagination').find_all('li')
    # Get the last page from the plugins pagination
    # the one before the arrow list element
    num_pages = int(pages[len(pages)-2].text)
    return num_pages

def get_previous_results():
    """
    get previous results and use them as a cache as a polite gesture to npm servers
    you can use the --no-cache flag to start fresh instead
    """
    try:
        with open('%s/%s.csv' % (OUTPUT_PATH, DATA_FILE), 'r') as f:
            reader = CSVKitDictReader(f)
            return list(reader)
    except IOError as e:
        return list()


def run(args):
    """
    main loop
    """

    prev_rows = []
    cache = set()
    # Restore cached package metadata if available and not overwritten by flag
    if not args.no_cache:
        prev_rows = get_previous_results()
        cache = set([r['plugin_page'] for r in prev_rows])

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    num_pages = get_total_number_of_pages()
    with open('%s/%s.csv' %
              (OUTPUT_PATH, DATA_FILE), 'w') as fout:
        writer = CSVKitDictWriter(fout, fieldnames=HEADER, extrasaction='ignore')
        writer.writeheader()
        # Write previous rows if available and we are using cache
        writer.writerows(prev_rows)

        count = 0
        for p in range(args.start, num_pages+1):
            count +=1
            # Found bug on html of a repo that causes script to break
            # Treat manually, see: http://www.pluginmirror.com/plugins?page=2344&sort=created&direction=asc
            if p == 2344:
                continue
            plugins = scrape_pluginmirror_page(p, cache)
            writer.writerows(plugins)

            if (count % 100 == 0):
                print('processed %s plugin mirror pages' % (count))
            sleep(1.1)


if __name__ == '__main__':
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="Scrape http://www.pluginmirror.com/plugins")
    parser.add_argument('--no-cache',
                        dest='no_cache',
                        action='store_true')
    parser.add_argument("-s", "--start", type=int, default=1,
                    help="The starting page")
    args = parser.parse_args()
    run(args)