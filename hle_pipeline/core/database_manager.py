#!/usr/bin/env python3
"""
Database Manager for HLE Quiz App
Handles SQLite database operations for efficient question storage and retrieval.
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
try:
    import pandas as pd  # optional; not required for DB operations
except Exception:
    pd = None

class DatabaseManager:
    def __init__(self, db_path: str = "data/hle_quiz.db"):
        self.db_path = db_path
        # Ensure parent directory exists (e.g., data/)
        parent_dir = os.path.dirname(self.db_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with proper tables and indexes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    raw_subject TEXT,
                    difficulty TEXT,
                    explanation TEXT,
                    question_type TEXT,
                    image TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create user_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds REAL,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    accuracy_percentage REAL,
                    subject TEXT,
                    difficulty TEXT,
                    detailed_results TEXT
                )
            """)
            
            # Create indexes for fast querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subject ON questions(subject)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_difficulty ON questions(difficulty)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_question_type ON questions(question_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_subject ON questions(raw_subject)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_results_timestamp ON user_results(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_results_user_id ON user_results(user_id)")
            
            conn.commit()
    
    def insert_questions(self, questions: List[Dict]) -> int:
        """Insert questions into the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Prepare data for insertion
            data = []
            for q in questions:
                data.append((
                    q.get('id', ''),
                    q.get('question', ''),
                    q.get('answer', ''),
                    q.get('subject', 'Other'),
                    q.get('raw_subject', ''),
                    q.get('difficulty', 'Intermediate'),
                    q.get('explanation', ''),
                    q.get('question_type', 'text'),
                    q.get('image', '')
                ))
            
            # Insert with conflict resolution (ignore duplicates)
            cursor.executemany("""
                INSERT OR IGNORE INTO questions 
                (id, question, answer, subject, raw_subject, difficulty, explanation, question_type, image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            return cursor.rowcount
    
    def get_random_questions(self, num_questions: int = 5, 
                           subject: Optional[str] = None, 
                           difficulty: Optional[str] = None,
                           question_type: Optional[str] = None) -> List[Dict]:
        """Get random questions with optional filtering"""
        query = "SELECT * FROM questions WHERE 1=1"
        params = []
        
        if subject and subject != "All":
            query += " AND subject = ?"
            params.append(subject)
        
        if difficulty and difficulty != "All":
            query += " AND difficulty = ?"
            params.append(difficulty)
        
        if question_type and question_type != "All":
            query += " AND question_type = ?"
            params.append(question_type)
        
        query += f" ORDER BY RANDOM() LIMIT {num_questions}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]

    def get_adaptive_question(self,
                              exclude_ids: Optional[List[str]] = None,
                              subject: Optional[str] = None,
                              difficulty: Optional[str] = None,
                              question_type: Optional[str] = None,
                              difficulty_bin: Optional[str] = None) -> Optional[Dict]:
        """
        Select a single question while excluding a provided set of IDs and optionally
        steering toward a target difficulty bin using a proxy based on question length.

        difficulty_bin values: 'easy' (short), 'medium' (mid), 'hard' (long).
        """
        base_query = ["SELECT * FROM questions WHERE 1=1"]
        params: List = []

        if subject and subject != "All":
            base_query.append("AND subject = ?")
            params.append(subject)

        # The dataset's difficulty is mostly 'Intermediate'; keep for forward-compat
        if difficulty and difficulty != "All":
            base_query.append("AND difficulty = ?")
            params.append(difficulty)

        if question_type and question_type != "All":
            base_query.append("AND question_type = ?")
            params.append(question_type)

        # Exclude already served question IDs
        if exclude_ids:
            # Build placeholders (?, ?, ...)
            placeholders = ",".join(["?"] * len(exclude_ids))
            base_query.append(f"AND id NOT IN ({placeholders})")
            params.extend(exclude_ids)

        # Apply length-based difficulty proxy if requested
        # easy: LENGTH(question) < 120
        # medium: 120 <= LENGTH(question) <= 240
        # hard: LENGTH(question) > 240
        if difficulty_bin == "easy":
            base_query.append("AND LENGTH(question) < 120")
        elif difficulty_bin == "medium":
            base_query.append("AND LENGTH(question) BETWEEN 120 AND 240")
        elif difficulty_bin == "hard":
            base_query.append("AND LENGTH(question) > 240")

        base_query.append("ORDER BY RANDOM() LIMIT 1")
        query = " ".join(base_query)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_subjects(self) -> List[str]:
        """Get list of available subjects"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT subject FROM questions ORDER BY subject")
            return [row[0] for row in cursor.fetchall()]
    
    def get_difficulties(self) -> List[str]:
        """Get list of available difficulties"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT difficulty FROM questions ORDER BY difficulty")
            return [row[0] for row in cursor.fetchall()]
    
    def get_question_types(self) -> List[str]:
        """Get list of available question types"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT question_type FROM questions ORDER BY question_type")
            return [row[0] for row in cursor.fetchall()]
    
    def get_raw_subjects(self) -> List[str]:
        """Get list of available raw subjects"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT raw_subject FROM questions WHERE raw_subject != '' ORDER BY raw_subject")
            return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total questions
            cursor.execute("SELECT COUNT(*) FROM questions")
            total_questions = cursor.fetchone()[0]
            
            # Subject counts
            cursor.execute("""
                SELECT subject, COUNT(*) as count 
                FROM questions 
                GROUP BY subject 
                ORDER BY count DESC
            """)
            subject_counts = dict(cursor.fetchall())
            
            # Difficulty counts
            cursor.execute("""
                SELECT difficulty, COUNT(*) as count 
                FROM questions 
                GROUP BY difficulty 
                ORDER BY count DESC
            """)
            difficulty_counts = dict(cursor.fetchall())
            
            # Question type counts
            cursor.execute("""
                SELECT question_type, COUNT(*) as count 
                FROM questions 
                GROUP BY question_type 
                ORDER BY count DESC
            """)
            question_type_counts = dict(cursor.fetchall())
            
            # Raw subject counts (top 20)
            cursor.execute("""
                SELECT raw_subject, COUNT(*) as count 
                FROM questions 
                WHERE raw_subject != ''
                GROUP BY raw_subject 
                ORDER BY count DESC 
                LIMIT 20
            """)
            raw_subject_counts = dict(cursor.fetchall())
            
            return {
                "total_questions": total_questions,
                "subjects": list(subject_counts.keys()),
                "difficulties": list(difficulty_counts.keys()),
                "question_types": list(question_type_counts.keys()),
                "raw_subjects": list(raw_subject_counts.keys()),
                "subject_counts": subject_counts,
                "difficulty_counts": difficulty_counts,
                "question_type_counts": question_type_counts,
                "raw_subject_counts": raw_subject_counts
            }
    
    def save_user_result(self, user_id: str, result: Dict) -> int:
        """Save user quiz result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_results 
                (user_id, duration_seconds, total_questions, correct_answers, 
                 accuracy_percentage, subject, difficulty, detailed_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                result.get('duration_seconds', 0),
                result.get('total_questions', 0),
                result.get('correct_answers', 0),
                result.get('accuracy_percentage', 0),
                result.get('subject', 'All'),
                result.get('difficulty', 'All'),
                json.dumps(result.get('detailed_results', []))
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_user_results(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's quiz results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_results 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['detailed_results'] = json.loads(result['detailed_results'])
                results.append(result)
            
            return results
    
    def get_analytics(self) -> Dict:
        """Get comprehensive analytics data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total results
            cursor.execute("SELECT COUNT(*) FROM user_results")
            total_results = cursor.fetchone()[0]
            
            # Average accuracy
            cursor.execute("SELECT AVG(accuracy_percentage) FROM user_results")
            avg_accuracy = cursor.fetchone()[0] or 0
            
            # Average duration
            cursor.execute("SELECT AVG(duration_seconds) FROM user_results")
            avg_duration = cursor.fetchone()[0] or 0
            
            # Results by subject
            cursor.execute("""
                SELECT subject, COUNT(*) as count, AVG(accuracy_percentage) as avg_acc
                FROM user_results 
                GROUP BY subject 
                ORDER BY count DESC
            """)
            subject_analytics = cursor.fetchall()
            
            # Results by difficulty
            cursor.execute("""
                SELECT difficulty, COUNT(*) as count, AVG(accuracy_percentage) as avg_acc
                FROM user_results 
                GROUP BY difficulty 
                ORDER BY count DESC
            """)
            difficulty_analytics = cursor.fetchall()
            
            return {
                "total_results": total_results,
                "average_accuracy": round(avg_accuracy, 2),
                "average_duration": round(avg_duration, 2),
                "subject_analytics": subject_analytics,
                "difficulty_analytics": difficulty_analytics
            }
    
    def clear_database(self):
        """Clear all data from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM questions")
            cursor.execute("DELETE FROM user_results")
            conn.commit()
    
    def get_database_size(self) -> str:
        """Get database file size"""
        if os.path.exists(self.db_path):
            size_bytes = os.path.getsize(self.db_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        return "0 B"

# Example usage
if __name__ == "__main__":
    db = DatabaseManager()
    print(f"Database initialized: {db.db_path}")
    print(f"Database size: {db.get_database_size()}")
    
    # Test stats
    stats = db.get_stats()
    print(f"Total questions: {stats['total_questions']}")
    print(f"Subjects: {stats['subjects']}")
