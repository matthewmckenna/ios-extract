from __future__ import annotations
from datetime import datetime
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from dates_and_times import _datetime_to_str, _str_to_datetime

FIELD_MAPPING = {
    "backup_directory": "Backup Directory",
    "build_version": "Build Version",
    "device_name": "Device Name",
    "display_name": "Display Name",
    "guid": "GUID",
    "iccid": "ICCID",
    "imei": "IMEI",
    "imei_2": "IMEI 2",
    "last_backup_date": "Last Backup Date",
    "meid": "MEID",
    "phone_number": "Phone Number",
    "product_name": "Product Name",
    "product_type": "Product Type",
    "product_version": "Product Version",
    "serial_number": "Serial Number",
    "target_identifier": "Target Identifier",
    "unique_identifier": "Unique Identifier",
}


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


@dataclass
class BackupInfo:
    backup_directory: str | Path
    build_version: str
    device_name: str
    display_name: str
    guid: str
    iccid: str
    imei: str
    imei_2: str
    last_backup_date: str | datetime
    meid: str | None
    phone_number: str
    product_name: str
    product_type: str
    product_version: str
    serial_number: str
    target_identifier: str
    unique_identifier: str

    def __post_init__(self):
        if isinstance(self.last_backup_date, str):
            self.last_backup_date = _str_to_datetime(self.last_backup_date)
        if isinstance(self.backup_directory, str):
            self.backup_directory = Path(self.backup_directory)

    def extract_info_mapping(self, data):
        print(data)
        return {FIELD_MAPPING.get(k): v for k, v in data}

    def to_dict(self):
        return {
            **asdict(self, dict_factory=self.extract_info_mapping),
            "Last Backup Date": _datetime_to_str(
                self.last_backup_date, json_encoder=CustomJSONEncoder
            ),
            "Backup Directory": str(self.backup_directory),
        }

    @classmethod
    def from_dict(cls, d):
        inverse_mapping = {v: k for k, v in FIELD_MAPPING.items()}
        return cls(**{inverse_mapping[k]: v for k, v in d.items()})

    @property
    def major_ios_version(self) -> int:
        return int(self.product_version.split(".")[0])
