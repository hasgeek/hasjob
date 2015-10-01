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

Hasjob can be used with Docker (recommended) or the harder way with a manual setup.

## With Docker

#### Install and run with Docker

* Install [Docker](https://docs.docker.com/installation/) and [Compose](https://docs.docker.com/compose/install/)

* Next, rename the `instance/development.docker.py` to `instance/development.py`

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

* Start the server
    
    ```
    $ docker-compose up
    ```

* You can edit the server name and Lastuser settings in `docker-compose.yml`

## Without Docker

Hasjob without Docker requires manual installation of all dependencies.

### Postgres

Hasjob requires Postgres >= 9.4 and Redis. To set up a Postgres DB:

On OS X using the [Postgres App](http://postgresapp.com):

    $ # Add Postgres app to the path if it's not already in there
    $ export PATH="/Applications/Postgres.app/Contents/Versions/9.4/bin:$PATH"
    $ # Make the user and database
    $ createuser -d hasjob
    $ createdb -O hasjob -W hasjob

On any Linux distribution:

    $ sudo -u postgres createuser -d hasgeek
    $ sudo -u postgres createdb -O hasgeek hasjob

Edit `instance/development.py` to set the variable `SQLALCHEMY_DATABASE_URI` to `postgres://hasjob:YOUR_PASSWORD_HERE@localhost:5432/hasjob`.

Redis does not require special configuration, but must listen on localhost and port 6379 (default).

### Local URLs

Hasjob makes use of subdomains to serve different sub-boards for jobs. To set it up:

* Edit `/etc/hosts` and add these entries:

    ```
    127.0.0.1    hasjob.dev
    127.0.0.1    static.hasjob.dev
    127.0.0.1    subboard.hasjob.dev
    ```

* Edit `instance/development.py` and change `SERVER_NAME` to `'hasjob.dev:5000'`

### Installation

Hasjob runs on [Python](https://www.python.org) with the [Flask](http://flask.pocoo.org/) microframework. You can choose to set up your development environment in the following two ways…

#### Virutalenv + pip/easy_install

If you are going to use a computer on which you would work on multiple Python based projects, [Virtualenv](docs.python-guide.org/en/latest/dev/virtualenvs/) is strongly recommended to ensure Hasjob's elaborate and sometimes version-specific requirements doesn't clash with anything else.

You will need to install all the requirements listed in `requirements.txt` using `easy_install` or `pip`:

    $ pip install -r requirements.txt

If you get an error, try running:

    $ easy_install -U setuptools

Finish configuration with:

    $ python manage.py db create
    $ python manage.py configure

Before you run the server in development mode, make sure you have Postgres server and Redis server running as well. To start Hasjob:

    $ python runserver.py

## Other notes

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

### License

HasJob uses GNU AFFERO GPL license. Please see `license.txt` file in this
repository.
