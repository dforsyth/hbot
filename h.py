import os

from peewee import Model, SqliteDatabase

database = SqliteDatabase(os.environ.get("H_DB_NAME", ":memory:"))

class HModel(Model):
    class Meta:
        database = database

class UsageException(Exception):
    pass
