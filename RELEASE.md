# Release Notes

All major changes in each released version of the archfx-cloud plugin are listed here.

## 0.17.0

- Made `ArchFxCloudSlug` (and all its derived classes) usable as a mapping key by overriding the `__hash__()` method.
- Made `ArchFxCloudSlug` (and all its derived classes) considered equal if their `slug` attributes are equal by overriding the `__eq__()` method.

## 0.16.0

- Updated `dev` domain in `BaseMain` class to be `http://localhost`.

## 0.15.0

- Use the endpoint `/auth/user-info/` to get account information in the `BaseMain` class.

## 0.14.0

- Add optional parameter to BaseMain constructor to give the config file path (.ini)
- Config file can configure JWT token (access and refresh)
- Provided user email is not required anymore if logging in via token
- Avoid one API request with empty token if no token provided

## 0.13.0

- Removed unneed pytz dependency

## 0.12.0

- Support `ArchFXFlexibleDictionaryReport` direct upload

## 0.11.0

- Support Django SimpleJWT authentication variety
- Fix scenario where base URL not ending with slash will create invalid URL paths
- Use session for storage of authentication headers
- Code modernization and cleanups

## 0.10.3

- Fix bug where slug expansion produces malformed slugs

## 0.10.2

- Remove mock_cloud until a proper ArchFX Cloud Mock is created

## 0.10.1

- Change BaseMain defaults for --customer (now "arch") and --server (now "prod")

## 0.10.0

- Add ArchFXFlexibleDictionaryReport to generate streamer reports compatible with ArchFX Cloud

## 0.9.1

- Add Github Actions

## 0.9.0

- Initial release with port from python-iotile-cloud and updates to
  match ArchFX Cloud specific slugs
