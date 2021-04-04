"""A flexible dictionary based report format suitable for msgpack and json serialization."""

import itertools
import msgpack
import datetime
from .exceptions import DataError
from .report import ArchFXDataPoint, ArchFXReport


class FlexibleDictionaryReport(ArchFXReport):
    """A list of events and readings encoded as a dictionary.
    This report format is designed to be suitable for storing in any
    format that supports key/value objects like json, msgpack, yaml,
    etc.
    Args:
        rawreport (bytearray): The raw data of this report
        signed (bool): Whether this report is signed to specify who it is from
        encrypted (bool): Whether this report is encrypted
        received_time (datetime): The time in UTC when this report was received from a device.
            If not received, the time is assumed to be utcnow().
    """

    FORMAT_TAG = "v200"

    @classmethod
    def FromReadings(cls, uuid, events, report_id=ArchFXDataPoint.InvalidReadingID,
                     selector=0xFFFF, streamer=0x100, sent_timestamp=None, received_time=None):
        """Create a flexible dictionary report from a list of readings and events.
        Args:
            uuid (int): The uuid of the device that this report came from
            readings (list of IOTileReading): A list of IOTileReading objects containing the data in the report
            events (list of IOTileEvent): A list of the events contained in the report.
            report_id (int): The id of the report.  If not provided it defaults to IOTileReading.InvalidReadingID.
                Note that you can specify anything you want for the report id but for actual IOTile devices
                the report id will always be greater than the id of all of the readings contained in the report
                since devices generate ids sequentially.
            selector (int): The streamer selector of this report.  This can be anything but if the report came from
                a device, it would correspond with the query the device used to pick readings to go into the report.
            streamer (int): The streamer id that this reading was sent from.
            sent_timestamp (int): The device's uptime that sent this report.
            received_time(datetime): The UTC time when this report was received from an IOTile device.  If it is being
                created now, received_time defaults to datetime.utcnow().
        Returns:
            FlexibleDictionaryReport: A report containing the readings and events passed in.
        """

        lowest_id = ArchFXDataPoint.InvalidReadingID
        highest_id = ArchFXDataPoint.InvalidReadingID

        for item in iter(events):
            if item.reading_id == ArchFXDataPoint.InvalidReadingID:
                continue

            if lowest_id == ArchFXDataPoint.InvalidReadingID or item.reading_id < lowest_id:
                lowest_id = item.reading_id
            if highest_id == ArchFXDataPoint.InvalidReadingID or item.reading_id > highest_id:
                highest_id = item.reading_id

        event_list = [x.asdict() for x in events]

        report_dict = {
            "format": cls.FORMAT_TAG,
            "device": uuid,
            "streamer_index": streamer,
            "streamer_selector": selector,
            "seqid": report_id,
            "lowest_id": lowest_id,
            "highest_id": highest_id,
            "device_sent_timestamp": sent_timestamp,
            "events": event_list
        }

        encoded = msgpack.packb(report_dict, default=_encode_datetime, use_bin_type=True)
        return FlexibleDictionaryReport(encoded, signed=False, encrypted=False, received_time=received_time)

    def decode(self):
        """Decode this report from a msgpack encoded binary blob."""

        report_dict = msgpack.unpackb(self.raw_report, raw=False)

        events = [ArchFXDataPoint.FromDict(x) for x in report_dict.get('events', [])]

        if 'device' not in report_dict:
            raise DataError("Invalid encoded FlexibleDictionaryReport that did not "
                            "have a device key set with the device uuid")

        self.origin = report_dict['device']
        self.report_id = report_dict.get("seqid", ArchFXDataPoint.InvalidReadingID)
        self.sent_timestamp = report_dict.get("device_sent_timestamp", None)
        self.origin_streamer = report_dict.get("streamer_index")
        self.streamer_selector = report_dict.get("streamer_selector")
        self.lowest_id = report_dict.get('lowest_id')
        self.highest_id = report_dict.get('highest_id')

        return events

    def asdict(self):
        """ Return this report as a dictionary """
        return msgpack.unpackb(self.raw_report)

    def serialize(self):
        """Serialize this report including the received time."""

        raise NotImplementedError("This report format (FlexibleDictionaryReport) does not support serialization")


def _encode_datetime(obj):
    """Pack a datetime into an isoformat string."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat() + 'Z'

    return obj
