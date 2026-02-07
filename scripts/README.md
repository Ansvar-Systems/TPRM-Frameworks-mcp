# TPRM Database Management Scripts

This directory contains database management utilities for the TPRM Frameworks MCP server.

## Scripts Overview

| Script | Purpose | Documentation |
|--------|---------|---------------|
| `migrate_db.py` | Database schema migrations | [Migration Guide](#migration-tool) |
| `backup_db.py` | Backup and restore database | [Backup Guide](#backup-tool) |
| `inspect_db.py` | Database inspection and verification | [Inspection Guide](#inspection-tool) |

## Quick Start

### Initial Setup

```bash
# 1. Initialize database schema
python scripts/migrate_db.py --migrate

# 2. Verify database
python scripts/inspect_db.py --verify

# 3. Create initial backup
python scripts/backup_db.py --backup --compress
```

### Daily Operations

```bash
# Check database health
python scripts/inspect_db.py --stats

# Create backup before changes
python scripts/backup_db.py --backup --compress --description "before_update"

# View vendor history
python scripts/inspect_db.py --vendor-history "Salesforce"
```

## Migration Tool

**File:** `migrate_db.py`

### Commands

```bash
# Check current schema version
python scripts/migrate_db.py --check

# View migration status
python scripts/migrate_db.py --status

# Apply pending migrations
python scripts/migrate_db.py --migrate

# Rollback last migration
python scripts/migrate_db.py --rollback

# Force set version (recovery only)
python scripts/migrate_db.py --force-version 1
```

### Options

- `--db-path PATH` - Custom database path
- `--no-backup` - Skip backup before migration (not recommended)

### Examples

```bash
# Standard migration
python scripts/migrate_db.py --migrate

# Use custom database
python scripts/migrate_db.py --db-path /custom/path/db.db --migrate

# Check status without changes
python scripts/migrate_db.py --status
```

## Backup Tool

**File:** `backup_db.py`

### Commands

```bash
# Create backup
python scripts/backup_db.py --backup

# Create compressed backup
python scripts/backup_db.py --backup --compress

# List available backups
python scripts/backup_db.py --list

# Restore from backup
python scripts/backup_db.py --restore /path/to/backup.db.gz

# Show database statistics
python scripts/backup_db.py --stats

# Clean up old backups
python scripts/backup_db.py --cleanup --keep 10
```

### Options

- `--db-path PATH` - Custom database path
- `--backup-dir PATH` - Custom backup directory
- `--compress` - Compress backup with gzip
- `--description TEXT` - Description for backup filename
- `--force` - Force restore without confirmation
- `--keep N` - Number of backups to keep (for cleanup)
- `--detailed` - Show detailed backup information

### Examples

```bash
# Daily backup (compressed)
python scripts/backup_db.py --backup --compress

# Pre-upgrade backup with description
python scripts/backup_db.py --backup --compress --description "before_phase2"

# List all backups with details
python scripts/backup_db.py --list --detailed

# Restore specific backup
python scripts/backup_db.py --restore ~/.tprm-frameworks/backups/tprm_backup_20260207_143022.db.gz

# Cleanup keeping only 10 most recent
python scripts/backup_db.py --cleanup --keep 10
```

## Inspection Tool

**File:** `inspect_db.py`

### Commands

```bash
# Show database statistics
python scripts/inspect_db.py --stats

# List all vendors
python scripts/inspect_db.py --vendors

# Show vendor assessment history
python scripts/inspect_db.py --vendor-history "Vendor Name"

# List recent assessments
python scripts/inspect_db.py --assessments

# Show assessment details
python scripts/inspect_db.py --assessment 12

# List questionnaires
python scripts/inspect_db.py --questionnaires

# Verify database integrity
python scripts/inspect_db.py --verify
```

### Options

- `--db-path PATH` - Custom database path
- `--limit N` - Limit number of results
- `--json` - Output as JSON (for all commands)

### Examples

```bash
# Database health check
python scripts/inspect_db.py --stats
python scripts/inspect_db.py --verify

# Vendor analysis
python scripts/inspect_db.py --vendors --limit 20
python scripts/inspect_db.py --vendor-history "Salesforce" --json

# Assessment review
python scripts/inspect_db.py --assessments --limit 10
python scripts/inspect_db.py --assessment 12

# Export data as JSON
python scripts/inspect_db.py --stats --json > stats.json
python scripts/inspect_db.py --vendors --json > vendors.json
```

## Automated Workflows

### Daily Backup (Cron)

Add to crontab:

```bash
# Daily backup at 2 AM, keep 30 days
0 2 * * * cd /path/to/TPRM-Frameworks-mcp && \
  /path/to/.venv/bin/python scripts/backup_db.py --backup --compress && \
  /path/to/.venv/bin/python scripts/backup_db.py --cleanup --keep 30
```

### Weekly Health Check

```bash
# Weekly integrity check on Sundays at 3 AM
0 3 * * 0 cd /path/to/TPRM-Frameworks-mcp && \
  /path/to/.venv/bin/python scripts/inspect_db.py --verify --json > /var/log/tprm-health.log
```

### Pre-Migration Workflow

```bash
#!/bin/bash
# Complete pre-migration workflow

# 1. Create backup
echo "Creating backup..."
python scripts/backup_db.py --backup --compress --description "pre_migration"

# 2. Verify current state
echo "Verifying database..."
python scripts/inspect_db.py --verify

# 3. Check migration status
echo "Checking migrations..."
python scripts/migrate_db.py --status

# 4. Apply migrations
echo "Applying migrations..."
python scripts/migrate_db.py --migrate

# 5. Verify post-migration
echo "Post-migration verification..."
python scripts/inspect_db.py --verify
```

## Environment Variables

All scripts support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `~/.tprm-frameworks/tprm.db` | Path to SQLite database |
| `BACKUP_DIR` | `~/.tprm-frameworks/backups` | Backup storage directory |

### Usage

```bash
# Use custom database location
export DATABASE_PATH=/custom/path/tprm.db
python scripts/migrate_db.py --check

# Or pass as argument
python scripts/migrate_db.py --db-path /custom/path/tprm.db --check
```

## Troubleshooting

### Database Locked

If you get a "database is locked" error:

```bash
# 1. Check for running processes
lsof ~/.tprm-frameworks/tprm.db

# 2. Stop server
pkill -f tprm_frameworks_mcp

# 3. Retry operation
python scripts/migrate_db.py --migrate
```

### Migration Failed

If migration fails:

```bash
# 1. Check what went wrong
python scripts/migrate_db.py --status

# 2. Restore from backup
python scripts/backup_db.py --list
python scripts/backup_db.py --restore /path/to/backup.db

# 3. Fix issue and retry
python scripts/migrate_db.py --migrate
```

### Corrupted Database

If database is corrupted:

```bash
# 1. Try SQLite recovery
sqlite3 ~/.tprm-frameworks/tprm.db ".recover" | sqlite3 tprm_recovered.db

# 2. Or restore from backup
python scripts/backup_db.py --restore /path/to/latest_good_backup.db.gz

# 3. Verify restored database
python scripts/inspect_db.py --verify
```

### Performance Issues

If queries are slow:

```bash
# 1. Analyze database
sqlite3 ~/.tprm-frameworks/tprm.db "ANALYZE;"

# 2. Vacuum to optimize
sqlite3 ~/.tprm-frameworks/tprm.db "VACUUM;"

# 3. Check statistics
python scripts/backup_db.py --stats
```

## Best Practices

### Before Major Changes

```bash
# Always backup before:
# - Schema migrations
# - Bulk data imports
# - Software updates
# - Configuration changes

python scripts/backup_db.py --backup --compress --description "before_change"
```

### Regular Maintenance

```bash
# Weekly tasks:
# - Create backup
# - Verify integrity
# - Review statistics
# - Clean old backups

python scripts/backup_db.py --backup --compress
python scripts/inspect_db.py --verify
python scripts/inspect_db.py --stats
python scripts/backup_db.py --cleanup --keep 30
```

### Monitoring

```bash
# Monitor database health:
# - Check size growth
# - Verify no integrity issues
# - Review assessment trends
# - Track vendor count

python scripts/inspect_db.py --stats --json | jq '.database_size_mb'
python scripts/inspect_db.py --verify --json | jq '.healthy'
```

## Security Considerations

### File Permissions

Ensure database and backups have appropriate permissions:

```bash
# Database should be readable/writable by app only
chmod 600 ~/.tprm-frameworks/tprm.db

# Backup directory should be private
chmod 700 ~/.tprm-frameworks/backups
```

### Backup Encryption

For sensitive data, encrypt backups:

```bash
# Backup and encrypt
python scripts/backup_db.py --backup --compress
gpg --encrypt ~/.tprm-frameworks/backups/tprm_backup_*.db.gz

# Decrypt and restore
gpg --decrypt backup.db.gz.gpg > backup.db.gz
python scripts/backup_db.py --restore backup.db.gz
```

### Access Control

Restrict script execution:

```bash
# Scripts should only be runnable by authorized users
chmod 700 scripts/*.py
```

## Support

For issues or questions:

1. Check [PHASE_1_PERSISTENCE.md](../PHASE_1_PERSISTENCE.md) for detailed documentation
2. Review troubleshooting section above
3. Check database integrity: `python scripts/inspect_db.py --verify`
4. Contact support with logs and error messages

## Version History

- **1.0.0** (2026-02-07) - Initial release
  - Migration tool
  - Backup/restore tool
  - Inspection tool
  - Complete documentation
