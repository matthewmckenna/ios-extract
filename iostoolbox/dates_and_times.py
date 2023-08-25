import json
from datetime import datetime, timezone

DDMMMYYYY_HHMMSS_Z_FORMAT = "%d-%b-%Y %H:%M:%S %Z"  # 01-Jan-2020 00:00:00 UTC
YYYYMMDD_FORMAT = "%Y-%m-%d"  # 2020-01-01
YYYYMMDD_HHMMSS_FORMAT = "%Y-%m-%d %H:%M:%S"  # 2020-01-01 00:00:00
YYYYMMDD_HHMMSS_FORMAT_2 = "%Y%m%d_%H%M%S"  # 20200101_000000


def datetime_to_ymdhms(dt: datetime) -> str:
    """Return the datetime object as a string in the format YYYY-MM-DD HH:MM:SS"""
    return dt.strftime(YYYYMMDD_HHMMSS_FORMAT)


def datetime_to_ymdhms_2(dt: datetime, json_encoder: json.JSONEncoder) -> str:
    """Return the datetime object as a string in the format YYYY-MM-DD HH:MM:SS"""
    return json.dumps(dt, cls=json_encoder).strip('"')


def ymdhms_to_datetime(datetime_str: str) -> datetime:
    """Return the datetime string in the format YYYY-MM-DD HH:MM:SS as a datetime object"""
    return datetime.strptime(datetime_str, YYYYMMDD_HHMMSS_FORMAT).astimezone(tz=timezone.utc)


def datetime_to_ddmmmyyyy(dt: datetime) -> str:
    """Return the datetime object as a string in the format DD-MMM-YYYY HH:MM:SS

    The timezone field of the datetime object is set to UTC.
    """
    return dt.replace(tzinfo=timezone.utc).strftime(DDMMMYYYY_HHMMSS_Z_FORMAT)


def isoformat_now(tz: timezone = timezone.utc) -> str:
    """Return the current datetime as a string formatted as ISO 8601.

    >>> isoformat_now()
    '2023-05-27T21:51:34.965891+00:00'
    """
    return datetime.now(tz=tz).isoformat()


def ymdhms_now() -> str:
    """Return the current date and time as a string formatted as YYYYMMDD_HHMMSS"""
    return datetime.now(tz=timezone.utc).strftime(YYYYMMDD_HHMMSS_FORMAT_2)


def today2ymd() -> str:
    """Return the current date as a string formatted as YYYY-MM-DD"""
    return datetime.now(tz=timezone.utc).strftime(YYYYMMDD_FORMAT)
