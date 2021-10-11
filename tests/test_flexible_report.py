from datetime import datetime, timezone
import unittest

import msgpack
import requests_mock

from archfx_cloud.api.connection import Api
from archfx_cloud.reports.flexible_dictionary import ArchFXFlexibleDictionaryReport
from archfx_cloud.reports.report import ArchFXDataPoint


class FlexibleReportTests(unittest.TestCase):
    def test_decoding_flexible_report(self):
        """Make sure we can decode a msgpack encoded report."""

        data = {
            "format": "v200",
            "device": 10,
            "streamer_index": 100,
            "streamer_selector": 65536,
            "sent_timestamp": 1,
            "seqid": 1,
            "lowest_id": 2,
            "highest_id": 3,
            "events": [
                {
                    "stream": "5020",
                    "timestamp": "2020-01-20T00:00:00.100000Z",
                    "dev_seqid": 2,
                    "value": 0,
                    "extra_data": {
                        "axis": "z",
                        "peak": 45.41939932879673,
                        "duration": 15,
                        "delta_v_x": 0.0,
                        "delta_v_y": 0.0,
                        "delta_v_z": 0.0
                    }
                },
                {
                    "stream": "5020",
                    "timestamp": "2020-01-20T01:12:00Z",
                    "dev_seqid": 3,
                    "value": 0,
                    "extra_data": {
                        "axis": "z",
                        "peak": 58.13753330123034,
                        "duration": 15,
                        "delta_v_x": 0.0,
                        "delta_v_y": 0.0,
                        "delta_v_z": 0.0
                    }
                }
            ]
        }

        encoded = msgpack.packb(data, use_bin_type=True)
        decoded = msgpack.unpackb(encoded, raw=False)
        report = ArchFXFlexibleDictionaryReport(encoded, False, False)

        assert len(report.visible_data) == 2

        ev1 = report.visible_data[0]
        ev2 = report.visible_data[1]

        assert isinstance(ev1.timestamp, datetime)
        assert isinstance(ev2.timestamp, datetime)

        assert ev1.summary_data == {
            "axis": "z",
            "peak": 45.41939932879673,
            "duration": 15,
            "delta_v_x": 0.0,
            "delta_v_y": 0.0,
            "delta_v_z": 0.0
        }

        assert ev2.summary_data == {
            "axis": "z",
            "peak": 58.13753330123034,
            "duration": 15,
            "delta_v_x": 0.0,
            "delta_v_y": 0.0,
            "delta_v_z": 0.0
        }

    def test_report_usage(self):
        """Test how users should use this report"""
        events = []

        reading = ArchFXDataPoint(
            timestamp=datetime(2021, 1, 20, 0, 0, 0, 100000, timezone.utc),
            stream='0001-5030',
            value=2.0,
            summary_data={'foo': 5, 'bar': 'foobar'},
            raw_data=None,
            reading_id=1000
        )
        events.append(reading)
        reading = ArchFXDataPoint(
            timestamp=datetime(2021, 1, 20, 0, 0, 0, 200000, timezone.utc),
            stream=0x15030,
            value=3.0,
            summary_data={'foo': 6, 'bar': 'foobar'},
            reading_id=1001
        )
        events.append(reading)
        reading = ArchFXDataPoint(
            timestamp=datetime(2021, 1, 20, 0, 0, 0, 200000, timezone.utc),
            stream='5051',
            value=1.0,
            reading_id=1002
        )
        events.append(reading)

        sent_time = datetime(2021, 1, 20, 0, 0, 0, 300000, timezone.utc)
        report = ArchFXFlexibleDictionaryReport.FromReadings(
            device='d--1234',
            data=events,
            report_id=1003,
            streamer=0xff,
            sent_timestamp=sent_time
        )
        decoded = msgpack.unpackb(report.encode(), raw=False)
        assert decoded.get('format') == 'v200'
        assert decoded.get('device') == 0x1234
        assert decoded.get('streamer_index') == 0xff
        assert decoded.get('streamer_selector') == 0xffff
        assert decoded.get('seqid') == 1003
        assert decoded.get('lowest_id') == 1000
        assert decoded.get('highest_id') == 1002
        assert decoded.get('sent_timestamp') == '2021-01-20T00:00:00.300000+00:00'
        report_data = decoded.get('events')
        assert len(report_data) == 3
        assert report_data[0].get('timestamp') == '2021-01-20T00:00:00.100000+00:00'
        assert report_data[1].get('timestamp') == '2021-01-20T00:00:00.200000+00:00'
        assert report_data[2].get('timestamp') == '2021-01-20T00:00:00.200000+00:00'
        assert report_data[0].get('stream') == 0x15030
        assert report_data[1].get('stream') == 0x15030
        assert report_data[2].get('stream') == 0x5051
        assert report_data[0].get('dev_seqid') == 1000
        assert report_data[1].get('dev_seqid') == 1001
        assert report_data[2].get('dev_seqid') == 1002
        assert report_data[0].get('value') == 2.0
        assert report_data[1].get('value') == 3.0
        assert report_data[2].get('value') == 1.0
        assert report_data[0].get('data') is None
        assert report_data[1].get('data') is None
        assert report_data[2].get('data') is None
        assert report_data[0].get('extra_data') == {'foo': 5, 'bar': 'foobar'}
        assert report_data[1].get('extra_data') == {'foo': 6, 'bar': 'foobar'}
        assert report_data[2].get('extra_data') == {}

    @requests_mock.Mocker()
    def test_upload(self, m):
        """Testing that we can upload a FlexibleDictionaryReport."""
        report = ArchFXFlexibleDictionaryReport.FromReadings(
            device='d--1234',
            data=[
                ArchFXDataPoint(
                    timestamp=datetime(2021, 1, 20, tzinfo=timezone.utc),
                    stream='0001-5030',
                    value=2.0,
                    summary_data={'foo': 5, 'bar': 'foobar'},
                    raw_data=None,
                    reading_id=1000
                ),
            ],
            report_id=1003,
            streamer=0xff,
            sent_timestamp=datetime(2021, 1, 20, tzinfo=timezone.utc),
        )
        sent_time_str = report.sent_timestamp.replace(":", "%3A").replace("+", "%2B")
        m.post(
            f"http://archfx.test/api/v1/streamer/report/?timestamp={sent_time_str}",
            json={"count": 1},
        )


        api = Api(domain='http://archfx.test')
        resp = report.upload(api)
        self.assertEqual(resp, 1)

        request = m.request_history[0]._request
        self.assertIn('multipart/form-data; boundary=', request.headers["Content-Type"])
        self.assertIn(b'Content-Disposition: form-data; name="file"; filename=', request.body)
        self.assertIn(b'filename="report.mp"', request.body)  # Check filename correctness
