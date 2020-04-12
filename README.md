# Hasjob

Code for Hasjob, HasGeek’s job board at https://hasjob.co/

Copyright © 2010-2018 by HasGeek

Hasjob’s code is open source under the AGPL v3 license (see LICENSE.txt). We welcome your examination of our code to:

- Establish trust and transparency on how it works, and
- Allow contributions to Hasjob.

Our workflow assumes this code is for use on a single production website. Using this to operate your own job board is not recommended. The name ‘Hasjob’ and the distinctive appearance of the job board are not part of the open source code.

To establish our intent, we use the AGPL v3 license, which requires you to release all your modifications to the public under the same license. You may not make a proprietary fork. To have your contributions merged back into the master repository, you must agree to assign copyright to HasGeek, and must assert that you have the right to make this assignment.

## Installation

Hasjob can be used with Docker (recommended for quick start) or the harder way with a manual setup (recommended for getting involved). The Docker approach is unmaintained at this time. Let us know if something doesn't work.

### Pick an environment

Hasjob requires a `FLASK_ENV` environment variable set to one of the following values, depending on whether the deployment is in development or production:

- `DEVELOPMENT` or `development` or `dev` (default)
- `PRODUCTION` or `production` or `prod`

In a production environment, you must set `FLASK_ENV` globally for it to be available across processes. On Ubuntu/Debian systems, add it to `/etc/environment` and reboot.

### With Docker

#### Install and run with Docker

- Install [Docker](https://docs.docker.com/installation/) and [Compose](https://docs.docker.com/compose/install/)

- Next, rename the `instance/development.docker.py` to `instance/development.py`

- Build the images

  ```
  $ docker-compose build
  ```

- Initialize the database

  ```
  $ docker-compose run web sh
      web$ python manage.py db create
      web$ exit
  ```

- Start the server

  ```
  $ docker-compose up
  ```

- You can edit the server name and Lastuser settings in `docker-compose.yml`

### Without Docker

Hasjob without Docker requires manual installation of all dependencies.

#### Postgres and Redis

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

#### Local URLs

Hasjob makes use of subdomains to serve different sub-boards for jobs. To set it up:

- Edit `/etc/hosts` and add these entries (substituting `your-machine` with whatever you call your computer):

  ```
  127.0.0.1    hasjob.your-machine.local
  127.0.0.1    static.hasjob.your-machine.local
  127.0.0.1    subboard.hasjob.your-machine.local
  ```

- Edit `instance/development.py` and change `SERVER_NAME` to `'hasjob.your-machine.local:5000'`

#### Install dependencies

Hasjob runs on [Python](https://www.python.org) with the [Flask](http://flask.pocoo.org/) microframework.

##### Virutalenv + pip + webpack

If you are going to use a computer on which you would work on multiple Python based projects, [Virtualenv](docs.python-guide.org/en/latest/dev/virtualenvs/) is strongly recommended to ensure Hasjob’s elaborate and sometimes version-specific requirements doesn't clash with anything else.

You will need to install all the requirements listed in `requirements.txt` using `pip`:

    $ pip install -r requirements.txt

If you intend to actively contribute to Hasjob code, some functionality is sourced from the related libraries [coaster](https://github.com/hasgeek/coaster), [baseframe](https://github.com/hasgeek/baseframe) and [Flask-Lastuser](https://github.com/hasgeek/flask-lastuser). You may want to clone these repositories separately and put them in development mode:

    $ cd ..
    $ git clone https://github.com/hasgeek/coaster.git
    $ git clone https://github.com/hasgeek/baseframe.git
    $ git clone https://github.com/hasgeek/flask-lastuser.git
    $ pip uninstall coaster baseframe flask-lastuser
    $ for DIR in coaster baseframe flask-lastuser; do cd $DIR; python setup.py develop; cd ..; done
    $ cd baseframe && make && cd ..

Finish configuration with:

    $ python manage.py db create

You will need to install all dependencies listed in `package.json`

    $ cd hasjob/assets
    $ npm install

You will need to run Webpack to bundle CSS, JS files & generate the service-worker.js

    $ cd hasjob/assets
    $ yarn build

Before you run the server in development mode, make sure you have Postgres server and Redis server running as well. To start Hasjob:

    $ python runserver.py

### Create root board

Some functionality in Hasjob requires the presence of a sub-board named `www`. Create it by visiting `http://hasjob.your-machine.local:5000/board` (or the `/board` page on whatever hostname and port you used for your installation). The `www` board is a special-case to refer to the root website.

### Periodic jobs

Hasjob requires some tasks to be run in periodic background jobs. These can be called from cron. Use `crontab -e` as the user account running Hasjob and add:

    */10 * * * * cd /path/to/hasjob; python manage.py periodic sessions
    */5  * * * * cd /path/to/hasjob; python manage.py periodic impressions
    0    2 * * * cd /path/to/hasjob; python manage.py periodic campaignviews

### Testing

Tests are outdated at this time, but whatever tests exist are written in [CasperJS](http://casperjs.org/).

You need to [install CasperJS](http://docs.casperjs.org/en/latest/installation.html), which needs Python 2.6 (or greater) and [PhantomJS](http://phantomjs.org/) installed.

Edit the top few lines of test file `tests/test_job_post.js` with the URL, username and password.

Run the test with `casperjs test tests/test_job_post.js`.

### Disabling cache

To disable cache in development, add these lines to to `development.py`:

    CACHE_TYPE = 'null'
    CACHE_NO_NULL_WARNING = False

### Other notes

If you encounter a problem setting up, please look at existing issue reports on GitHub before filing a new issue. This code is the same version used in production, so if the website works, chances are something is wrong in your installation.

WSGI is recommended for production. For Apache, enable `mod_wsgi` and make a `VirtualHost` with:

    WSGIScriptAlias / /path/to/hasjob/git/repo/folder/website.py

For Nginx, run `website.py` under uWSGI and proxy to it:

    location / {
        include uwsgi_params; # Include common uWSGI settings here
        uwsgi_pass 127.0.0.1:8093;  # Use the port number uWSGI is running on
        uwsgi_param UWSGI_CHDIR /path/to/hasjob/git/repo/folder;
        uwsgi_param UWSGI_MODULE website;
    }
