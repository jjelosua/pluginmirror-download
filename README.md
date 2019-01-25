pluginmirror-download
=====================

* [What is this?](#what-is-this)
* [Assumptions](#assumptions)
* [Installation](#installation)
* [Run project](#run-project)

What is this?
-------------

A repository created to bulk download the [Wordpress Plugin mirror from github](http://www.pluginmirror.com/)

This codebase is licensed under the MIT open source license. See the [LICENSE](LICENSE) file for the complete license.

Assumptions
-----------

* You are using Python 2.7. (Probably the version that came OSX.)
* You have [virtualenv](https://pypi.python.org/pypi/virtualenv) and [virtualenvwrapper](https://pypi.python.org/pypi/virtualenvwrapper) installed and working.


Installation
------------

```
cd pluginmirror-download
mkvirtualenv pluginmirror-download
pip install -r requirements.txt
```

Run Project
-----

Make sure the virtualenv is activated, if it is not run `workon pluginmirror-download`.

This project uses github api token in order to increase the rate limit allowance.

First Get your github token and store it in an envirorment variable called `GITHUB_TOKEN` or change the default value on `get_github_api_data.py`. We advise that you use enviromental variables, you can do so by using virtualenv hooks `postactivate` and `predeactivate` located in 'bin' inside your virtualenv folder.

1. Run the script scrapes metadata from the Wordpress Plugin Mirror Site
	`python scrape_pluginmirror_metadata.py`

	The results are stored in `data/pluginmirror_list.csv`

2. Run the script that using github api gets the tags from each repository and downloads it to the local machine
	`python get_github_api_data`

	The results are stored in `data/wp-plugins/`

*NOTE:* There's a glitch on one page on the plugin mirror site so either you can ignore it or add them manually, I know, but it's only 10 plugins out of 56k.