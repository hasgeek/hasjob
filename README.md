HasGeek Job Board -- beta
=========================

Code for HasGeek's job board at http://jobs.hasgeek.com/

You are welcome to contribute a patch or use this code to run your own job
board under the terms of the BSD license, but please design your own UI.
Don't copy ours. We will like you better if you contribute a patch.

This code runs on [Python][] with the [Flask][] microframework. You will need
to install all the requirements listed in `requirements.txt` using
`easy_install` or `pip` or run `setup.sh` which shall install all the packages
mentioned in requirements.txt. Copy `settings-sample.py` to `settings.py`, edit as
necessary, and start the server with:

    $ python website.py

WSGI is recommended for production. Enable `mod_wsgi` in Apache and make a
`VirtualHost` with:

    WSGIScriptAlias / /path/to/website.wsgi

[Python]: http://python.org/
[Flask]: http://flask.pocoo.org/
