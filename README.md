Hasjob
======

Code for Hasjob, HasGeek's job board at https://hasjob.co/

You are welcome to contribute a patch or use this code to run your own job
board under the terms of the BSD license, but please design your own UI.
Don't copy ours and confuse users into thinking you are affiliated with us.
We will like you better if you contribute a patch.

Hasjob runs on [Python][] with the [Flask][] microframework. You will need
to install all the requirements listed in `requirements.txt` using
`easy_install` or `pip`:

    $ pip install -r requirements.txt

Next, Copy `settings-sample.py` to `settings.py`, edit as
necessary, and finish configuration with:

    $ python manage.py db create
    $ python manage.py configure

To run the server in development mode:

    $ python runserver.py

WSGI is recommended for production. For Apache: enable `mod_wsgi` and make a
`VirtualHost` with:

    WSGIScriptAlias / /path/to/website.wsgi

For Nginx, run website.py under uWSGI and proxy to it:

    location / {
        include uwsgi_params; # Include common uWSGI settings here
        uwsgi_pass 127.0.0.1:8093;
        uwsgi_param UWSGI_CHDIR /path/to/hasjob/git/repo/folder;
        uwsgi_param UWSGI_MODULE website;
    }


[Python]: http://python.org/
[Flask]: http://flask.pocoo.org/
