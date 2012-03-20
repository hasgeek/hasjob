# Classifieds

[![Build Status](https://secure.travis-ci.org/caulagi/classifieds.png?branch=master)](http://travis-ci.org/caulagi/classifieds)

classifieds is a [Flask][] based web app that is free to use.
You can get started in less that 2 minutes.  There is a demo
version of this app at [demo][]

## Install and setup

    pip install -r requirements.txt`
    cp settings-sample.py settings.py ; edit as necessary

## Tests

    nosetests --with-coverage --cover-package=admin,app,assets,forms,get-twitter,loghandler,models,search,twitter,uploads,utils,views,website

## Run

For dev setup

    $ python website.py

WSGI is recommended for production. Enable `mod_wsgi` in Apache and make a
`VirtualHost` with:

    WSGIScriptAlias / /path/to/website.wsgi

## Acknowledgements

As is evident from the git history, classifieds is a fork of [hasjob][]

## License

Classifieds is MIT licensed.  See the accompanying LICENSE for legalese.

[hasjob]: https://github.com/hasgeek/hasjob/
[Flask]: http://flask.pocoo.org/
[demo]: http://classifieds.caulagi.com/
