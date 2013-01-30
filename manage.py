#!/usr/bin/env python

from flask.ext.script import Manager, Server, Option, prompt_bool
from flask.ext.script.commands import Clean, ShowUrls
from flask.ext.alembic import ManageMigrations

from hasjob import app, init_for
from hasjob import models
from hasjob.models import db


manager = Manager(app)
database = Manager(usage="Perform database operations")


class InitedServer(Server):
    def get_options(self):
        return super(InitedServer, self).get_options() + (
        Option('-e', dest='env', default='dev', help="run server for this environment [default 'dev']"),
        )

    def handle(self, *args, **kwargs):
        if 'env' in kwargs:
            init_for(kwargs.pop('env'))
        super(InitedServer, self).handle(*args, **kwargs)


class InitedMigrations(ManageMigrations):
    def run(self, args):
        if len(args) and not args[0].startswith('-'):
            init_for(args[0])
        super(InitedMigrations, self).run(args[1:])


@manager.shell
def _make_context():
    return dict(app=app, db=db, models=models, init_for=init_for)


@database.option('-e', '--env', default='dev', help="runtime environment [default 'dev']")
def drop(env):
    "Drops database tables"
    init_for(env)
    if prompt_bool("Are you sure you want to lose all your data?"):
        db.drop_all()


@database.option('-e', '--env', default='dev', help="runtime environment [default 'dev']")
def create(env):
    "Creates database tables from sqlalchemy models"
    init_for(env)
    db.create_all()


manager.add_command("db", database)
manager.add_command("runserver", InitedServer())
manager.add_command("clean", Clean())
manager.add_command("showurls", ShowUrls())
manager.add_command("migrate", InitedMigrations())


if __name__ == "__main__":
    manager.run()
