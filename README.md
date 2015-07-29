Hasjob
======

Code for Hasjob, HasGeek's job board at https://hasjob.co/

Copyright © 2010-2015 by HasGeek Media LLP

Hasjob's code is open source under the AGPL v3 license (see LICENSE.txt),
but the name 'Hasjob' and the distinctive appearance of the job board are
not part of the open source code. The code is open to:

* Establish trust and transparency on how it works, and
* Allow contributions to Hasjob.

HasGeek is a business, and like any business has trade secrets, intellectual
property and competition. Hasjob's code is not intended to be used to setup
rival job boards.

If you really must use this code to run your own job board, the AGPLv3 license
requires you to release all your modifications to the public under the same
license. You may not make a proprietary fork.

To have your contributions merged back into the master repository, you must
agree to assign copyright to HasGeek Media LLP and must assert that you have
the right to make this assignment.

-----

Hasjob runs on [Python][] with the [Flask][] microframework. You will need
to install all the requirements listed in `requirements.txt` using
`easy_install` or `pip`:

    $ pip install -r requirements.txt

If you get an error, try running:

    $ easy_install -U setuptools

Next, Copy `settings-sample.py` to `settings.py`, edit as
necessary, and finish configuration with:

    $ python manage.py db create
    $ python manage.py configure

To run the server in development mode:

    $ python runserver.py

### Install and run with Docker

You can alternatively run Hasjob with Docker.

* Install [Docker](https://docs.docker.com/installation/) and [Compose](https://docs.docker.com/compose/install/)
Next, rename the `instance/development.docker.py` to `development.py`

* Build the images

    ```
    $ docker-compose build
    ```

* Initialize the database
    ```
    $ docker-compose run web sh
        web$ python manage.py db create
        web$ exit
    ```
* Start hasjob
    
    ```
    $ docker-compose up
    ```

If you encounter a problem setting up, please look at existing issue reports
on GitHub before filing a new issue. This code is the same version used in
production so there is a very good chance you did something wrong and there
is no actual problem in the code. Issues you encounter after setup could
be real bugs.

WSGI is recommended for production. For Apache: enable `mod_wsgi` and make a
`VirtualHost` with:

    WSGIScriptAlias / /path/to/website.wsgi

For Nginx, run website.py under uWSGI and proxy to it:

    location / {
        include uwsgi_params; # Include common uWSGI settings here
        uwsgi_pass 127.0.0.1:8093;  # Use the port number uWSGI is running on
        uwsgi_param UWSGI_CHDIR /path/to/hasjob/git/repo/folder;
        uwsgi_param UWSGI_MODULE website;
    }


[Python]: http://python.org/
[Flask]: http://flask.pocoo.org/
