from datetime import datetime, timezone

import pytest

from dates_and_times import _datetime_to_str, _str_to_datetime
from models import BackupInfo, CustomJSONEncoder


@pytest.fixture
def extract_info_dict():
    return {
        "Backup Directory": "backup-directory",
        "Build Version": "20D47",
        "Device Name": "device-name",
        "Display Name": "display-name",
        "GUID": "fake-guid",
        "ICCID": "fake-iccid",
        "IMEI": "fake-imei",
        "IMEI 2": "fake-imei-2",
        "Last Backup Date": "2022-03-11 01:47:03",
        "MEID": None,
        "Output Directory": "output-directory",
        "Phone Number": "+353 (01) 234 5678",
        "Product Name": "iPhone 14 Pro Max",
        "Product Type": "iPhone15,3",
        "Product Version": "16.3",
        "Serial Number": "fake_serial",
        "Target Identifier": "fake-target-identifier",
        "Unique Identifier": "fake-unique-identifier",
    }


@pytest.fixture
def extract_info():
    return BackupInfo(
        backup_directory="backup-directory",
        build_version="20D47",
        device_name="device-name",
        display_name="display-name",
        guid="fake-guid",
        iccid="fake-iccid",
        imei="fake-imei",
        imei_2="fake-imei-2",
        last_backup_date="2022-03-11 01:47:03",
        meid=None,
        output_directory="output-directory",
        phone_number="+353 (01) 234 5678",
        product_name="iPhone 14 Pro Max",
        product_type="iPhone15,3",
        product_version="16.3",
        serial_number="fake_serial",
        target_identifier="fake-target-identifier",
        unique_identifier="fake-unique-identifier",
    )


def test_extract_info_to_dict(extract_info, extract_info_dict):
    assert extract_info.to_dict() == extract_info_dict


def test_extract_info_from_dict(extract_info, extract_info_dict):
    assert BackupInfo.from_dict(extract_info_dict) == extract_info


def test_datetime_to_str():
    dt = datetime(2022, 3, 11, 1, 47, 3, tzinfo=timezone.utc)
    assert _datetime_to_str(dt, json_encoder=CustomJSONEncoder) == "2022-03-11 01:47:03"


def test_str_to_datetime():
    dt_str = "2022-03-11 01:47:03"
    assert _str_to_datetime(dt_str) == datetime(
        2022, 3, 11, 1, 47, 3, tzinfo=timezone.utc
    )
