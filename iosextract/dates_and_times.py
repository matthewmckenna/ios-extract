from datetime import datetime, timezone
import json


def _datetime_to_str(dt: datetime, json_encoder: json.JSONEncoder) -> str:
    return json.dumps(dt, cls=json_encoder).strip('"')


def _str_to_datetime(datetime_str: str) -> datetime:
    datetime_fmt = "%Y-%m-%d %H:%M:%S"
    return datetime.strptime(datetime_str, datetime_fmt).astimezone(tz=timezone.utc)


def _datetime_to_ddmmmyyyy(dt: datetime) -> str:
    """Return the datetime object as a string in the format DD-MMM-YYYY HH:MM:SS

    The timezone field of the datetime object is set to UTC.
    """
    return dt.astimezone(tz=timezone.utc).strftime("%d-%b-%Y %H:%M:%S")


def _isoformat_now(tz: timezone = timezone.utc):
    return datetime.now(tz=tz).isoformat()


def _get_ymd_hms_timestamp(tz: timezone = timezone.utc):
    return datetime.now(tz=tz).strftime("%Y%m%d_%H%M%S")
