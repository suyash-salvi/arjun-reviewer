"""
Database Manager for Arjun Code Review Tool
Handles SQLite operations for storing and retrieving code review issues
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path: str = "arjun_reviews.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table to store file information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                first_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_count INTEGER DEFAULT 1
            )
        ''')
        
        # Table to store issues
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                issue_hash TEXT NOT NULL UNIQUE,
                severity TEXT NOT NULL,
                issue_line INTEGER,
                issue_type TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                issue_solution TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                user_acknowledged INTEGER DEFAULT 0,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        # Table to track scan history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                new_issues_count INTEGER DEFAULT 0,
                existing_issues_count INTEGER DEFAULT 0,
                resolved_issues_count INTEGER DEFAULT 0,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def compute_file_hash(self, content: str) -> str:
        """Compute SHA256 hash of normalized file content."""
        normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
        normalized_lines = [line.rstrip() for line in normalized_content.split('\n')]
        normalized_content = '\n'.join(normalized_lines).strip()
        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    def compute_issue_hash(self, filename: str, issue_type: str, issue_line: int, issue_description: str) -> str:
        """Compute a unique hash for an issue based on its characteristics."""
        issue_str = f"{filename}:{issue_type}:{issue_line}:{issue_description}"
        return hashlib.sha256(issue_str.encode('utf-8')).hexdigest()

    def get_file_by_name(self, filename: str) -> Optional[Dict]:
        """Get file metadata by filename."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM files WHERE filename = ?', (filename,))
        row = cursor.fetchone()

        conn.close()
        return dict(row) if row else None
    
    def get_or_create_file(self, filename: str, file_hash: str) -> Tuple[int, bool]:
        """
        Get existing file record or create new one.
        Returns: (file_id, is_new_file)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if file with same name exists
        cursor.execute('SELECT id, file_hash FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        
        if result:
            file_id = result['id']
            # Update last scanned timestamp and increment count
            cursor.execute('''
                UPDATE files 
                SET last_scanned_at = CURRENT_TIMESTAMP, 
                    scan_count = scan_count + 1,
                    file_hash = ?
                WHERE id = ?
            ''', (file_hash, file_id))
            conn.commit()
            conn.close()
            return file_id, False
        else:
            # Create new file record
            cursor.execute('''
                INSERT INTO files (filename, file_hash) 
                VALUES (?, ?)
            ''', (filename, file_hash))
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return file_id, True
    
    def get_existing_issues(self, file_id: int) -> List[Dict]:
        """Get all open issues for a file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM issues 
            WHERE file_id = ? AND status = 'open'
            ORDER BY severity DESC, issue_line ASC
        ''', (file_id,))
        
        issues = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return issues
    
    def get_all_issues_for_file(self, file_id: int) -> List[Dict]:
        """Get all issues (open and resolved) for a file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM issues 
            WHERE file_id = ?
            ORDER BY status ASC, severity DESC, issue_line ASC
        ''', (file_id,))
        
        issues = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return issues
    
    def add_issue(self, file_id: int, filename: str, issue: Dict) -> Tuple[int, bool]:
        """
        Add a new issue or return existing one.
        Returns: (issue_id, is_new)
        """
        issue_hash = self.compute_issue_hash(
            filename,
            issue['issue_type'],
            issue.get('issue_line', 0),
            issue['issue_description']
        )
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if issue already exists
        cursor.execute('SELECT id, status FROM issues WHERE issue_hash = ?', (issue_hash,))
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return result['id'], False
        
        # Insert new issue
        cursor.execute('''
            INSERT INTO issues (file_id, issue_hash, severity, issue_line, issue_type, 
                              issue_description, issue_solution, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
        ''', (
            file_id,
            issue_hash,
            issue['severity'],
            issue.get('issue_line', 0),
            issue['issue_type'],
            issue['issue_description'],
            issue['issue_solution']
        ))
        
        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return issue_id, True
    
    def mark_issue_resolved(self, issue_id: int):
        """Mark an issue as resolved."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE issues 
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (issue_id,))
        
        conn.commit()
        conn.close()

    def mark_issues_resolved(self, issue_ids: List[int]):
        """Mark multiple issues as resolved by their IDs."""
        if not issue_ids:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        placeholders = ','.join(['?' for _ in issue_ids])
        cursor.execute(f'''
            UPDATE issues
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders}) AND status = 'open'
        ''', issue_ids)

        conn.commit()
        conn.close()
    
    def mark_issues_resolved_by_hash(self, issue_hashes: List[str]):
        """Mark multiple issues as resolved by their hashes."""
        if not issue_hashes:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in issue_hashes])
        cursor.execute(f'''
            UPDATE issues 
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE issue_hash IN ({placeholders}) AND status = 'open'
        ''', issue_hashes)
        
        conn.commit()
        conn.close()
    
    def acknowledge_issue(self, issue_id: int):
        """Mark an issue as acknowledged by the user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE issues 
            SET user_acknowledged = 1
            WHERE id = ?
        ''', (issue_id,))
        
        conn.commit()
        conn.close()

    def update_issue(self, issue_id: int, issue: Dict):
        """Update core fields of an existing issue (e.g., line shift after reupload)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE issues
            SET severity = ?,
                issue_line = ?,
                issue_type = ?,
                issue_description = ?,
                issue_solution = ?
            WHERE id = ?
        ''', (
            issue['severity'],
            issue.get('issue_line', 0),
            issue['issue_type'],
            issue['issue_description'],
            issue['issue_solution'],
            issue_id
        ))

        conn.commit()
        conn.close()
    
    def record_scan_history(self, file_id: int, file_hash: str, 
                           new_count: int, existing_count: int, resolved_count: int):
        """Record scan history for analytics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scan_history (file_id, file_hash, new_issues_count, 
                                     existing_issues_count, resolved_issues_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_id, file_hash, new_count, existing_count, resolved_count))
        
        conn.commit()
        conn.close()
    
    def get_acceptance_ratio(self, file_id: Optional[int] = None) -> Dict:
        """
        Calculate user acceptance ratio.
        Returns ratio of acknowledged issues to total existing issues.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if file_id:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN user_acknowledged = 1 THEN 1 ELSE 0 END) as acknowledged_issues,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_issues,
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_issues
                FROM issues 
                WHERE file_id = ?
            ''', (file_id,))
        else:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN user_acknowledged = 1 THEN 1 ELSE 0 END) as acknowledged_issues,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_issues,
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_issues
                FROM issues
            ''')
        
        result = cursor.fetchone()
        conn.close()
        
        total = result['total_issues'] or 0
        acknowledged = result['acknowledged_issues'] or 0
        resolved = result['resolved_issues'] or 0
        open_issues = result['open_issues'] or 0
        
        acceptance_ratio = (acknowledged / open_issues * 100) if open_issues > 0 else 100
        resolution_ratio = (resolved / total * 100) if total > 0 else 0
        
        return {
            'total_issues': total,
            'acknowledged_issues': acknowledged,
            'resolved_issues': resolved,
            'open_issues': open_issues,
            'acceptance_ratio': round(acceptance_ratio, 2),
            'resolution_ratio': round(resolution_ratio, 2)
        }
    
    def get_file_history(self, filename: str) -> List[Dict]:
        """Get scan history for a specific file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sh.*, f.filename
            FROM scan_history sh
            JOIN files f ON sh.file_id = f.id
            WHERE f.filename = ?
            ORDER BY sh.scanned_at DESC
        ''', (filename,))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    
    def get_resolved_issues(self, file_id: int) -> List[Dict]:
        """Get all resolved issues for a file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM issues 
            WHERE file_id = ? AND status = 'resolved'
            ORDER BY resolved_at DESC
        ''', (file_id,))
        
        issues = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return issues
