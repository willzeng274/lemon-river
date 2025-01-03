"""
Database adapter for SQLite persistence
"""

import sqlite3
import logging
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from gui.dataclasses import Application, ApplicationStatus, ApplicationMetadata

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    """SQLite database adapter for job applications"""

    def __init__(self, db_path: str = "applications.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self._ensure_db_directory()
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info("Database initialized at %s", db_path)

    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    role TEXT,
                    company TEXT,
                    location TEXT,
                    duration TEXT,
                    description TEXT,
                    notes TEXT,
                    check_url TEXT,
                    status TEXT,
                    resume_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER,
                    question TEXT,
                    answer TEXT,
                    FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE
                )
            """)

    def add_application(self, application: Application) -> int:
        """Add a new application to the database"""
        if not application.metadata.created_at:
            application.metadata.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.conn:
            cursor = self.conn.execute("""
                INSERT INTO applications (
                    url, role, company, location, duration,
                    description, notes, check_url, status, resume_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application.metadata.url,
                application.metadata.role,
                application.metadata.company,
                application.metadata.location,
                application.metadata.duration,
                application.metadata.description,
                application.metadata.notes,
                application.metadata.check_url,
                application.status.value,
                None,
                application.metadata.created_at
            ))
            
            app_id = cursor.lastrowid

            if application.metadata.questions:
                self.conn.executemany("""
                    INSERT INTO questions (application_id, question, answer)
                    VALUES (?, ?, ?)
                """, [(app_id, q, a) for q, a in application.metadata.questions])
            
            return app_id

    def update_application(self, app_id: int, application: Application) -> bool:
        """Update an existing application without modifying questions"""
        try:
            with self.conn:
                self.conn.execute("""
                    UPDATE applications SET
                        url = ?, role = ?, company = ?, location = ?,
                        duration = ?, description = ?, notes = ?,
                        check_url = ?, status = ?, resume_path = ?, created_at = ?
                    WHERE id = ?
                """, (
                    application.metadata.url,
                    application.metadata.role,
                    application.metadata.company,
                    application.metadata.location,
                    application.metadata.duration,
                    application.metadata.description,
                    application.metadata.notes,
                    application.metadata.check_url,
                    application.status.value,
                    application.metadata.resume_path,
                    application.metadata.created_at,
                    app_id
                ))
                
                return True
        except sqlite3.Error as e:
            logger.error("[DB] Error updating application: %s", str(e))
            return False

    def delete_application(self, app_id: int) -> bool:
        """Delete an application from the database"""
        try:
            with self.conn:
                self.conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
                return True
        except sqlite3.Error as e:
            logger.error("Error deleting application: %s", e)
            return False

    def get_application(self, app_id: int) -> Optional[Application]:
        """Get a single application by ID"""
        try:
            cursor = self.conn.execute("""
                SELECT * FROM applications WHERE id = ?
            """, (app_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            questions_cursor = self.conn.execute("""
                SELECT id, question, answer
                FROM questions
                WHERE application_id = ?
                ORDER BY id
            """, (app_id,))
            questions = [(row[0], row[1], row[2]) for row in questions_cursor.fetchall()]
            
            application = self._row_to_application(row, questions)
            return application
        except sqlite3.Error as e:
            logger.error("[DB] Error getting application: %s", str(e))
            return None

    def get_all_applications(self) -> List[Application]:
        """Get all applications from the database"""
        try:
            applications = []
            cursor = self.conn.execute("SELECT * FROM applications ORDER BY created_at DESC")
            
            for row in cursor.fetchall():
                app_id = row['id']
                questions_cursor = self.conn.execute("""
                    SELECT id, question, answer
                    FROM questions
                    WHERE application_id = ?
                    ORDER BY id
                """, (app_id,))
                questions = [(row[0], row[1], row[2]) for row in questions_cursor.fetchall()]
                
                application = self._row_to_application(row, questions)
                applications.append(application)
            
            return applications
        except sqlite3.Error as e:
            logger.error("Error getting applications: %s", e)
            return []

    def get_question(self, question_id: int) -> Optional[Tuple[int, str, str]]:
        """Get a question by its ID"""
        try:
            cursor = self.conn.execute("""
                SELECT id, application_id, question, answer
                FROM questions
                WHERE id = ?
            """, (question_id,))
            
            row = cursor.fetchone()
            if row:
                return (row[0], row[2], row[3])  # id, question, answer
            return None
        except sqlite3.Error as e:
            logger.error("[DB] Error getting question: %s", str(e))
            return None

    def get_questions_for_application(self, app_id: int) -> List[Tuple[int, str, str]]:
        """Get all questions for an application with their IDs"""
        try:
            cursor = self.conn.execute("""
                SELECT id, question, answer
                FROM questions
                WHERE application_id = ?
                ORDER BY id
            """, (app_id,))
            
            questions = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
            return questions
        except sqlite3.Error as e:
            logger.error("[DB] Error getting questions: %s", str(e))
            return []

    def add_question(self, app_id: int, question: str, answer: str) -> int:
        """Add a new question to an application"""
        try:
            with self.conn:
                cursor = self.conn.execute("""
                    INSERT INTO questions (application_id, question, answer)
                    VALUES (?, ?, ?)
                """, (app_id, question, answer))
                
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("[DB] Error adding question: %s", str(e))
            return -1

    def update_question(self, question_id: int, question: str, answer: str) -> bool:
        """Update an existing question"""
        try:
            logger.info("[DB] Updating question ID %d: Q='%s', A='%s'", 
                       question_id, question[:50], answer[:50])
            with self.conn:
                self.conn.execute("""
                    UPDATE questions
                    SET question = ?, answer = ?
                    WHERE id = ?
                """, (question, answer, question_id))
                
                return True
        except sqlite3.Error as e:
            logger.error("[DB] Error updating question: %s", str(e))
            return False

    def delete_question(self, question_id: int) -> bool:
        """Delete a question by its ID"""
        try:
            with self.conn:
                self.conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
                return True
        except sqlite3.Error as e:
            logger.error("[DB] Error deleting question: %s", str(e))
            return False

    def _row_to_application(self, row: sqlite3.Row, questions: List[tuple]) -> Application:
        """Convert a database row to an Application object"""
        metadata = ApplicationMetadata(
            url=row['url'],
            company=row['company'],
            role=row['role'],
            location=row['location'],
            duration=row['duration'],
            description=row['description'],
            notes=row['notes'],
            check_url=row['check_url'],
            resume_path=row['resume_path'],
            created_at=row['created_at'],
            questions=[]
        )

        metadata.questions = [(q[1], q[2]) for q in questions]
        metadata.question_ids = {i: q[0] for i, q in enumerate(questions)}
        
        return Application(
            metadata=metadata,
            status=ApplicationStatus(row['status']),
            id=row['id']
        )

    def close(self):
        """Close the database connection"""
        self.conn.close()
