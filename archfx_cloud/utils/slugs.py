from .convert import *

class ArchFxCloudSlug(object):
    _slug = None

    def __str__(self):
        return self._slug

    def formatted_id(self):
        parts = gid_split(self._slug)
        return gid_join(parts[1:])

    def set_from_single_id_slug(self, stype, terms, id_):
        """Create slug for an ID, based on the stype and number of terms"""
        if stype not in ['pl', 'ps', 'pa', 'm', 'd', 'b', 'g']:
            raise ValueError('Slugs must start with p/d/b/g')
        if not isinstance(id_, str):
            raise ValueError('Slug must be a string')
        parts = gid_split(id_)
        if parts[0] in ['pl', 'ps', 'pa', 'm', 'd', 'b', 'g']:
            id_ = parts[1]
        id_ = fix_gid(id_, terms)
        self._slug = gid_join([stype, id_])

    def get_id(self):
        parts = gid_split(self._slug)
        if len(parts) != 2:
            raise ValueError('Cannot call get_id() for IDs with more than one term')
        if parts[0] not in ['ps', 'pa', 'pl', 'd',]:
            raise ValueError('Only Devices/DataBlocks/Fleets have single IDs')
        return gid2int(parts[1])


class ArchFxParentSlug(ArchFxCloudSlug):
    """
    Formatted Global Site, Area or Line ID:
       ps--0000-0001, pa--0000-0001, pl--0000-0001
    """
    _type = 'pl'

    def __init__(self, id, ptype='pl'):
        self._type = ptype
        if isinstance(id, ArchFxParentSlug):
            self._slug = id._slug
            self._type = id.get_type()
            return
        elif isinstance(id, int):
            if id < 0 or id >= pow(16, 8):
                raise ValueError('ArchFxProjectSlug: UUID should be greater or equal than zero and less than 16^8')
            pid = int2pid(id)
        else:
            parts = gid_split(id)
            if len(parts) == 1:
                pid = parts[0]
            else:
                if parts[0] not in ['pl', 'ps', 'pa']:
                    raise ValueError('ArchFxProjectSlug: must start with a "p"')
                pid = gid_join(parts[1:])
                self._type = parts[0]

            # Convert to int and back to get rid of anything above 48 bits
            id = gid2int(pid)
            if id < 0 or id >= pow(16, 8):
                raise ValueError('ArchFxProjectSlug: UUID should be greater or equal than zero and less than 16^8')
            pid = int2pid(id)

        self.set_from_single_id_slug(self._type, 2, pid)

    def get_type(self):
        return self._type


class ArchFxDeviceSlug(ArchFxCloudSlug):
    """Formatted Global Device ID: d--0000-0000-0000-0001"""

    def __init__(self, id, allow_64bits=True):
        # For backwards compatibility, allow 64 bit IDs if required
        # Meaning that the device may in fact be a data block
        hex_count = 16 if allow_64bits else 12

        if isinstance(id, ArchFxDeviceSlug):
            self._slug = id._slug
            return

        if isinstance(id, int):
            if id < 0 or id >= pow(16, hex_count):
                raise ValueError('ArchFxDeviceSlug: UUID should be greater or equal than zero and less than 16^12')
            did = int2did(id)
        else:
            if not isinstance(id, str):
                raise ValueError('ArchFxDeviceSlug: must be an int or str')
            parts = gid_split(id)
            if len(parts) == 1:
                did = parts[0]
            else:
                if parts[0] not in ['d', 'm']:
                    raise ValueError('ArchFxDeviceSlug: must start with a "d" or "m"')
                did = gid_join(parts[1:])

            # Convert to int and back to get rid of anything above 48 bits
            id = gid2int(did)
            if id < 0 or id >= pow(16, hex_count):
                raise ValueError('ArchFxDeviceSlug: UUID should be greater or equal than zero and less than 16^12')

        self.set_from_single_id_slug('d', 4, did)


class ArchFxVariableID(ArchFxCloudSlug):
    """
    Formatted Local Variable ID: 0000-0001
    This is a 32bit number with first 16bits representing a scope
    and the last 16bits repreenting the actual variable ID.
    This is different from other Slugs in that it does
    not represent a globally unique ID. Variable IDs are only
    unique within a Device/Machine.
    Args:
        id: string, integer, a single int/string pair (tuple) or another VariableID version of a variable ID. If pair
            version is used, it must be (scope, var) (so scope is at index 0).
    """

    def __init__(self, id_):
        if isinstance(id_, ArchFxVariableID):
            self._slug = id_._slug
            return

        if isinstance(id_, tuple):
            scope, var = id_

            if isinstance(scope, int):
                if scope < 0 or scope >= pow(16, 4):
                    raise ValueError('ArchFxVariableID: Scope should be greater or equal than zero and less than 16^4')
                scope = int16gid(scope)

            if isinstance(var, int):
                if var < 0 or var >= pow(16, 4):
                    raise ValueError('ArchFxVariableID: Var should be greater or equal than zero and less than 16^4')
                var = int16gid(var)

            id_ = '-'.join([scope, var])

        if isinstance(id_, int):
            if id_ < 0 or id_ >= pow(16, 8):
                raise ValueError('ArchFxVariableID: ID should be greater or equal than zero and less than 16^8')
            vid = int2vid(id_)
        else:
            if not isinstance(id_, str):
                raise ValueError('ArchFxVariabeID: must be an int or str: {}'.format(type(id_)))
            parts = gid_split(id_)
            if len(parts) == 1:
                vid = parts[0]
            else:
                raise ValueError('ArchFxVariableID: must start with a digit')

            # Convert to int and back to get rid of anything above 32 bits
            int_id = gid2int(vid)
            if int_id < 0 or int_id >= pow(16, 8):
                raise ValueError('ArchFxVariableID: ID should be greater or equal than zero and less than 16^8')
            vid = int2vid(int_id)

        self.set_from_single_id_slug(None, None, vid)

    def formatted_id(self):
        """Formatted ID is the same as a Slug for a VariableID"""
        return self._slug

    def set_from_single_id_slug(self, stype, terms, id_):
        """Create slug, and ensure it is formatted XXXX-YYYYY"""
        self._slug = fix_gid(id_, 2)

    def get_id(self):
        """Return integer representation of ID"""
        parts = gid_split(self._slug)
        if len(parts) != 1:
            raise ValueError('ArchFxVariableID should not have stype')
        return gid2int(parts[0])

    @property
    def var_hex(self):
        """Return HEX representation of the variable id (no scope)"""
        return self._slug[5:9]

    @property
    def scope_hex(self):
        """Return HEX representation of the scope (no scope)"""
        return self._slug[0:4]

    @property
    def var_id(self):
        """Return the 16 Least significant bits representing the variable id"""
        return 0xFFFF & self.get_id()

    @property
    def scope(self):
        """Return the 16 Most significant bits representing the variable scope"""
        return (0xFFFF0000 & self.get_id()) >> 16


