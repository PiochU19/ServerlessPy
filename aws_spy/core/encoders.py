import datetime
import json
import typing as t
from decimal import Decimal
from uuid import UUID

T = t.TypeVar("T")


class JSONEncoder(json.JSONEncoder):
    def default(self, o: T) -> T | str | float:
        if isinstance(o, datetime.datetime | datetime.date):
            return o.isoformat()
        elif isinstance(o, UUID):
            return str(o)
        elif isinstance(o, Decimal):
            return float(o)
        return super().default(o)  # pragma: no cover
