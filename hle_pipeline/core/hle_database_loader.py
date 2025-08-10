#!/usr/bin/env python3
"""
HLE Database Loader
Integrates HLE dataset with SQLite database for efficient storage and retrieval.
"""

import os
import requests
import pandas as pd
from typing import Dict, List, Optional
from core.database_manager import DatabaseManager

class HLEDatabaseLoader:
    def __init__(self, db_path: str = "data/hle_quiz.db"):
        self.db_manager = DatabaseManager(db_path)
        self.dataset_url = "https://huggingface.co/api/datasets/cais/hle/parquet/default/test"
        # Authentication for Hugging Face is handled via the HF_TOKEN environment variable.
    
    def load_dataset_to_db(self, force_refresh: bool = False) -> bool:
        """Load HLE dataset into the database"""
        try:
            # Check if database already has data
            stats = self.db_manager.get_stats()
            if stats['total_questions'] > 0 and not force_refresh:
                print(f"✅ Database already contains {stats['total_questions']} questions")
                return True
            
            print("📥 Loading HLE dataset into database...")
            
            # Use Hugging Face datasets library
            from datasets import load_dataset
            
            # Load the dataset
            dataset = load_dataset("cais/hle", split="test")
            print(f"📊 Loaded {len(dataset)} questions from HLE dataset")
            
            # Convert to question format
            questions = []
            for item in dataset:
                question = {
                    'id': str(item.get('id', '')),
                    'question': str(item.get('question', '')),
                    'answer': str(item.get('answer', '')),
                    'subject': str(item.get('category', 'Other')),
                    'raw_subject': str(item.get('raw_subject', '')),
                    'difficulty': 'Intermediate',  # HLE dataset doesn't have difficulty
                    'explanation': str(item.get('rationale', 'No explanation available.')),
                    'question_type': 'text',
                    'image': str(item.get('image', ''))
                }
                questions.append(question)
            
            # Insert into database
            inserted = self.db_manager.insert_questions(questions)
            print(f"✅ Inserted {inserted} questions into database")
            
            print(f"🎉 Successfully loaded {inserted} questions into database")
            return True
            
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return False
    
    def get_random_questions(self, num_questions: int = 5, 
                           subject: Optional[str] = None, 
                           difficulty: Optional[str] = None,
                           question_type: Optional[str] = None) -> List[Dict]:
        """Get random questions from database"""
        return self.db_manager.get_random_questions(num_questions, subject, difficulty, question_type)
    
    def get_subjects(self) -> List[str]:
        """Get available subjects from database"""
        return self.db_manager.get_subjects()
    
    def get_difficulties(self) -> List[str]:
        """Get available difficulties from database"""
        return self.db_manager.get_difficulties()
    
    def get_question_types(self) -> List[str]:
        """Get available question types from database"""
        return self.db_manager.get_question_types()
    
    def get_raw_subjects(self) -> List[str]:
        """Get available raw subjects from database"""
        return self.db_manager.get_raw_subjects()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return self.db_manager.get_stats()
    
    def save_user_result(self, user_id: str, result: Dict) -> int:
        """Save user quiz result"""
        return self.db_manager.save_user_result(user_id, result)
    
    def get_user_results(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's quiz results"""
        return self.db_manager.get_user_results(user_id, limit)
    
    def get_analytics(self) -> Dict:
        """Get comprehensive analytics"""
        return self.db_manager.get_analytics()
    
    def get_database_info(self) -> Dict:
        """Get database information"""
        stats = self.db_manager.get_stats()
        return {
            "database_size": self.db_manager.get_database_size(),
            "total_questions": stats['total_questions'],
            "subjects": len(stats['subjects']),
            "difficulties": len(stats['difficulties']),
            "question_types": len(stats['question_types']),
            "raw_subjects": len(stats['raw_subjects'])
        }

# Example usage
if __name__ == "__main__":
    loader = HLEDatabaseLoader()
    
    # Load dataset into database
    success = loader.load_dataset_to_db()
    
    if success:
        # Get database info
        info = loader.get_database_info()
        print(f"Database Info: {info}")
        
        # Test getting questions
        questions = loader.get_random_questions(3, subject="Physics")
        print(f"Sample Physics questions: {len(questions)}")
        
        # Get stats
        stats = loader.get_stats()
        print(f"Subjects available: {stats['subjects']}")
    else:
        print("Failed to load dataset")
