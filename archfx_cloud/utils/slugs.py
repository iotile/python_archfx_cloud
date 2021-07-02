import re
import unicodedata
from datetime import datetime
from functools import lru_cache

from .convert import (
    gid_join,
    gid_split,
    fix_gid,
    int2did,
    int16gid,
    int2pid,
    int2vid,
    gid2int,
)


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Also strip leading and trailing whitespace.
    """
    if isinstance(value, int):
        value = str(value)
    assert isinstance(value, str)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip()
    return re.sub(r'[-\s]+', '-', value).lower()


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
        if parts[0] not in ['ps', 'pa', 'pl', 'd', ]:
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

        if isinstance(id, str):
            parts = gid_split(id)
            if len(parts) == 1:
                did = parts[0]
            else:
                if parts[0] not in ['d', 'm']:
                    raise ValueError('ArchFxDeviceSlug: must start with a "d" or "m"')
                did = gid_join(parts[1:])

            id = gid2int(did)  # Canonicalize to int

        if not isinstance(id, int):
            raise ValueError(f"ArchFxDeviceSlug: not convertible from {type(id)}")

        if id < 0 or id >= pow(16, hex_count):
            raise ValueError('ArchFxDeviceSlug: UUID should be greater or equal than zero and less than 16^12')

        self.set_from_single_id_slug('d', 4, int2did(id))


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

            id_ = f"{scope}-{var}"

        if isinstance(id_, str):
            parts = gid_split(id_)
            if len(parts) == 1:
                vid = parts[0]
            else:
                raise ValueError('ArchFxVariableID: must start with a digit')

            id_ = gid2int(vid)  # Canonicalize to int

        if not isinstance(id_, int):
            raise ValueError(f"ArchFxDeviceSlug: not convertible from {type(id_)}")

        if id_ < 0 or id_ >= pow(16, 8):
            raise ValueError('ArchFxVariableID: ID should be greater or equal than zero and less than 16^8')

        self.set_from_single_id_slug(None, None, int2vid(id_))

    def formatted_id(self):
        """Formatted ID is the same as a Slug for a VariableID"""
        return self._slug

    def set_from_single_id_slug(self, stype, terms, id_):
        """Create slug, and ensure it is formatted XXXX-YYYYY"""
        self._slug = fix_gid(id_, 2)

    @lru_cache()
    def get_id(self):
        """Return integer representation of ID"""
        parts = gid_split(self._slug)
        if len(parts) != 1:
            raise ValueError('ArchFxVariableID should not have stype')
        return gid2int(parts[0])

    @property
    @lru_cache()
    def var_hex(self):
        """Return HEX representation of the variable id (no scope)"""
        return self._slug[5:9]

    @property
    @lru_cache()
    def scope_hex(self):
        """Return HEX representation of the scope (no scope)"""
        return self._slug[0:4]

    @property
    @lru_cache()
    def var_id(self):
        """Return the 16 Least significant bits representing the variable id"""
        return 0xFFFF & self.get_id()

    @property
    @lru_cache()
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
        if not sid:
            self.stype = 'sd'
            return

        if not isinstance(sid, str):
            raise ValueError("Stream ID must be str")

        parts = gid_split(sid)
        if not 4 <= len(parts) <= 5:
            raise ValueError("Stream slug must have at least four terms: s<type>--<prnt>--<dev>--<var> - "
                             "and at most five: s<type>--<prnt>--<dev>--<var>--<start>")

        if parts[1] == '':
            parts[1] = '0000-0000'

        parts[0] = parts[0]  # TODO: get parts[0] from parent
        parts[1] = ArchFxParentSlug(parts[1]).formatted_id()
        parts[2] = ArchFxDeviceSlug(parts[2]).formatted_id()
        parts[3] = str(ArchFxVariableID(parts[3]))
        if len(parts) == 5:
            # TODO: check
            parts[4] = parts[4]

        # Make sure we expand to ensure we end up with a 63 char string
        # expanding with any missing zeros
        self._slug = gid_join(parts)
        self.stype = parts[0]

    def from_parts(self, parent, device, variable, start=None):
        """
        Build slug from the different parts: Parent, Device and Variable
        """
        parts = []

        if parent is None or parent == '':
            # It is legal to pass something like `s----1234--5001` as projects are optional
            parent = ArchFxParentSlug(0)
            self.stype = 'sd'
        else:
            if not isinstance(parent, ArchFxParentSlug):
                parent = ArchFxParentSlug(parent)
            self.stype = self.STYPES_FROM_PTYPE[parent.get_type()]
        parts.append(self.stype)
        parts.append(parent.formatted_id())

        if device is None or device == '':
            # It is legal to pass something like `s--0123----5001` as projects are optional
            device = ArchFxDeviceSlug(0)
        elif not isinstance(device, ArchFxDeviceSlug):
            # Allow 64bits to handle blocks
            device = ArchFxDeviceSlug(device, allow_64bits=True)
        parts.append(device.formatted_id())

        if not isinstance(variable, ArchFxVariableID):
            variable = ArchFxVariableID(variable)
        parts.append(str(variable))

        if start is not None:
            if isinstance(start, datetime):
                start = int(start.timestamp() * 10**6)
            else:
                # Else assume it's already in acceptable form
                start = int(start)
                if len(str(start)) > 16:
                    raise ValueError(f'Start timestamp of {start} us is too big (must fit into 16 decimal places)')

            parts.append(f'{start:016}')

        self._slug = gid_join(parts)

    def get_parts(self):
        """
        Get the different components of the slug:
        - Parent: Site, Line or Area
        - Block: If this represents an Archive
        - Score: 0000 for devices or something else for machines
        - device: ID of the device or machine
        - variable: ID of the variable
        - start: Microsecond unix timestamp of the stream start
        """
        parts = gid_split(self._slug)
        assert 4 <= len(parts) <= 5
        parent = ArchFxParentSlug(parts[1], ptype=self.PTYPES_FROM_STYPE[parts[0]]) if parts[1] else ArchFxParentSlug(0)
        device_parts = parts[2].split('-')
        variable = parts[3]
        start = parts[4] if len(parts) == 5 else None
        result = {
            'parent': str(parent),
            'block': device_parts[0],
            'scope': device_parts[1],
            'device': '-'.join(device_parts[2:]),
            'variable': str(variable),
            'start': start
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
