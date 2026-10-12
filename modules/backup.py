import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any
from modules.database import DB_PATH

class BackupManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.backup_dir = "data/backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> str:
        """Creates a full backup of the SQLite database."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"alorEx_leads_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        # Safe SQLite backup using the backup API if available, otherwise simple copy
        try:
            src = sqlite3.connect(self.db_path)
            dst = sqlite3.connect(backup_path)
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
        except Exception as e:
            # Fallback to shutil copy
            shutil.copy2(self.db_path, backup_path)

        return backup_path

    def list_backups(self) -> List[Dict[str, Any]]:
        """Lists all available backups in the backup directory."""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db'):
                path = os.path.join(self.backup_dir, filename)
                stats = os.stat(path)
                backups.append({
                    "filename": filename,
                    "size": stats.st_size,
                    "created": datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    "path": path
                })
        # Sort by creation date descending
        return sorted(backups, key=lambda x: x['created'], reverse=True)

    def restore_backup(self, backup_path: str) -> bool:
        """Restores the database from a backup file."""
        if not os.path.exists(backup_path):
            return False

        # 1. Create a safety backup of the current DB
        self.create_backup()

        # 2. Restore
        try:
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception:
            return False
