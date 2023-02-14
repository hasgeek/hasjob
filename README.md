# Hasjob

Code for Hasjob, Hasgeek’s job board at https://hasjob.co/

Copyright © 2010-2021 by Hasgeek

Hasjob’s code is open source under the AGPL v3 license (see LICENSE.txt). We welcome your examination of our code to:

- Establish trust and transparency on how it works, and
- Allow contributions to Hasjob.

Our workflow assumes this code is for use on a single production website. Using this to operate your own job board is not recommended. The name ‘Hasjob’ and the distinctive appearance of the job board are not part of the open source code.

To establish our intent, we use the AGPL v3 license, which requires you to release all your modifications to the public under the same license. You may not make a proprietary fork. To have your contributions merged back into the master repository, you must agree to assign copyright to Hasgeek, and must assert that you have the right to make this assignment. (You may not like this condition, and we understand. If you have a better idea, tell us!)

## Installation

Installation is a multi-step process. If any of this is outdated, consult the `.travis.yml` file. That tends to be better maintained.

### Pick an environment

Hasjob requires a `FLASK_ENV` environment variable set to one of the following values, depending on whether the deployment is in development or production:

- `DEVELOPMENT` or `development` or `dev` (default)
- `PRODUCTION` or `production` or `prod`

In a production environment, you must set `FLASK_ENV` globally for it to be available across processes. On Ubuntu/Debian systems, add it to `/etc/environment` and reboot.

### PostgreSQL, Redis, NodeJS

Hasjob requires PostgreSQL, Redis and NodeJS. Installation

On macOS using Homebrew:

    $ brew install postgresql
    $ brew services start postgresql
    $ brew install redis
    $ brew services start redis
    $ brew install node

On Ubuntu:

- PostgreSQL:

  ```
  $ sudo apt install postgresql
  $ sudo systemctl enable postgresql@13-main
  ```

- Redis: `sudo apt install redis`
- NodeJS: Follow instructions at https://node.dev/node-binary

Next, create a PostgreSQL DB. On macOS:

    $ createdb hasjob

On any Linux distribution:

    $ sudo -u postgres createuser -d hasgeek
    $ sudo -u postgres createdb -O hasgeek hasjob

Edit `instance/development.py` to set the variable `SQLALCHEMY_DATABASE_URI` to one of these, depending on whether the database is hosted under the `hasgeek` user or your personal account, and whether your database is accessed over a Unix socket or IP:

1. `postgresql:///hasjob`
2. `postgresql://localhost/hasjob`
3. `postgresql://hasgeek:YOUR_PASSWORD_HERE@localhost:5432/hasjob`

Redis does not require special configuration, but must listen on localhost and port 6379 (default).

### Configuration

Hasjob requires several configuration variables. Copy `instance/settings-sample.py` into a new file named either `instance/development.py` or `instance/production.py` depending on runtime environment, and set all values.

Hasjob operates as a client app of [Funnel](https://github.com/hasgeek/funnel) (previously Lastuser before it merged into Funnel). You must either run Funnel yourself, in parallel with Hasjob, or register as a client on the production website at https://hasgeek.com/apps.

Hasjob makes use of subdomains to serve different sub-boards for jobs. To set it up for development:

- Edit `/etc/hosts` and add these entries:

  ```
  127.0.0.1    hasjob.test
  127.0.0.1    static.hasjob.test
  127.0.0.1    www.hasjob.test
  129.0.0.1    your-test-subboard.hasjob.test
  ```

- Edit `instance/development.py` and change `SERVER_NAME` to `'hasjob.test:5001'`

### Install dependencies

Hasjob runs on [Python](https://www.python.org) 3.7 or later with the [Flask](http://flask.pocoo.org/) microframework.

#### Virutalenv + pip + webpack

If you are going to use a computer on which you would work on multiple Python based projects, [Virtualenv](docs.python-guide.org/en/latest/dev/virtualenvs/) is strongly recommended to ensure Hasjob’s elaborate and sometimes version-specific requirements doesn't clash with anything else.

You will need to install all the requirements listed in `requirements.txt` using `pip`:

```
$ pip install -r requirements.txt
```

If you intend to actively contribute to Hasjob code, some functionality is sourced from the related libraries [coaster](https://github.com/hasgeek/coaster), [baseframe](https://github.com/hasgeek/baseframe) and [Flask-Lastuser](https://github.com/hasgeek/flask-lastuser). You may want to clone these repositories separately and put them in development mode:

```
$ cd ..
$ git clone https://github.com/hasgeek/coaster.git
$ git clone https://github.com/hasgeek/baseframe.git
$ git clone https://github.com/hasgeek/flask-lastuser.git
$ pip uninstall coaster baseframe flask-lastuser
$ for DIR in coaster baseframe flask-lastuser; do cd $DIR; python setup.py develop; cd ..; done
$ cd baseframe && make && cd ..
```

You will need to install all dependencies, run Webpack to bundle CSS, JS files & generate the service-worker.js

```
$ cd <hasjob project root>
$ make
```

Before you run the server in development mode, make sure you have Postgres server and Redis server running as well. To start Hasjob:

```
$ ./runserver.sh
```

### Create root board

Some functionality in Hasjob requires the presence of a sub-board named `www`. Create it by visiting `http://hasjob.test:5001/board` (or the `/board` page on whatever hostname and port you used for your installation). The `www` board is a special-case to refer to the root website.

### Periodic jobs

Hasjob requires some tasks to be run in periodic background jobs. These can be called from cron. Use `crontab -e` as the user account running Hasjob and add:

```cron
*/10 * * * * cd /path/to/hasjob; flask periodic sessions
*/5  * * * * cd /path/to/hasjob; flask periodic impressions
0    2 * * * cd /path/to/hasjob; flask periodic campaignviews
```

### Other notes

If you encounter a problem setting up, please look at existing issue reports on GitHub before filing a new issue. This code is the same version used in production, so if the website works, chances are something is wrong in your installation.

WSGI is recommended for production. For Apache, enable `mod_wsgi` and make a `VirtualHost` with:

```apache
WSGIScriptAlias / /path/to/hasjob/git/repo/folder/wsgi.py
```

For Nginx, run `wsgi.py` under uWSGI and proxy to it:

```nginx
location / {
    include uwsgi_params; # Include common uWSGI settings here
    uwsgi_pass 127.0.0.1:8093;  # Use the port number uWSGI is running on
    uwsgi_param UWSGI_CHDIR /path/to/hasjob/git/repo/folder;
    uwsgi_param UWSGI_MODULE wsgi;
}
```

Sample uWSGI configuration:

```uwsgi
[uwsgi]
socket = 127.0.0.1:8093
processes = 8
threads = 2
enable-threads = True
master = true
uid = <user-account-on-your-server>
gid = <group-for-user-account>
chdir = /path/to/hasjob/git/repo/folder
virtualenv = /path/to/virtualenv
plugins-dir = /usr/lib/uwsgi/plugins
plugins = python37
pp = ..
wsgi-file = wsgi.py
callable = application
touch-reload = /path/to/file/to/touch/to/cause/reload
pidfile = /var/run/uwsgi/%n.pid
daemonize = /var/log/uwsgi/app/%n.log
```
