import unittest2 as unittest
import pytest

from archfx_cloud.utils.slugs import (
    ArchFxParentSlug,
    ArchFxDeviceSlug,
    ArchFxVariableID,
    ArchFxStreamSlug,
    ArchFxStreamerSlug
)


class GIDTestCase(unittest.TestCase):

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

        id = ArchFxParentSlug('0005')
        self.assertEqual(str(id), 'pl--0000-0005')

        self.assertEqual(id.formatted_id(), '0000-0005')

        self.assertRaises(ValueError, ArchFxParentSlug, 'string')
        self.assertRaises(ValueError, ArchFxParentSlug, 'x--0000-0001')
        self.assertRaises(ValueError, ArchFxParentSlug, 'p--1234-0000-0000-0001') # > 16bts
        self.assertRaises(ValueError, ArchFxParentSlug, -5)
        self.assertRaises(ValueError, ArchFxParentSlug, pow(16,8))


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
        self.assertRaises(ValueError, ArchFxDeviceSlug, 'd--1234-0000-0000-0001', False) # > 48bts
        self.assertRaises(ValueError, ArchFxDeviceSlug, -5)
        self.assertRaises(ValueError, ArchFxDeviceSlug, pow(16,16))
        self.assertRaises(ValueError, ArchFxDeviceSlug, pow(16,12), False)

    def test_variable_slugs(self):

        var1 = ArchFxVariableID('5051')
        self.assertEqual(str(var1), '0000-5051')
        self.assertEqual(var1.formatted_id(), '0000-5051')
        self.assertEqual(var1.get_id(), 0x5051)
        self.assertEqual(var1.var_id, 0x5051)
        self.assertEqual(var1.var_hex, '5051')
        self.assertEqual(var1.scope, 0)

        var2 = ArchFxVariableID(0x5051)
        self.assertEqual(str(var2), '0000-5051')
        self.assertEqual(var2.formatted_id(), '0000-5051')

        var3 = ArchFxVariableID(0x10000 | 0x5051)
        self.assertEqual(str(var3), '0001-5051')
        self.assertEqual(var3.formatted_id(), '0001-5051')
        self.assertEqual(var3.get_id(), 0x15051)
        self.assertEqual(var3.var_hex, '5051')
        self.assertEqual(var3.scope_hex, '0001')
        self.assertEqual(var3.var_id, 0x5051)
        self.assertEqual(var3.scope, 1)

        var4 = ArchFxVariableID('0001-5051')
        self.assertEqual(str(var4), '0001-5051')
        self.assertEqual(var4.formatted_id(), '0001-5051')
        self.assertEqual(var4.get_id(), 0x15051)
        self.assertEqual(var4.var_hex, '5051')
        self.assertEqual(var4.scope_hex, '0001')
        self.assertEqual(var4.var_id, 0x5051)
        self.assertEqual(var4.scope, 1)

        var5 = ArchFxVariableID('f5051')
        self.assertEqual(str(var5), '000f-5051')
        self.assertEqual(var5.formatted_id(), '000f-5051')
        self.assertEqual(var5.get_id(), 0xF5051)
        self.assertEqual(var5.var_hex, '5051')
        self.assertEqual(var5.scope_hex, '000f')
        self.assertEqual(var5.var_id, 0x5051)
        self.assertEqual(var5.scope, 0xF)

    def test_stream_slug(self):
        self.assertRaises(ValueError, ArchFxStreamSlug, 5)
        self.assertRaises(ValueError, ArchFxStreamSlug, 's--0001')

        id = ArchFxStreamSlug('sl--0000-0001--0000-0000-0000-0002--0000-0003')
        self.assertEqual(str(id), 'sl--0000-0001--0000-0000-0000-0002--0000-0003')

        parts = id.get_parts()
        self.assertEqual(str(parts['parent']), 'pl--0000-0001')
        self.assertEqual(str(parts['device']), '0000-0002')
        self.assertEqual(str(parts['variable']), '0000-0003')

        id = ArchFxStreamSlug('sl--0000-0000--0000-0000-0000-0002--0000-0003')
        self.assertEqual(str(id), 'sl--0000-0000--0000-0000-0000-0002--0000-0003')

        id = ArchFxStreamSlug('sl----0000-0000-0000-0002--0000-0003')
        self.assertEqual(str(id), 'sl--0000-0000--0000-0000-0000-0002--0000-0003')

        parts = id.get_parts()
        self.assertEqual(str(parts['parent']), 'pl--0000-0000')
        self.assertEqual(str(parts['block']), '0000')
        self.assertEqual(str(parts['scope']), '0000')
        self.assertEqual(str(parts['device']), '0000-0002')
        self.assertEqual(str(parts['variable']), '0000-0003')


    def test_stream_from_parts(self):
        parent = ArchFxParentSlug(5)
        device = ArchFxDeviceSlug(10)
        variable = ArchFxVariableID('0000-5001')

        id = ArchFxStreamSlug()
        id.from_parts(parent=parent, device=device, variable=variable)
        self.assertEqual(str(id), 'sl--0000-0005--0000-0000-0000-000a--0000-5001')
        self.assertEqual(id.formatted_id(), '0000-0005--0000-0000-0000-000a--0000-5001')

        parts = id.get_parts()
        self.assertEqual(str(parts['parent']), str(parent))
        self.assertEqual(str(parts['device']), '0000-000a')
        self.assertEqual(str(parts['variable']), str(variable))

        id = ArchFxStreamSlug()
        pslug = 'pl--0000-0006'
        dslug = 'd--0000-0000-0000-0100'
        vid = '0000-5002'
        id.from_parts(parent=pslug, device=dslug, variable=vid)
        self.assertEqual(str(id), 'sl--0000-0006--0000-0000-0000-0100--0000-5002')

        parts = id.get_parts()
        self.assertEqual(str(parts['parent']), pslug)
        self.assertEqual(str(parts['device']), '0000-0100')
        self.assertEqual(str(parts['variable']), vid)

        id = ArchFxStreamSlug()
        vid = '0000-5002'
        id.from_parts(parent=7, device=1, variable=vid)
        self.assertEqual(str(id), 'sl--0000-0007--0000-0000-0000-0001--0000-5002')

        id = ArchFxStreamSlug()
        id.from_parts(parent=7, device=1, variable='5002')
        self.assertEqual(str(id), 'sl--0000-0007--0000-0000-0000-0001--0000-5002')

        # Project is the only one that can be zero (wildcard)
        id = ArchFxStreamSlug()
        id.from_parts(parent=0, device=1, variable='5002')
        self.assertEqual(str(id), 'sl--0000-0000--0000-0000-0000-0001--0000-5002')
        id.from_parts(parent=None, device=1, variable='5002')
        # self.assertEqual(str(id), 'sl--0000-0000--0000-0000-0000-0001--0000-5002')

        id = ArchFxStreamSlug()
        id.from_parts(parent='', device=1, variable='5002')
        # self.assertEqual(str(id), 'sl--0000-0000--0000-0000-0000-0001--0000-5002')
        id.from_parts(parent=None, device=1, variable='5002')
        # self.assertEqual(str(id), 'sl--0000-0000--0000-0000-0000-0001--0000-5002')

        id = ArchFxStreamSlug()
        with pytest.raises(ValueError):
            id.from_parts(parent=-1, device=1, variable='5002')
        with pytest.raises(ValueError):
            id.from_parts(parent=1, device=-1, variable='5002')
        with pytest.raises(ValueError):
            id.from_parts(parent=1, device=1, variable=-1)

        # Virtual Streams
        id = ArchFxStreamSlug()
        id.from_parts(parent=5, device=0, variable='5001')
        self.assertEqual(str(id), 'sl--0000-0005--0000-0000-0000-0000--0000-5001')
        self.assertEqual(id.formatted_id(), '0000-0005--0000-0000-0000-0000--0000-5001')
        id.from_parts(parent=5, device=None, variable='5001')
        self.assertEqual(str(id), 'sl--0000-0005--0000-0000-0000-0000--0000-5001')
        self.assertEqual(id.formatted_id(), '0000-0005--0000-0000-0000-0000--0000-5001')

    def test_id_property(self):
        parent = ArchFxParentSlug(5)
        self.assertEqual(parent.get_id(), 5)
        device = ArchFxDeviceSlug(10)
        self.assertEqual(device.get_id(), 10)
        variable = ArchFxVariableID('5001')

        id = ArchFxStreamSlug()
        id.from_parts(parent=parent, device=device, variable=variable)
        self.assertRaises(ValueError, id.get_id)

    def test_streamer_gid(self):
        """Ensure that ArchFxStreamerSlug works."""

        s_gid = ArchFxStreamerSlug(1, 2)
        assert str(s_gid) == "t--0000-0000-0000-0001--0002"
        assert s_gid.get_device() == "d--0000-0000-0000-0001"
        assert s_gid.get_index() == "0002"

        s_gid = ArchFxStreamerSlug("d--0000-0000-0000-1234", 1)
        assert str(s_gid) == "t--0000-0000-0000-1234--0001"

        with pytest.raises(ValueError):
            ArchFxStreamerSlug([], 1)

        d_gid = ArchFxDeviceSlug(15)
        s_gid = ArchFxStreamerSlug(d_gid, 0)
        assert str(s_gid) == "t--0000-0000-0000-000f--0000"
        assert s_gid.get_device() == str(d_gid)
        assert s_gid.get_index() == "0000"
