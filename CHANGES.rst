CHANGES
=======

0.9 (2014-09-07)
------------------

- Support for Django 1.7

- South migrations are moved to ``south_migrations/`` and older Django's should
  upgrade to South 1.0

- Use atomic() transaction handling method introduced in Django 1.6

- Fix bug in the key names used for response caching

- Test improvements


0.8 (2014-04-04)
------------------

- Initial release
