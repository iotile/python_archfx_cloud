import unittest2 as unittest
import datetime
import pytest

from archfx_cloud.utils.slugs import (
    ArchFxParentSlug,
    ArchFxDeviceSlug,
    ArchFxVariableID,
    ArchFxStreamSlug,
    ArchFxStreamerSlug
)

ArchFxVariableID_CASES = (
    ("int-no-scope", 0x5051, '0000-5051', 0, 0x5051),
    ("int-with-scope", 0x10000 | 0x5051, '0001-5051', 1, 0x5051),
    ("string-no-scope", '5051', '0000-5051', 0, 0x5051),
    ("scoped-string", '0001-5051', '0001-5051', 1, 0x5051),
    ("scoped-string-no-delimiter", 'f5051', '000f-5051', 0x0f, 0x5051),
    ("int-tuple", (1, 0x5051), '0001-5051', 1, 0x5051),
    ("string-tuple", ("1", "5051"), '0001-5051', 1, 0x5051),
)
ArchFxVariableID_NAMES = [x[0] for x in ArchFxVariableID_CASES]


@pytest.mark.parametrize("name, input, formatted, scope, var", ArchFxVariableID_CASES, ids=ArchFxVariableID_NAMES)
def test_ArchFxVariableID(name, input, formatted, scope, var):
    result = ArchFxVariableID(input)
    assert str(result) == formatted
    assert result.formatted_id() == formatted
    assert result.get_id() == (scope << 16) + var
    assert result.var_id == var
    assert result.var_hex == f"{var:04x}"
    assert result.scope == scope
    assert result.scope_hex == f"{scope:04x}"


