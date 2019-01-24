#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import re
import requests
from bs4 import BeautifulSoup
import shutil
from time import sleep
from csvkit.py2 import CSVKitDictReader, CSVKitDictWriter

HEADER = ["plugin_name", "plugin_page", "mirror_status", "repository_url", "tags", "master"]

cwd = os.path.dirname(__file__)
INPUT_PATH = os.path.join(cwd, 'data')
INPUT_FILE = 'pluginmirror_list'
OUTPUT_FILE = 'pluginmirror_list_donwload'
# Regex templates
github_tpl_regex = re.compile('^https://github.com/(.+?)/([^/]+).*$')
link_header_tpl_regex = re.compile('^.*<(.*)>;\s*rel="next".*$')
# Github api token
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN','GITHUB_TOKEN')


def download_tag(row, tag):
    """
    download tag zipball
    """
    tag_name = tag['zipball_url'].split('/')[-1]
    OUTPUT_PATH = '%s/%s/%s' % (INPUT_PATH, row['owner'], row['repo'])
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    fname = '%s.zip' % (tag_name.replace('.zip', '').replace(".", "_").replace("-", "_"))
    fpath = '%s/%s' % (OUTPUT_PATH, fname)
    row['fpath'] = fpath
    if os.path.isfile(fpath):
        return None
    else:
        try:
            r = requests.get(tag['zipball_url'], stream=True)
            if (r.status_code != 200):
                print "found error %s for %s" % (r.status_code, row['repository_url'])
                return None
            with open(fpath, 'wb') as of:
                shutil.copyfileobj(r.raw, of)
            del r
        except Exception, e:
            print e
            print "Error while downloading {}...skipping" % (tag['zipball_url'])
            return None
    return True


def get_trunk(row):
    """
    download master branch current contents
    """
    participation = None

    # Github API v3 list of commits
    result = download_tag(row,
        {'zipball_url': 'https://github.com/%s/%s/archive/master.zip' % (
            row['owner'],row['repo'])})
    if result:
        row['master'] = 1
    return row


def get_tags(row, url):
    """
    Download the available tags using Github API v3
    """

    # Github API v3 list of commits
    next_url = None
    r = make_request(url,{'Authorization': 'token %s' % (GITHUB_TOKEN)})
    if r.status_code == 200:
        tags = r.json()
        if not len(r.json()):
            return row, next_url

        for tag in tags:
            result = download_tag(row, tag)
            if result:
                row['tags'] = 1

        if 'link' in r.headers:
            m = link_header_tpl_regex.match(r.headers['link'])
            if m:
                next_url = m.group(1)
                print next_url
    else:
        print "unexpected status_code %s for repo %s" % (r.status_code, row['repository_url'])

    return row, next_url


def make_request(url, headers):
    """
    make an http request
    """
    r = None
    try:
        r = requests.get(url, headers=headers)
    except Exception as e:
        raise e
    return r


def get_pluginmirror_data():
    """
    get previously calculated npm metadata results
    """
    try:
        with open('%s/%s.csv' % (INPUT_PATH, INPUT_FILE), 'r') as f:
            reader = CSVKitDictReader(f)
            return list(reader)
    except IOError as e:
        return list()


def run(args):
    """
    main loop
    """

    rows = get_pluginmirror_data()

    with open('%s/%s.csv' %
              (INPUT_PATH, OUTPUT_FILE), 'w') as fout:
        writer = CSVKitDictWriter(fout, fieldnames=HEADER, extrasaction='ignore')
        writer.writeheader()
        # Allow the script to jump start after network glitches
        count = args.start
        for row in rows[args.start:]:
            if row['repository_url']:
                count +=1

                if (count % 50 == 0):
                    print('processed %s github repos' % (count))

                m = github_tpl_regex.match(row['repository_url'])
                if m:
                    row['owner'] = m.group(1)
                    row['repo'] = m.group(2)
                else:
                    print "could not extract owner and repo from github repo url %s" % (row['repository_url'])
                    continue

                GITHUB_TAGS_API_TPL = "https://api.github.com/repos/%(owner)s/%(repo)s/tags"
                url = GITHUB_TAGS_API_TPL % {'owner': row['owner'], 'repo': row['repo']}
                while url:
                    row, url = get_tags(row, url)
                row = get_trunk(row)
                sleep(1.1)
            else:
                print 'repository not found, maybe mirror was cloning %s' % (row['plugin_page'])
                row['download_status'] = None
            writer.writerow(row)


if __name__ == '__main__':
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="Scrape http://www.pluginmirror.com/plugins")
    parser.add_argument("-s", "--start", type=int, default=0,
                    help="The starting page")
    args = parser.parse_args()
    run(args)