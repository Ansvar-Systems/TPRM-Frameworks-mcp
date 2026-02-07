# Phase 1: Quick Start Guide

Get started with the TPRM Frameworks MCP persistence layer in 5 minutes.

## Prerequisites

- Phase 0 installed and working
- Python 3.10+ with virtual environment
- Read/write access to `~/.tprm-frameworks/`

## 5-Minute Setup

### Step 1: Initialize Database (1 minute)

```bash
# Navigate to project directory
cd /Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp

# Activate virtual environment (if not already active)
source .venv/bin/activate

# Initialize database schema
python scripts/migrate_db.py --migrate
```

Expected output:
```
Found 1 pending migration(s)
✓ Database backed up to: ~/.tprm-frameworks/backups/tprm_backup_20260207_075721.db
Applying migration 1: Initial schema - questionnaires and assessments
✓ Migration 1 applied successfully

✓ All migrations applied successfully (version 1)
```

### Step 2: Verify Setup (1 minute)

```bash
# Check database was created
python scripts/inspect_db.py --stats

# Verify integrity
python scripts/inspect_db.py --verify
```

Expected output:
```
================================================================================
DATABASE STATISTICS
================================================================================

Path: ~/.tprm-frameworks/tprm.db
Size: 0.06 MB
Schema Version: 1
...
Overall Status: ✓ HEALTHY
```

### Step 3: Create Initial Backup (1 minute)

```bash
# Create compressed backup
python scripts/backup_db.py --backup --compress
```

Expected output:
```
Creating backup: tprm_backup_20260207_080000.db
  Database size: 0.06 MB
  Tables: 5
✓ Backup created: ~/.tprm-frameworks/backups/tprm_backup_20260207_080000.db
✓ Backup compressed: ~/.tprm-frameworks/backups/tprm_backup_20260207_080000.db.gz
```

### Step 4: Test the Server (2 minutes)

```bash
# Start the server (in one terminal)
python -m tprm_frameworks_mcp
```

The server will automatically use the new database. All questionnaires and assessments are now persisted!

## What Just Happened?

You now have:

1. **SQLite Database**: `~/.tprm-frameworks/tprm.db`
   - 5 tables (vendors, questionnaires, assessments, assessment_responses, schema_version)
   - Fully indexed for performance
   - Ready for production use

2. **Backup System**: `~/.tprm-frameworks/backups/`
   - Automatic backups before migrations
   - Manual backup capability
   - Compression support

3. **Management Tools**: `scripts/`
   - Migration tool for schema updates
   - Backup/restore utility
   - Database inspection and verification

## What Changed from Phase 0?

### Before (Phase 0)
```python
# In-memory storage (server.py)
generated_questionnaires: dict[str, Questionnaire] = {}
```
- Data lost on server restart
- No historical tracking
- No vendor comparison

### After (Phase 1)
```python
# Database storage
conn = sqlite3.connect('~/.tprm-frameworks/tprm.db')
```
- Data persists across restarts
- Complete audit trail
- Vendor history and trend analysis
- New tools: `get_vendor_history`, `compare_assessments`

## Quick Testing

### Generate and Persist a Questionnaire

Using MCP tools via your client:

```
Agent: "Generate a CAIQ questionnaire for Salesforce"
→ Tool: generate_questionnaire(framework="caiq_v4", entity_type="saas_provider")
→ Returns: Questionnaire ID (now stored in database)
```

Verify it's in the database:
```bash
python scripts/inspect_db.py --questionnaires
```

### Evaluate and Store an Assessment

```
Agent: "Evaluate Salesforce's responses"
→ Tool: evaluate_response(questionnaire_id="...", vendor_name="Salesforce", responses=[...])
→ Returns: Assessment results (now stored in database)
```

Check the database:
```bash
python scripts/inspect_db.py --vendors
python scripts/inspect_db.py --assessments
```

### View Vendor History

```
Agent: "Show Salesforce's assessment history"
→ Tool: get_vendor_history(vendor_name="Salesforce")
→ Returns: Complete history with trend analysis
```