class SlugTestCase(unittest.TestCase):

    def test_parent_slug(self):
        id = ArchFxParentSlug(5)
        self.assertEqual(str(id), 'pl--0000-0005')

        # We allow parents to be zero as we use that to represent no parent
        id = ArchFxParentSlug(0, ptype='pa')
        self.assertEqual(str(id), 'pa--0000-0000')
        id = ArchFxParentSlug('pa--0000-0000')
        self.assertEqual(str(id), 'pa--0000-0000')

        id = ArchFxParentSlug('pl--0000-1234')
        self.assertEqual(str(id), 'pl--0000-1234')

        id = ArchFxParentSlug('pl--1234')
        self.assertEqual(str(id), 'pl--0000-1234')

        id = ArchFxParentSlug('pl--1')
        self.assertEqual(str(id), 'pl--0000-0001')

        id = ArchFxParentSlug('0005')
        self.assertEqual(str(id), 'pl--0000-0005')

        self.assertEqual(id.formatted_id(), '0000-0005')

        self.assertRaises(ValueError, ArchFxParentSlug, 'string')
        self.assertRaises(ValueError, ArchFxParentSlug, 'x--0000-0001')
        self.assertRaises(ValueError, ArchFxParentSlug, 'p--1234-0000-0000-0001')  # > 16bts
        self.assertRaises(ValueError, ArchFxParentSlug, -5)
        self.assertRaises(ValueError, ArchFxParentSlug, pow(16, 8))

    def test_device_slug(self):
        id = ArchFxDeviceSlug(0)
        self.assertEqual(str(id), 'd--0000-0000-0000-0000')
        id = ArchFxDeviceSlug(5)
        self.assertEqual(str(id), 'd--0000-0000-0000-0005')
        id = ArchFxDeviceSlug(0xa)
        self.assertEqual(str(id), 'd--0000-0000-0000-000a')

        id = ArchFxDeviceSlug('d--0000-0000-1234')
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')

        id = ArchFxDeviceSlug('d--0000-0000-0000-1234')
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')
        id = ArchFxDeviceSlug(id)
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')

        id = ArchFxDeviceSlug('d--1')
        self.assertEqual('d--0000-0000-0000-0001', str(id))

        id = ArchFxDeviceSlug('d--1234')
        self.assertEqual(str(id), 'd--0000-0000-0000-1234')

        id = ArchFxDeviceSlug('d--1234-0000-0000-0001', allow_64bits=True)
        self.assertEqual(str(id), 'd--1234-0000-0000-0001')

        id = ArchFxDeviceSlug('0005')
        self.assertEqual(str(id), 'd--0000-0000-0000-0005')
        self.assertEqual(id.formatted_id(), '0000-0000-0000-0005')
        id = ArchFxDeviceSlug('0000')
        self.assertEqual(str(id), 'd--0000-0000-0000-0000')
        self.assertEqual(id.formatted_id(), '0000-0000-0000-0000')
        id = ArchFxDeviceSlug('0000-0000-0000')
        self.assertEqual(str(id), 'd--0000-0000-0000-0000')
        self.assertEqual(id.formatted_id(), '0000-0000-0000-0000')

        self.assertRaises(ValueError, ArchFxDeviceSlug, 'string')
        self.assertRaises(ValueError, ArchFxDeviceSlug, 'x--0000-0000-0000-0001')
        self.assertRaises(ValueError, ArchFxDeviceSlug, 'd--1234-0000-0000-0001', False)  # > 48bts
        self.assertRaises(ValueError, ArchFxDeviceSlug, b'binary string')
        self.assertRaises(ValueError, ArchFxDeviceSlug, -5)
        self.assertRaises(ValueError, ArchFxDeviceSlug, pow(16, 16))
        self.assertRaises(ValueError, ArchFxDeviceSlug, pow(16, 12), False)

    def test_stream_slug(self):
        slug1 = ArchFxStreamSlug('sl--0000-0001--0000-0000-0000-0002--5051')
        parts = slug1.get_parts()
        self.assertEqual(parts['parent'], 'pl--0000-0001')
        self.assertEqual(parts['block'], '0000')
        self.assertEqual(parts['scope'], '0000')
        self.assertEqual(parts['device'], '0000-0002')
        self.assertEqual(parts['start'], None)

        slug2 = ArchFxStreamSlug()
        slug2.from_parts(
            parent='pa--0000-0001',
            device='d--0000-0001-0000-0123',
            variable='5051'
        )
        self.assertEqual(str(slug2), 'sa--0000-0001--0000-0001-0000-0123--0000-5051')

        slug3 = ArchFxStreamSlug()
        slug3.from_parts(
            parent=None,
            device='d--0000-0001-0000-0123',
            variable='0001-5051'
        )
        self.assertEqual(str(slug3), 'sd--0000-0000--0000-0001-0000-0123--0001-5051')

        slug4 = ArchFxStreamSlug()
        slug4.from_parts(
            parent='pa--0000-0001',
            device='d--0000-0001-0000-0123',
            variable=0x5051
        )
        self.assertEqual(str(slug4), 'sa--0000-0001--0000-0001-0000-0123--0000-5051')

        slug5 = ArchFxStreamSlug()
        slug5.from_parts(
            parent=ArchFxParentSlug('ps--0000-0001'),
            device=ArchFxDeviceSlug('d--0000-0001-0000-0123'),
            variable=ArchFxVariableID(0x5051)
        )
        self.assertEqual(str(slug5), 'ss--0000-0001--0000-0001-0000-0123--0000-5051')

        slug6 = ArchFxStreamSlug()
        slug6.from_parts(
            parent=ArchFxParentSlug('pa--0000-0001'),
            device=ArchFxDeviceSlug('d--0000-0001-0000-0123'),
            variable=ArchFxVariableID(0x10000 | 0x5051)
        )
        self.assertEqual(str(slug6), 'sa--0000-0001--0000-0001-0000-0123--0001-5051')

        slug7 = ArchFxStreamSlug('sa--0000-0001--0000-0001-0000-0123--0001-5051')
        parts = slug7.get_parts()
        self.assertEqual(parts['block'], '0000')
        self.assertEqual(parts['scope'], '0001')
        self.assertEqual(parts['device'], '0000-0123')
        self.assertEqual(parts['variable'], '0001-5051')
        self.assertEqual(parts['parent'], 'pa--0000-0001')
        self.assertEqual(parts['start'], None)

        slug8 = ArchFxStreamSlug('sl--0000-0001--0000-0001-0000-0123--0001-5051')
        parts = slug8.get_parts()
        self.assertEqual(parts['block'], '0000')
        self.assertEqual(parts['scope'], '0001')
        self.assertEqual(parts['device'], '0000-0123')
        self.assertEqual(parts['variable'], '0001-5051')
        self.assertEqual(parts['parent'], 'pl--0000-0001')
        self.assertEqual(parts['start'], None)

        slug9 = ArchFxStreamSlug('ss--0000-0001--0000-0001-0000-0123--0001-5051')
        parts = slug9.get_parts()
        self.assertEqual(parts['block'], '0000')
        self.assertEqual(parts['scope'], '0001')
        self.assertEqual(parts['device'], '0000-0123')
        self.assertEqual(parts['variable'], '0001-5051')
        self.assertEqual(parts['parent'], 'ps--0000-0001')
        self.assertEqual(parts['start'], None)

        slug10 = ArchFxStreamSlug('sa--0001--0000-0123--5051')
        parts = slug10.get_parts()
        self.assertEqual(parts['block'], '0000')
        self.assertEqual(parts['scope'], '0000')
        self.assertEqual(parts['device'], '0000-0123')
        self.assertEqual(parts['variable'], '0000-5051')
        self.assertEqual(parts['parent'], 'pa--0000-0001')
        self.assertEqual(parts['start'], None)

        slug11 = ArchFxStreamSlug('sl--0000-0001--0000-0001-0000-0123--0001-5051--1612829726628904')
        parts = slug11.get_parts()
        self.assertEqual(parts['block'], '0000')
        self.assertEqual(parts['scope'], '0001')
        self.assertEqual(parts['device'], '0000-0123')
        self.assertEqual(parts['variable'], '0001-5051')
        self.assertEqual(parts['parent'], 'pl--0000-0001')
        self.assertEqual(parts['start'], '1612829726628904')

        slug12 = ArchFxStreamSlug()
        slug12.from_parts(
            parent='pa--0000-0001',
            device='d--0000-0001-0000-0123',
            variable='5051',
            start='1612829726628904'
        )
        self.assertEqual(str(slug12), 'sa--0000-0001--0000-0001-0000-0123--0000-5051--1612829726628904')

        slug13 = ArchFxStreamSlug()
        with self.assertRaises(ValueError):
            slug13.from_parts(
                parent='pa--0000-0001',
                device='d--0000-0001-0000-0123',
                variable='5051',
                start='16128297266289040'  # 17 digits is too many
            )

        now = datetime.datetime.now()
        slug14 = ArchFxStreamSlug()
        slug14.from_parts(
            parent='pa--0000-0001',
            device='d--0000-0001-0000-0133',
            variable='5051',
            start=now
        )
        self.assertEqual(str(slug14), f'sa--0000-0001--0000-0001-0000-0133--0000-5051--{int(now.timestamp() * 10**6)}')
