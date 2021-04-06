"""Base class for data streamed from an IOTile device"""

import datetime
from typing import Union, Dict, Optional
import dateutil.parser
from typedargs.exceptions import NotFoundError
from ..utils.slugs import ArchFxVariableID
from .exceptions import DataError


class ArchFXDataPoint:
    """Base class for all ArchFX Data records.
    An event is a dictionary with a small summary section and an arbitrarily
    large data section.  ArchFXDataPoint always have one value and zero or more
    key/value stored as extra data.
    There are two different key/value stores in an ArchFXDataPoint because there
    may be a very large amount of raw data that is summarized into a smaller
    representation.  It may be useful to know that separation so that we can
    store the large data somewhere different from where we store the summary.
    Args:
        timestamp: A UTC time when this data was acquired.
        reading_id: An optional unique identifier for this reading that allows
            deduplication.  If no reading id is passed, InvalidReadingID is used.
        stream: The stream that this reading is part of
        value: The primary reading value
        summary_data: A dictionary of any summary data this event has.  You
            may pass None if there is no summary data.
        raw_data: A dictionary (possibly very large) of all data associated
            with this event.  You may pass None if all data is contained in the
            summary_data member.
    """

    InvalidRawTime = 0xFFFFFFFF
    InvalidReadingID = 0

    def __init__(self,
                 timestamp: datetime.datetime,
                 stream: Union[str, int],
                 value: float,
                 summary_data: Optional[Dict] = None,
                 raw_data: Optional[Dict] = None,
                 reading_id: int = None):

        # Always store stream as variable ID
        self.stream = ArchFxVariableID(stream).get_id()

        if reading_id is None:
            reading_id = ArchFXDataPoint.InvalidReadingID

        self.reading_id = reading_id

        self.timestamp = timestamp

        self.value = float(value)
        if summary_data is None:
            summary_data = {}
        elif 'value' in summary_data:
            # We used to add 'value' as part of summary_data so checking we don't
            raise DataError('value is not a valid field for summary_data')
        self.summary_data = summary_data
        self.raw_data = raw_data

    def asdict(self):
        """Encode the data in this event into a dictionary.
        The dictionary returned from this method is a reference to the data
        stored in the ArchFXDataPoint, not a copy.  It should be treated as read
        only.
        Returns:
            dict: A dictionary containing the information from this event.
        """

        return {
            'stream': self.stream,
            'dev_seqid': self.reading_id,
            'timestamp': self.timestamp,
            'value': self.value,
            'extra_data': self.summary_data,
            'data': self.raw_data
        }

    @classmethod
    def FromDict(cls, obj):
        """Create an ArchFXDataPoint from the result of a previous call to asdict().
        Args:
            obj (dict): A dictionary produced by a call to ArchFXDataPoint.asdict()
        Returns:
            ArchFXDataPoint: The converted ArchFXDataPoint object.
        """

        timestamp = dateutil.parser.parse(obj['timestamp'])

        return ArchFXDataPoint(
            timestamp,
            obj.get('stream'),
            obj.get('value'),
            obj.get('extra_data'),
            obj.get('data'),
            reading_id=obj.get('dev_seqid')
        )

    def __str__(self):
        return "Stream {}: Data at {}, value {}".format(self.stream, self.timestamp, self.value)


class ArchFXReport:
    """Base class for data uploaded to ArchFX Cloud.
    All ArchFXReport must derive from this class and must implement the following interface
    - class method FromReadings(cls, uuid, readings)
        function that creates an instance of an ArchFXReport subclass from a list of readings
        and a device uuid.
    - property ReportType:
        The one byte type code that defines this report type
    - instance method verify(self):
        function that verifies that a report is correctly received and, if possible, that
        the sender is who it says it is.
    - instance method decode(self):
        function that decodes a report into a series of ArchFXDataPoint objects. The function
        should return a list of readings.
    - instance method serialize(self):
        function that should turn the report into a serialized bytearray that could be
        decoded with decode().
    Args:
        rawreport: The raw data of this report
        signed: Whether this report is signed to specify who it is from
        encrypted: Whether this report is encrypted
        received_time: The time in UTC when this report was received from a device.
            If not received, the time is assumed to be utcnow().
    """

    def __init__(self,
                 rawreport: bytearray,
                 signed: bool,
                 encrypted: bool,
                 received_time: datetime.datetime = None):
        self.visible_data = []

        self.origin = None

        if received_time is None:
            self.received_time = datetime.datetime.utcnow()
        else:
            self.received_time = received_time

        self.raw_report = rawreport
        self.signed = signed
        self.encrypted = encrypted
        self.verified = False

        # We may not have any visible readings if our report is encrypted
        # and we do not have access to the decryption key.
        self.visible_data = self.decode()

    def decode(self):
        """Decode a raw report into a series of readings
        """

        raise NotFoundError("ArchFXReport decode needs to be overriden")

    def encode(self):
        """Encode this report into a binary blob that could be decoded by a report format's decode method."""

        return self.raw_report

    def save(self, path: str):
        """Save a binary copy of this report
        Args:
            path: The path where we should save the binary copy of the report
        """

        data = self.encode()

        with open(path, "wb") as out:
            out.write(data)

    def serialize(self):
        """Turn this report into a dictionary that encodes all information including received timestamp"""

        info = {}
        info['received_time'] = self.received_time
        info['encoded_report'] = bytes(self.encode())

        # Handle python 2 / python 3 differences
        report_format = info['encoded_report'][0]
        if not isinstance(report_format, int):
            report_format = ord(report_format)
        info['report_format'] = report_format  # Report format is the first byte of the encoded report
        info['origin'] = self.origin

        return info

    def write(self, file_path: str):
        """Write Streamer Report to disk"""
        raise NotFoundError("ArchFXReport decode needs to be overriden")

    def __str__(self):
        if self.verified:
            verified = "verified"
        else:
            verified = "not verified"

        if self.encrypted:
            enc = "encrypted"
        else:
            enc = "not encrypted"
        return "ArchFX Report (length: {}, visible data: {}, {} and {})".format(
            len(self.raw_report), len(self.visible_data), verified, enc)