class ArchFxStreamSlug(ArchFxCloudSlug):
    stype = 'sd'

    PTYPES_FROM_STYPE = {
        'sl': 'pl',
        'sa': 'pa',
        'ss': 'ps'
    }
    STYPES_FROM_PTYPE = {
        'pl': 'sl',
        'pa': 'sa',
        'ps': 'ss'
    }
    def __init__(self, sid=None):
        if sid:
            if not isinstance(sid, str):
                raise ValueError("Variable ID must be int or str")
            parts = gid_split(sid)
            if len(parts) != 4:
                raise ValueError("Stream slug must have three terms: s--<prj>--<dev>--<var>")
            if parts[1] == '':
                parts[1] = '0000-0000'
            # Make sure we expand to ensure we end up with a 45 char string
            # expanding with any missing zeros
            self._slug = gid_join([
                parts[0],
                ArchFxParentSlug(parts[1]).formatted_id(),
                ArchFxDeviceSlug(parts[2]).formatted_id(),
                str(ArchFxVariableID(parts[3]))
            ])
            self.stype = parts[0]

    def from_parts(self, parent, device, variable):
        """
        Build slug from the different parts: Parent, Device and Variable
        """
        if parent is None or parent == '':
            # It is legal to pass something like `s----1234--5001` as projects are optional
            parent = ArchFxParentSlug(0)
            self.stype = 'sd'
        else:
            parent = ArchFxParentSlug(parent)
            self.stype = self.STYPES_FROM_PTYPE[parent.get_type()]
        if device is None or device == '':
            # It is legal to pass something like `s--0123----5001` as projects are optional
            device = ArchFxDeviceSlug(0)
        elif not isinstance(device, ArchFxDeviceSlug):
            # Allow 64bits to handle blocks
            device = ArchFxDeviceSlug(device, allow_64bits=True)
        if not isinstance(variable, ArchFxVariableID):
            variable = ArchFxVariableID(variable)
        self._slug = gid_join([
            self.stype,
            parent.formatted_id(),
            device.formatted_id(),
            str(variable)
        ])

    def get_parts(self):
        """
        Get the different components of the slug:
        - Parent: Site, Line or Area
        - Block: If this represents an Archive
        - Score: 0000 for devices or something else for machines
        - device: ID of the device or machine
        - variable: ID of the variable
        """
        parts = gid_split(self._slug)
        assert len(parts) == 4
        parent = ArchFxParentSlug(parts[1]) if parts[1] else ArchFxParentSlug(0)
        device_parts = parts[2].split('-')
        variable = parts[3]
        result = {
            'parent': str(parent),
            'block': device_parts[0],
            'scope': device_parts[1],
            'device': '-'.join(device_parts[2:]),
            'variable': str(variable)
        }
        return result


class ArchFxStreamerSlug(ArchFxCloudSlug):
    """Formatted Global Streamer ID: t--0000-0000-0000-0000--0000.
    Args:
        device (str, int or ArchFxDeviceSlug): The device that this streamer corresponds with.
        index (int): The sub-index of the stream in the device, typically a small number in [0, 8)
    """

    def __init__(self, device, index):
        if isinstance(device, int):
            device_id = device
        elif isinstance(device, ArchFxDeviceSlug):
            device_id = device.get_id()
        elif isinstance(device, str):
            device_id = ArchFxDeviceSlug(device).get_id()
        else:
            raise ValueError("ArchFxStreamerSlug: Unknown device specifier, must be string, int or ArchFxDeviceSlug")

        index = int(index)

        device_gid48 = int2did(device_id)
        index_gid = int16gid(index)
        device_gid = fix_gid(device_gid48, 4)

        self._slug = gid_join(['t', device_gid, index_gid])
        self._device = gid_join(['d', device_gid])
        self._index = index_gid

    def get_device(self):
        """Get the device slug as a string."""
        return self._device

    def get_index(self):
        """Get the streamer index in the device as a padded string."""
        return self._index
