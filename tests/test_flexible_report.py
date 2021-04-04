import unittest2 as unittest
import msgpack
from datetime import datetime
from archfx_cloud.reports.flexible_dictionary import FlexibleDictionaryReport


class FlexibleReportTests(unittest.TestCase):
    def test_decoding_flexible_report(self):
        """Make sure we can decode a msgpack encoded report."""

        data = {
            "format": "v200",
            "device": 10,
            "streamer_index": 100,
            "streamer_selector": 65536,
            "device_sent_timestamp": 1,
            "seqid": 1,
            "lowest_id": 2,
            "highest_id": 3,
            "events": [
                {
                    "stream": "5020",
                    "timestamp": "2018-01-20T00:00:00.100000Z",
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
                    "timestamp": "2018-01-20T01:12:00Z",
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
        report = FlexibleDictionaryReport(encoded, False, False)

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
