import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from aws_spy.core.encoders import JSONEncoder


def test_json_encoder() -> None:
    uid = UUID("a2618752-dc19-4f40-adf5-6173d419f2ed")
    obj = {
        "decimal": Decimal(0.55),
        "datetime": datetime(2023, 5, 10),
        "date": date(2022, 5, 10),
        "uuid": uid,
        "default": 1,
    }
    encoded = json.dumps(obj, cls=JSONEncoder)
    assert encoded == (
        '{"decimal": 0.55, "datetime": "2023-05-10T00:00:00", "date": "2022-05-10", '
        '"uuid": "a2618752-dc19-4f40-adf5-6173d419f2ed", "default": 1}'
    )
