# Database Migrations

This directory contains database migration files for both Firebase and Neon PostgreSQL.

## Migration Format

Migrations follow the format: `YYYYMMDD_HHMMSS_description.sql` or `.ts` for TypeScript migrations.

## Providers

- **Firebase**: Firestore data structure migrations
- **Neon**: PostgreSQL schema migrations

## Configuration

Migrations are configured in:
- `global-config.yaml`: Main configuration
- `ctb/sys/neon/neon.config.json`: Neon-specific settings
- `ctb/sys/firebase/firebase.json`: Firebase-specific settings

## Running Migrations

Migrations are set to manual execution (`auto_run: false` in config).

To run migrations:
1. Review migration files
2. Test in development environment
3. Execute manually using migration tool
4. Verify schema changes

## Schema Validation

Schema validation is enabled to ensure data integrity across migrations.
