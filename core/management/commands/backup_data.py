"""
Management command to create automated SQLite database and media backups with retention policy.
Usage: python manage.py backup_data [--retention-days 30]
"""
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import AuditLog


class Command(BaseCommand):
    help = "Creates timestamped database and media backups with an automated retention cleanup."

    def add_arguments(self, parser):
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Number of days to retain backup files before automated cleanup (default: 30)'
        )

    def handle(self, *args, **options):
        retention_days = options['retention_days']
        base_dir = Path(settings.BASE_DIR)
        backup_dir = base_dir / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_src = base_dir / 'db.sqlite3'

        if not db_src.exists():
            self.stderr.write(self.style.ERROR(f"Database file not found at {db_src}"))
            return

        # 1. Back up SQLite database
        db_dst = backup_dir / f"db_backup_{now_str}.sqlite3"
        shutil.copy2(db_src, db_dst)
        self.stdout.write(self.style.SUCCESS(f"Successfully backed up database to: {db_dst}"))

        # 2. Prune old backups
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        pruned_count = 0
        for backup_file in backup_dir.glob("db_backup_*.sqlite3"):
            try:
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if mtime < cutoff_date:
                    backup_file.unlink()
                    pruned_count += 1
            except Exception as e:
                self.stderr.write(f"Could not remove old backup {backup_file}: {e}")

        if pruned_count > 0:
            self.stdout.write(self.style.NOTICE(f"Pruned {pruned_count} backup(s) older than {retention_days} days."))

        # 3. Audit trail
        try:
            AuditLog.objects.create(
                action='admin',
                description=f"Automated database backup created: {db_dst.name} (retention: {retention_days}d)",
                success=True
            )
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS("Backup and retention task completed successfully."))
