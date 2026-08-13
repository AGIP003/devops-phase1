# Legacy learning archive

This directory preserves earlier implementations for study and comparison.
Files here are not part of the running application and must not be imported by
routes, services, models, tests, or deployment entry points.

`legacy_psycopg2_db.py` records the project's original raw-psycopg2 data layer.
The active data layer uses SQLAlchemy ORM services in `app/services/`.
