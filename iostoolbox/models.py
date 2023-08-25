import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .dates_and_times import datetime_to_ymdhms, ymdhms_to_datetime

DIRECTORY_FIELDS = ["backup_directory", "output_directory"]
FIELDS = {
    "Backup Directory",
    "Build Version",
    "Device Name",
    "Display Name",
    "GUID",
    "ICCID",
    "IMEI",
    "IMEI 2",
    "Last Backup Date",
    "MEID",
    "Output Directory",
    "Phone Number",
    "Product Name",
    "Product Type",
    "Product Version",
    "Serial Number",
    "Target Identifier",
    "Unique Identifier",
}
FIELD_MAPPING = {f.lower().replace(" ", "_"): f for f in FIELDS}


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return datetime_to_ymdhms(obj)
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


@dataclass
class BackupInfo:
    _INFO_TXT_FILENAME = "info.txt"

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
    output_directory: str | Path
    phone_number: str
    product_name: str
    product_type: str
    product_version: str
    serial_number: str
    target_identifier: str
    unique_identifier: str

    def __post_init__(self):
        if isinstance(self.last_backup_date, str):
            self.last_backup_date = ymdhms_to_datetime(self.last_backup_date)
        if isinstance(self.backup_directory, str):
            self.backup_directory = Path(self.backup_directory)

    def extract_info_mapping(self, data):
        return {FIELD_MAPPING.get(k): v for k, v in data}

    def to_dict(self):
        return {
            **asdict(self, dict_factory=self.extract_info_mapping),
            "Last Backup Date": datetime_to_ymdhms(self.last_backup_date),
            "Backup Directory": str(self.backup_directory),
            "Output Directory": str(self.output_directory),
        }

    @classmethod
    def from_dict(cls, d):
        inverse_mapping = {v: k for k, v in FIELD_MAPPING.items()}
        return cls(
            **{inverse_mapping[k] if k not in DIRECTORY_FIELDS else k: v for k, v in d.items()}
        )

    @property
    def major_ios_version(self) -> int:
        """Return the major iOS version as an integer"""
        return int(self.product_version.split(".")[0])

    def write_info_txt(self):
        """Write an `info.txt` file to the output directory containing information about the backup"""
        info_txt_filepath = self.output_directory / self._INFO_TXT_FILENAME
        info_txt_filepath.write_text(
            "\n".join(f"{k}: {v}" for k, v in self.to_dict().items()) + "\n"
        )
