#!/usr/bin/env python3
"""Database backup and restore utility for TPRM Frameworks MCP.

This script provides backup and restore functionality for the TPRM database:
- Create timestamped backups with optional compression
- Restore from backup
- List available backups
- Auto-cleanup old backups

Usage:
    python scripts/backup_db.py --backup                    # Create backup
    python scripts/backup_db.py --backup --compress         # Create compressed backup
    python scripts/backup_db.py --restore <backup_file>     # Restore from backup
    python scripts/backup_db.py --list                      # List available backups
    python scripts/backup_db.py --cleanup --keep 10         # Keep only 10 most recent
"""

import argparse
import gzip
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Default paths
DEFAULT_DB_PATH = Path.home() / ".tprm-frameworks" / "tprm.db"
DEFAULT_BACKUP_DIR = Path.home() / ".tprm-frameworks" / "backups"


class BackupManager:
    """Manages database backups."""

    def __init__(self, db_path: Path, backup_dir: Path):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, compress: bool = False, description: str = None) -> Path:
        """Create a database backup."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"tprm_backup_{timestamp}"

        if description:
            # Sanitize description for filename
            safe_desc = "".join(c for c in description if c.isalnum() or c in ("-", "_"))
            backup_name += f"_{safe_desc}"

        backup_name += ".db"
        backup_path = self.backup_dir / backup_name

        print(f"Creating backup: {backup_name}")

        # Get database stats before backup
        stats = self.get_database_stats()
        print(f"  Database size: {stats['size_mb']:.2f} MB")
        print(f"  Tables: {stats['table_count']}")

        # Create backup using SQLite backup API (handles locks properly)
        try:
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)

            with backup_conn:
                source_conn.backup(backup_conn)

            source_conn.close()
            backup_conn.close()

            print(f"✓ Backup created: {backup_path}")

            # Compress if requested
            if compress:
                compressed_path = self.compress_backup(backup_path)
                backup_path.unlink()  # Remove uncompressed version
                backup_path = compressed_path
                print(f"✓ Backup compressed: {compressed_path}")

            return backup_path

        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()
            raise Exception(f"Backup failed: {e}")

    def compress_backup(self, backup_path: Path) -> Path:
        """Compress a backup file using gzip."""
        compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")

        with open(backup_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb", compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        original_size = backup_path.stat().st_size
        compressed_size = compressed_path.stat().st_size
        ratio = (1 - compressed_size / original_size) * 100

        print(f"  Compression: {original_size:,} → {compressed_size:,} bytes ({ratio:.1f}% saved)")

        return compressed_path

    def restore_backup(self, backup_path: Path, force: bool = False) -> bool:
        """Restore database from backup."""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Check if database exists
        if self.db_path.exists() and not force:
            print(f"⚠️  Database already exists: {self.db_path}")
            response = input("Overwrite existing database? [y/N]: ")
            if response.lower() != "y":
                print("Restore cancelled")
                return False

        # Create backup of current database before restore
        if self.db_path.exists():
            pre_restore_backup = self.db_path.parent / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(self.db_path, pre_restore_backup)
            print(f"✓ Current database backed up to: {pre_restore_backup}")

        print(f"Restoring from: {backup_path}")

        try:
            # Decompress if needed
            if backup_path.suffix == ".gz":
                print("  Decompressing backup...")
                temp_path = self.backup_dir / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

                with gzip.open(backup_path, "rb") as f_in:
                    with open(temp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                source_path = temp_path
            else:
                source_path = backup_path

            # Verify backup is valid SQLite database
            conn = sqlite3.connect(source_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            conn.close()

            # Restore database
            shutil.copy2(source_path, self.db_path)

            # Clean up temp file if created
            if source_path != backup_path:
                source_path.unlink()

            # Verify restored database
            stats = self.get_database_stats()
            print(f"✓ Database restored successfully")
            print(f"  Tables: {stats['table_count']}")
            print(f"  Size: {stats['size_mb']:.2f} MB")

            return True

        except Exception as e:
            print(f"✗ Restore failed: {e}")
            return False

    def list_backups(self, detailed: bool = False) -> List[Tuple[Path, dict]]:
        """List available backups."""
        backups = []

        # Find all backup files
        for pattern in ["tprm_backup_*.db", "tprm_backup_*.db.gz"]:
            for backup_file in sorted(self.backup_dir.glob(pattern), reverse=True):
                info = {
                    "name": backup_file.name,
                    "size": backup_file.stat().st_size,
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                    "compressed": backup_file.suffix == ".gz",
                }

                # Get additional details if requested
                if detailed and not info["compressed"]:
                    try:
                        conn = sqlite3.connect(backup_file)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                        info["table_count"] = cursor.fetchone()[0]
                        conn.close()
                    except Exception:
                        info["table_count"] = "N/A"

                backups.append((backup_file, info))

        return backups

    def cleanup_old_backups(self, keep: int = 10) -> int:
        """Remove old backups, keeping only the N most recent."""
        backups = self.list_backups()

        if len(backups) <= keep:
            print(f"Only {len(backups)} backup(s) found, nothing to clean up")
            return 0

        to_remove = backups[keep:]
        print(f"Removing {len(to_remove)} old backup(s), keeping {keep} most recent")

        removed = 0
        for backup_path, info in to_remove:
            try:
                backup_path.unlink()
                print(f"  Removed: {info['name']}")
                removed += 1
            except Exception as e:
                print(f"  Failed to remove {info['name']}: {e}")

        print(f"✓ Cleaned up {removed} old backup(s)")
        return removed

    def get_database_stats(self) -> dict:
        """Get statistics about the database."""
        if not self.db_path.exists():
            return {"size_mb": 0, "table_count": 0}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

        # Get database size
        size_bytes = self.db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        # Get row counts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_version'")
        tables = cursor.fetchall()

        row_counts = {}
        for (table_name,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_counts[table_name] = cursor.fetchone()[0]
            except Exception:
                row_counts[table_name] = "N/A"

        conn.close()

        return {
            "size_mb": size_mb,
            "size_bytes": size_bytes,
            "table_count": table_count,
            "row_counts": row_counts,
        }


def format_size(bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database backup and restore utility")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH),
        help=f"Path to database file (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Path to backup directory (default: {DEFAULT_BACKUP_DIR})",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", action="store_true", help="Create a backup")
    group.add_argument("--restore", type=Path, help="Restore from backup file")
    group.add_argument("--list", action="store_true", help="List available backups")
    group.add_argument("--cleanup", action="store_true", help="Clean up old backups")
    group.add_argument("--stats", action="store_true", help="Show database statistics")

    parser.add_argument("--compress", action="store_true", help="Compress backup with gzip")
    parser.add_argument(
        "--description", type=str, help="Description to include in backup filename"
    )
    parser.add_argument("--force", action="store_true", help="Force restore without confirmation")
    parser.add_argument("--keep", type=int, default=10, help="Number of backups to keep (for cleanup)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed backup information")

    args = parser.parse_args()

    manager = BackupManager(args.db_path, args.backup_dir)

    try:
        if args.backup:
            backup_path = manager.create_backup(
                compress=args.compress, description=args.description
            )
            print(f"\n✓ Backup complete: {backup_path}")
            return 0

        elif args.restore:
            success = manager.restore_backup(args.restore, force=args.force)
            return 0 if success else 1

        elif args.list:
            backups = manager.list_backups(detailed=args.detailed)

            if not backups:
                print("No backups found")
                return 0

            print(f"\nAvailable backups ({len(backups)}):")
            print("-" * 80)

            for backup_path, info in backups:
                compressed = " [COMPRESSED]" if info["compressed"] else ""
                print(f"\n{info['name']}{compressed}")
                print(f"  Created: {info['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Size: {format_size(info['size'])}")
                if args.detailed and "table_count" in info:
                    print(f"  Tables: {info['table_count']}")
                print(f"  Path: {backup_path}")

            print("-" * 80)
            return 0

        elif args.cleanup:
            manager.cleanup_old_backups(keep=args.keep)
            return 0

        elif args.stats:
            stats = manager.get_database_stats()
            print("\nDatabase Statistics:")
            print("-" * 80)
            print(f"Path: {args.db_path}")
            print(f"Size: {stats['size_mb']:.2f} MB ({stats['size_bytes']:,} bytes)")
            print(f"Tables: {stats['table_count']}")

            if stats["row_counts"]:
                print("\nRow Counts:")
                for table, count in stats["row_counts"].items():
                    print(f"  {table}: {count:,}" if isinstance(count, int) else f"  {table}: {count}")

            print("-" * 80)
            return 0

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
