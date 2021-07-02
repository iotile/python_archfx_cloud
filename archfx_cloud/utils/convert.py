# pylint: disable=invalid-name
def int16gid(n):
    return f"{n&0xFFFF:04x}"[-4:]


def int32gid(n):
    return f"{n&0xFFFFFFFF:09_x}".replace("_", "-")


def int48gid(n):
    return f"{n&0xFFFFFFFFFFFF:014_x}".replace("_", "-")


def int64gid(n):
    return f"{n&0xFFFFFFFFFFFFFFFF:019_x}".replace("_", "-")


# pylint: enable=invalid-name

int2bid = int16gid
int2did = int64gid
int2did_short = int48gid
int2fleet_id = int48gid
int2pid = int32gid
int2vid = int32gid

gid_split = lambda val: val.split('--')


def gid_join(elements):
    return '--'.join(elements)


def fix_gid(gid, num_terms):
    elements = gid.split('-')
    if len(elements) < num_terms:
        # Prepend '0000' as needed to get proper format (in groups of '0000')
        extras = ['0000' for i in range(num_terms - len(elements))]
        elements = extras + elements
    elif len(elements) > num_terms:
        # Only keep right most terms
        elements = elements[(len(elements) - num_terms):]

    return '-'.join(elements)


def formatted_dbid(bid, did):
    """Formatted Global Data Block ID: d--<block>-<device>"""
    # The old Deviuce ID was 4 4-hex blocks, but the new is only three. Remove the left side block if needed
    device_id_parts = did.split('-')
    if len(device_id_parts) == 4:
        device_id_parts = device_id_parts[1:]
    elif len(device_id_parts) < 3:
        extras = ['0000' for i in range(3 - len(device_id_parts))]
        device_id_parts = extras + device_id_parts
    return gid_join(['b', '-'.join([bid,] + device_id_parts)])


def formatted_machine_id(did, bid='0000', mid='0001'):
    """
    Formatted Global Machine ID: d--XXXX-YYYY-ZZZZ-ZZZZ
    XXXX: 16bit Block ID
    YYYY: 16bit Machine or Scope ID
    ZZZZ: 32bit ID
    """
    # ID should only map
    gid = '-'.join([bid, mid, fix_gid(did, 2)])
    return gid_join(['d', gid])


def formatted_line_id(pid):
    pid = fix_gid(pid, 2)
    return gid_join(['pl', pid])


def formatted_site_id(pid):
    pid = fix_gid(pid, 2)
    return gid_join(['ps', pid])


def formatted_area_id(pid):
    pid = fix_gid(pid, 2)
    return gid_join(['pa', pid])


def formatted_gpid(pid):
    return formatted_line_id(pid)


def formatted_gdid(did, bid='0000'):
    """Formatted Global Device ID: d--0000-0000-0000-0001"""
    # ID should only map
    did = '-'.join([bid, fix_gid(did, 3)])
    return gid_join(['d', did])


def formatted_gsid(pid, did, vid):
    """Formatted Global Stream ID: s--0000-0001--0000-0000-0000-0001--5000"""
    pid = fix_gid(pid, 2)
    did = fix_gid(did, 4)
    return gid_join(['s', pid, did, vid])


def formatted_gtid(did, index):
    """
    Formatted Global Streamer ID: t--0000-0000-0000-0001--0001
    """
    did = fix_gid(did, 4)
    return gid_join(['t', did, index])


def formatted_fleet_id(id):
    """Formatted Global Fleet ID: g--0000-0000-0001"""
    return gid_join(['g', fix_gid(id, 3)])


def gid2int(gid):
    elements = gid.split('-')
    hex_value = ''.join(elements)
    return int(hex_value, 16)


def get_vid_from_gvid(gvid):
    parts = gid_split(gvid)
    return parts[2]


def get_device_and_block_by_did(gid):
    parts = gid_split(gid)
    if parts[0] == 'd' or parts[0] == 'b':
        elements = parts[1].split('-')
        block_hex_value = elements[0]
        device_hex_value = ''.join(elements[1:])
        return int(block_hex_value, 16), int(device_hex_value, 16)
    else:
        return None, None


def get_device_slug_by_block_slug(block_slug):
    parts = gid_split(block_slug)
    return gid_join(['d', parts[1]])
