# Release Notes

All major changes in each released version of the archfx-cloud plugin are listed here.

## 0.12.1

- Switch to `auth/api-jwt-auth` for authentication

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
