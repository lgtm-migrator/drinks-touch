# coding=utf-8

from database.storage import get_session
from sqlalchemy.sql import text


def get_by_ean(ean):
    session = get_session()
    sql = text("""
        SELECT *
        FROM drink
        WHERE ean = :ean
    """)
    row = session.connection().execute(sql, ean=ean).fetchone()
    drink = dict(zip(row.keys(), row))
    if not drink:
        drink = {
            'name': 'Unbekannt ('+ean+')',
            'size': 0,
            'tags': ['unkown']
        }

    return drink