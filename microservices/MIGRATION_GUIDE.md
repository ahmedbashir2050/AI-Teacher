# Database Migrations Guide (Alembic)

This guide outlines the production-grade strategy for database migrations in the AI Teacher microservices architecture.

## 🚀 Strategy: Automatic & Safe

1.  **Automatic Execution**: Migrations are executed automatically during service deployment via the `entrypoint.sh` of each container (`alembic upgrade head`).
2.  **CI/CD Verification**: Every Pull Request triggers a CI job that:
    - Verifies that models and migration scripts are in sync (`alembic check`).
    - Verifies that all migrations can be applied from scratch (`alembic upgrade head`).
    - Verifies that rollbacks are possible (`alembic downgrade base`).
3.  **Idempotence**: All migrations must be idempotent. Alembic's version tracking ensures that only necessary migrations are applied.

## 🛡️ Backward Compatibility (No-Breakage Policy)

To support zero-downtime rolling updates, migrations must not break the *currently running* version of the service.

### ✅ Do's
- **Adding Columns**: Always make new columns `nullable` or provide a default value.
- **Adding Tables**: Safe to do at any time.
- **Adding Indexes**: Safe, but consider `CONCURRENTLY` for large production tables (PostgreSQL specific).

### ❌ Don'ts (Destructive Changes)
- **Renaming Columns**:
    - *Instead*: Add a new column, double-write to both, migrate data, then update code to use the new column, and finally drop the old one in a later release.
- **Dropping Columns**:
    - *Instead*: First update the code to stop using the column, deploy, then create a migration to drop it in the next release.
- **Changing Data Types**:
    - *Instead*: Add a new column with the target type, migrate data, then switch.

## 🔄 Rollback Plan

If a deployment fails, the following rollback strategy is applied:
1.  **Immediate Reversion**: Revert the container image to the previous stable version.
2.  **Database Downgrade**: If the new schema is incompatible with the old code, run `alembic downgrade -1` manually via a management task.
    - *Note*: Our No-Breakage Policy aims to make the database compatible with both the new and old code, often making a DB downgrade unnecessary for a code rollback.

## 🛠️ Creating Migrations

```bash
# Inside the specific service directory
export DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
alembic revision --autogenerate -m "description of change"
```

Always review the auto-generated migration script to ensure it follows the backward compatibility rules.
