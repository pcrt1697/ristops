from sqlalchemy.orm import DeclarativeBase as _DeclarativeBase

SCHEMA_NAME = "ristops_venue"


def make_table_args(*args):
    return args + ({"schema": SCHEMA_NAME},)


class Base(_DeclarativeBase):
    __table_args__ = make_table_args()
