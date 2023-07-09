import datetime
import json
from decimal import Decimal
from typing import Any
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime | datetime.date):
            return o.isoformat()
        elif isinstance(o, UUID):
            return str(o)
        elif isinstance(o, Decimal):
            return float(o)
        return super().default(o)  # pragma: no cover
