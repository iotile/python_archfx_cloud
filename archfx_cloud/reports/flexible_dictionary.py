"""A flexible dictionary based report format suitable for msgpack and json serialization."""

import datetime
from io import BytesIO
from typing import List, Union
import msgpack
from ..utils.slugs import ArchFxDeviceSlug
from .exceptions import DataError
from .report import ArchFXDataPoint, ArchFXReport


class ArchFXFlexibleDictionaryReport(ArchFXReport):
    """A list of events and readings encoded as a dictionary.
    This report format is designed to be suitable for storing in any
    format that supports key/value objects like json, msgpack, yaml,
    etc.
    Args:
        rawreport: The raw data of this report
        signed: Whether this report is signed to specify who it is from
        encrypted: Whether this report is encrypted
        received_time: The time in UTC when this report was received from a device.
            If not received, the time is assumed to be utcnow().
    """

    FORMAT_TAG = "v200"

    @classmethod
    def FromReadings(cls,
                     device: Union[str, int],
                     data: List[ArchFXDataPoint],
                     report_id: int = ArchFXDataPoint.InvalidReadingID,
                     selector: int = 0xFFFF,
                     streamer: int = 0x100,
                     sent_timestamp: datetime.datetime = None,
                     received_time: datetime.datetime = None):
        """Create a flexible dictionary report from a list of readings and events.
        Args:
            device: The uuid or slug of the device that this report came from
            events: A list of the events contained in the report.
            report_id: The id of the report.  If not provided it defaults to IOTileReading.InvalidReadingID.
                Note that you can specify anything you want for the report id but for actual IOTile devices
                the report id will always be greater than the id of all of the readings contained in the report
                since devices generate ids sequentially.
            selector: The streamer selector of this report.  This can be anything but if the report came from
                a device, it would correspond with the query the device used to pick readings to go into the report.
            streamer: The streamer id that this reading was sent from.
            sent_timestamp: The device's uptime that sent this report.
            received_time: The UTC time when this report was received from an IOTile device.  If it is being
                created now, received_time defaults to datetime.utcnow().
        Returns:
            ArchFXFlexibleDictionaryReport: A report containing the data passed in.
        """

        lowest_id = ArchFXDataPoint.InvalidReadingID
        highest_id = ArchFXDataPoint.InvalidReadingID

        for item in iter(data):
            if item.reading_id == ArchFXDataPoint.InvalidReadingID:
                continue

            if lowest_id == ArchFXDataPoint.InvalidReadingID or item.reading_id < lowest_id:
                lowest_id = item.reading_id
            if highest_id == ArchFXDataPoint.InvalidReadingID or item.reading_id > highest_id:
                highest_id = item.reading_id

        data_list = [x.asdict() for x in data]

        report_dict = {
            "format": cls.FORMAT_TAG,
            "device": ArchFxDeviceSlug(device).get_id(),
            "streamer_index": streamer,
            "streamer_selector": selector,
            "seqid": report_id,
            "lowest_id": lowest_id,
            "highest_id": highest_id,
            "sent_timestamp": sent_timestamp,
            "events": data_list  # Still using 'event' for backwards compatibility with old reports
        }

        encoded = msgpack.packb(report_dict, default=_encode_datetime, use_bin_type=True)
        return ArchFXFlexibleDictionaryReport(encoded, signed=False, encrypted=False, received_time=received_time)

    def decode(self):
        """Decode this report from a msgpack encoded binary blob."""

        report_dict = msgpack.unpackb(self.raw_report, raw=False)

        data = [ArchFXDataPoint.FromDict(x) for x in report_dict.get('events', [])]

        if 'device' not in report_dict:
            raise DataError("Invalid encoded ArchFXFlexibleDictionaryReport that did not "
                            "have a device key set with the device uuid")

        self.origin = report_dict['device']
        self.report_id = report_dict.get("seqid", ArchFXDataPoint.InvalidReadingID)
        self.sent_timestamp = report_dict.get("sent_timestamp", None)
        self.origin_streamer = report_dict.get("streamer_index")
        self.streamer_selector = report_dict.get("streamer_selector")
        self.lowest_id = report_dict.get('lowest_id')
        self.highest_id = report_dict.get('highest_id')

        return data

    def asdict(self):
        """ Return this report as a dictionary """
        return msgpack.unpackb(self.raw_report)

    def serialize(self):
        """Serialize this report including the received time."""

        raise NotImplementedError("This report format (ArchFXFlexibleDictionaryReport) does not support serialization")

    def write(self, file_path: str):
        """Write Streamer Report to disk as a msgpack file"""
        with open(file_path, "wb") as outfile:
            outfile.write(self.encode())

    def upload(self, cloud):
        """Uploads this report into ArchFX cloud

        Args:
            cloud: an instance of archfx_cloud.api.connection.Api. Must be authenticated.

        Returns:
            int: The number of new readings that were accepted by the cloud as novel.
        """
        return cloud("streamer/report").upload_fp(
            ("report.mp", BytesIO(self.encode())),
            timestamp=self.sent_timestamp,
        )['count']


def _encode_datetime(obj):
    """Pack a datetime into an isoformat string."""
    if isinstance(obj, datetime.datetime):
        if obj.tzinfo:
            obj = obj.astimezone(datetime.timezone.utc)
        dt_str = obj.isoformat()
        if dt_str[-6] in ['-', '+']:
            return dt_str
        else:
            return dt_str + '+00:00'

    return obj