Or use the CLI:
```bash
python scripts/inspect_db.py --vendor-history "Salesforce"
```

## Daily Operations

### Morning Check
```bash
# Health check
python scripts/inspect_db.py --stats
python scripts/inspect_db.py --verify
```

### Before Important Changes
```bash
# Create backup
python scripts/backup_db.py --backup --compress --description "before_change"
```

### Weekly Maintenance
```bash
# Create backup
python scripts/backup_db.py --backup --compress

# Clean old backups (keep 30 days)
python scripts/backup_db.py --cleanup --keep 30

# Verify integrity
python scripts/inspect_db.py --verify
```

## Common Tasks

### List All Vendors
```bash
python scripts/inspect_db.py --vendors
```

### Show Recent Assessments
```bash
python scripts/inspect_db.py --assessments --limit 10
```

### View Specific Assessment
```bash
python scripts/inspect_db.py --assessment 1
```

### Export Data as JSON
```bash
python scripts/inspect_db.py --stats --json > stats.json
python scripts/inspect_db.py --vendors --json > vendors.json
```

### Restore from Backup
```bash
# List backups
python scripts/backup_db.py --list

# Restore (you'll be prompted for confirmation)
python scripts/backup_db.py --restore ~/.tprm-frameworks/backups/tprm_backup_YYYYMMDD_HHMMSS.db.gz
```

## Troubleshooting

### Server Won't Start
```bash
# Check database exists
ls -la ~/.tprm-frameworks/tprm.db

# Verify integrity
python scripts/inspect_db.py --verify

# Check permissions
chmod 600 ~/.tprm-frameworks/tprm.db
```

### Database Locked
```bash
# Stop server
pkill -f tprm_frameworks_mcp

# Retry operation
python scripts/migrate_db.py --check
```

### Need to Reset Database
```bash
# Backup current database
python scripts/backup_db.py --backup --compress --description "before_reset"

# Remove database
rm ~/.tprm-frameworks/tprm.db

# Reinitialize
python scripts/migrate_db.py --migrate
```

## Next Steps

1. **Read Full Documentation**: [PHASE_1_PERSISTENCE.md](PHASE_1_PERSISTENCE.md)
2. **Set Up Automated Backups**: Add cron job for daily backups
3. **Test New MCP Tools**: Try `get_vendor_history` and `compare_assessments`
4. **Integrate with Workflows**: Use persistence in your TPRM workflows

## Automated Backup Setup

### Linux/macOS (Cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/TPRM-Frameworks-mcp && \
  /path/to/.venv/bin/python scripts/backup_db.py --backup --compress && \
  /path/to/.venv/bin/python scripts/backup_db.py --cleanup --keep 30
```

### Windows (Task Scheduler)

Create a batch file `backup.bat`:
```batch
@echo off
cd C:\path\to\TPRM-Frameworks-mcp
.venv\Scripts\python.exe scripts\backup_db.py --backup --compress
.venv\Scripts\python.exe scripts\backup_db.py --cleanup --keep 30
```

Schedule it via Task Scheduler to run daily.

## Configuration

### Custom Database Location

```bash
# Set environment variable
export DATABASE_PATH=/custom/path/tprm.db

# Or use --db-path flag
python scripts/migrate_db.py --db-path /custom/path/tprm.db --migrate
```

### Custom Backup Location

```bash
# Set environment variable
export BACKUP_DIR=/custom/path/backups

# Or use --backup-dir flag
python scripts/backup_db.py --backup-dir /custom/path/backups --backup
```

## Support

- **Full Documentation**: [PHASE_1_PERSISTENCE.md](PHASE_1_PERSISTENCE.md)
- **Script Reference**: [scripts/README.md](scripts/README.md)
- **General Setup**: [QUICKSTART.md](QUICKSTART.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)

## Summary

Phase 1 persistence is now active:

- ✅ Database initialized with schema v1
- ✅ Backup system configured
- ✅ Management tools ready
- ✅ Integrity verified
- ✅ Server using database for persistence

You can now track vendor assessments over time, compare results, and maintain a complete audit trail.

**Total Setup Time: ~5 minutes**
**Status: Production Ready**
