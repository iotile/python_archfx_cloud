# ArchFX Cloud Python API Package

[![PyPI version](https://img.shields.io/pypi/v/archfx_cloud.svg)](https://pypi.python.org/pypi/archfx-cloud)

A python library for interacting with [ArchFX Cloud](https://archfx.io) Rest API.

## Installation

When it comes to using Python packages, it is always recommened you use a Python Virtual Env. Using Python 3, you can simply do

```bash
python3 -m venv  ~/.virtualenv/archfx-cloud
source ~/.virtualenv/archfx-cloud/bin/activate
```

or follow one of the many tutorials to setup Python virtual environments.

Once you have set up a virtual, env, simply install the package with:

```bash
pip install archfx_cloud
```

Package is based on https://github.com/samgiles/slumber and https://github.com/iotile/python_iotile_cloud

## ArchFX Cloud Resource Overview

In a Rest API, Resources represent tables in the database. The following resources are available in **ArchFX Cloud**:

- **account**: Represent users. A user only has access to its own user profile
- **org**: Users belong to Organizations as members. Some of these users can act as admins for the organization.
- **site**: Organizations contain Sites. A site usually represents a geographical location.
- **area**: Sites can have Areas, which either represent a group of discrete manufacturing, or it is a group
of assembly lines. Areas usually represent Buildings or a set of machines of the same type.
- **line**: Sites or Areas can have Lines, which represent assembly lines. Lines are usually created within an area
but do not need to. But like areas, they do need to always belong to a Site.
- **machine**: A Machine represents the physical machine we are extracting data from. It is a virtual concept but
is usually one to one with a machine in the factory, and has a brand, model, serial number and maybe asset number.
- **device**: A device represent IOTile HW Taps, and/or Factory SW connectors that extract data from a Machine. a Given
**Machine** may have multiple HW taps or even multiple SW connectors, which is one there is a one to many
relationship between Machines and Devices
- **stream**: Streams represent a globally unique instance of data comming from a given device (sensor).
Streams represent the virtual data at the machine level (regardless of the device it came from). Over time,
a given stream may come from different devices (e.g. if a device breaks and needs to be replaced).
- **streampages**: A stream is a virtual concept that is build out of **device** data. Data on a device is
represented by a StreamPage. A stream page is always linked to a Stream, but may have a specific start/end
time period. A stream is therefore built out of stream pages, which may or may not come from the same device.
- **data**: Every Stream represents the time series data. This resource can be used to access this data.

### Globally Unique IDs

Most of the key records in the database use a universally unique ID, in the form of an ID Slug. We borrow the term slug
from blogging systems because we use it the same way to create unique but readable URLs.

The following are the resources that use a globally unique ID:

- Sites use **ps--0000-0001**
- Areas use **pa--0000-0001**
- Lines use **pl--0000-0001**
- Device **d--0000-0000-0000-0001** represent device 1. Note that this is also the Serial Number for the device itself,
and can be found on each IOTile Device. For virtual devices (SW connectors), the ID is also assigned from the same
place. Note that all device IDs are allocated and managed by https://iotile.cloud but that should be transparent to users.
All devices have the same `d--0000-0000` scope.
- Machines use the same standard as devices, except that the use a non-zero scope. e.g. **d--0000-0001-0000-0001**
- Sites, Areas, Lines, Machines and Devices can all have streams of data, but all share the same globally unique naming
standard. All streams are named based on `<parent_type>--<parent_id>--<device/machine_id>--<variable_id>` where the variable
is a 32bit identifier, usually following global IDs (e.g. `0000-5051` to represent `ProductReady`):
  - **ss--0000-0001--0000-0000-0000-0000--0000-5051** represents a site stream for site `ps--0000-0001`
  - **sa--0000-0001--0000-0000-0000-0000--0000-5051** represents an area stream for area `pa--0000-0001`
  - **sl--0000-0001--0000-0000-0000-0000--0000-5051** represents a line stream for line `pl--0000-0001`
  - **sl--0000-0001--0000-0000-0000-0001--0000-5051** represents a device stream for device `d--0000-0000-0000-0001` under line `pl--0000-0001`
  - **sl--0000-0001--0000-0001-0000-0001--0000-5051** represents a machine stream for machine `d--0000-0001-0000-0001` under line `pl--0000-0001`

You can see how:

- Slug components are separated by a ‘--’ string
- A one or two character letter(s) represents the type of slug: 'p?', 'd', and 's?'

## User Guide

### Login and Logout

The Api class is used to login and logout from the ArchFX Cloud

Example:

```python
from archfx_cloud.api.connection import Api

c = Api('https://arch.arhfx.io')

ok = c.login(email=args.email, password=password)
if ok:
    # Do something
    
    c.logout()
```

If you have a JWT token, you can skip the login and just set the token:

```python
from archfx_cloud.api.connection import Api

c = Api('https://arch.arhfx.io')

c.set_token('big-ugly-token')
```

You can use the Api itself to login and get a token:

```python
from archfx_cloud.api.connection import Api

c = Api('https://arch.arhfx.io')

ok = c.login(email=args.email, password=password)
if ok:
    token = c.token
    # write out token or store in some secret .ini file
```

### Generic Rest API

The `Api(domain)` can be used to access any of the APIs in https://arch.archfx.io/api/v1/

The `Api(domain)` is generic and therefore will support any future resources supported by the ArchFX Cloud Rest API.

```python
from archfx_cloud.api.connection import Api

api = Api('https://arch.arhfx.io')
ok = api.login(email='user@example.com', password='my.pass')

## GET https://arch.archfx.io/api/v1/org/
##     Note: Any kwargs passed to get(), post(), put(), delete() will be used as url parameters
api.org.get()

## POST https://arch.archfx.io/api/v1/org/
new = api.org.post({"name": "My new Org"})

## PUT https://arch.archfx.io/api/v1/org/{slug}/
api.org(new["slug"]).put({"about": "About Org"})

PATCH https://arch.archfx.io/api/v1/org/{slug}/
api.org(new["slug"]).patch({"about": "About new Org"})

## GET https://arch.archfx.io/api/v1/org/{slug}/
api.org(new["slug"]).get()

## DELETE https://arch.archfx.io/api/v1/org/{slug}/
## NOTE: Not all resources can be deleted by users
api.org(new["slug"]).delete()
```

You can pass arguments to any get() using

```python
# /api/v1/org/
for org in api.org.get()['results']:
   # Pass any arguments as get(foo=1, bar='2'). e.g.
   # /api/v1/site/?org__slug=<slug>
   org_sites = c.site.get(org='{0}'.format(org['slug']))

```

You can also call nested resources/actions like this:

```python
# /api/v1/machine/<slug>/devices/
for org in api.machine.get()['results']:
   # /api/v1/machine/<slug>/devices
   associated_devices = c.machine(org['slug']).devices.get()

```

### Globaly unique ID slugs

To easily handle ID slugs, use the `utils.gid` package:

```python
parent = ArchFxParentSlug(5, ptype='pl)
assert(str(parent) == 'pl--0000-0005')

device = ArchFxDeviceSlug(10)
assert(str(device) == 'd--0000-0000-0000-000a')


id = ArchFxStreamSlug()
id.from_parts(parent=parent, device=device, variable='0000-5501)
assert(str(id) == 'sl--0000-0005--0000-0000-0000-000a--0000-5001')

parts = id.get_parts()
self.assertEqual(str(parts['parent']), str(parent))
self.assertEqual(str(parts['device']), str(device))
self.assertEqual(str(parts['variable']), '0000-5501')

# Other forms of use
device = ArchFxDeviceSlug('000a)
assert(str(device) == 'd--0000-0000-0000-000a')
device = ArchFxDeviceSlug('d--000a')
assert(str(device) == 'd--0000-0000-0000-000a')
device = ArchFxDeviceSlug(0xa)
assert(str(device) == 'd--0000-0000-0000-000a')
```

### BaseMain Utility Class

As you can see from the examples above, every script is likely to follow the following format:

```python
# Parse arguments from user and get password
# Login to server
# Do some real work
# Logout
```

To make it easy to add this boilerplate code, the BaseMain can be used to follow a predefined, opinionated flow
which basically configures the `logging` and `argsparse` python packages with a basic configuration during the 
construction. Then the `main()` method runs the following flow, where each function call can be overwritten in your
own derived class

```python
   self.domain = self.get_domain()
   self.api = Api(self.domain)
   self.before_login()
   ok = self.login()
   if ok:
       self.after_login()
       self.logout()
       self.after_logout()
```

An example of how to use this class is shown below:

```python
class MyScript(BaseMain):

    def add_extra_args(self):
        # Add extra positional argument (as example)
        self.parser.add_argument('foo', metavar='foo', type=str, help='RTFM')

    def before_login(self):
        logger.info('-----------')

    def after_login(self):
        # Main function to OVERWITE and do real work
        do_some_real_work(self.api, self.args)

    def login(self):
        # Add extra message welcoming user
        ok = super(MyScript, self).login()
        if ok:
            logger.info('Welcome {0}'.format(self.args.email))
        return ok

    def logout(self):
        # Add extra message to say Goodbye
        super(MyScript, self).logout()
        logger.info('Goodbye!')


if __name__ == '__main__':

    work = MyScript()
    work.main()
```

### Uploading a Streamer Report

The `ArchFXDataPoint` and `ArchFXFlexibleDictionaryReport` helper classes can be used to generate a Streamer Report
compatible with ArchFX Cloud. A Streamer Report can be used to send several stream data records together.
Using Streamer Reports have several benefits over uploading data manually using the Rest API. Apart from the efficiency
of uploading multiple data points together, the streamer report ensures that data is not processed multiple times.
Each record has a sequential ID which ensures that the cloud will never process data that has already been processed,
allowing Streamer Reports to be uploaded multiple times without worrying about duplication.

The Streamer Report uses [msgpack](https://msgpack.org) as format, which is a compressed JSON file.

Next is a simple example for using these classes:

```python
from datetime import datetime
from io import BytesIO
from dateutil import parser
from archfx_cloud.api.connection import Api
from archfx_cloud.reports.report import ArchFXDataPoint
from archfx_cloud.reports.flexible_dictionary import ArchFXFlexibleDictionaryReport

# Create Data Points
reading = ArchFXDataPoint(
    timestamp=parser.parse('2021-01-20T00:00:00.100000Z'),
    stream='0001-5090',
    value=2.0,
    summary_data={'foo': 5, 'bar': 'foobar'},
    raw_data=None,
    reading_id=1000
)
events.append(reading)
reading = ArchFXDataPoint(
    timestamp=parser.parse('2021-01-20T00:00:00.200000+00:00'),
    stream='0001-5090',
    value=3.0,
    summary_data={'foo': 6, 'bar': 'foobar'},
    reading_id=1001
)
events.append(reading)

# Create Report
sent_time = datetime.datetime.utcnow()
report = ArchFXFlexibleDictionaryReport.FromReadings(
    device='d--1234',
    data=events,
    report_id=1003,
    streamer=0xff,
    sent_timestamp=sent_time
)

# Load Report to the Cloud
api = Api('https://arch.arhfx.io')
ok = api.login(email=args.email, password=password)
if ok:
    fp = ("report.mp", BytesIO(report.encode()))
    resp = api.streamer().report.upload_fp(fp=fp, timestamp=sent_time.isoformat())
```

## Requirements

archfx_cloud requires the following modules.

- Python 3.7+
- requests
- python-dateutil

## Development

To test, run `python setup.py test` or to run coverage analysis:

```bash
coverage run --source=archfx_cloud setup.py test
coverage report -m
```

## Deployment

To deploy to pypi:

1. Update `version.py` with new version number
1. Update `RELEASE.md` with description of new release
1. Run `python setup.py test` to ensure everything is ok
1. Commit all changes to master (PR is needed)
1. Once everythin commited, create a new version Tag. Deployment is triggered from that:

```bash
git tag -a v0.9.13 -m "v0.9.13"
git push origin v0.9.13
```

### Manual Release

All deployments should be done using the Ci/CD process (github actions)
but just for copleteness, this is how a manual deployments is done

```bash
# Test
python setup.py test
# Build
python setup.py sdist bdist_wheel
twine check dist/*
# Publish
twine upload dist/*
```
