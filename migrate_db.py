#!/usr/bin/env python3
"""
Simple database migration script to add new columns for file grouping and AI suggestions
"""
import sqlite3
import os

def migrate_database():
    """Add new columns to ai_reports table"""
    db_path = "sonar_advisor.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. It will be created when the app starts.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if new columns already exist
        cursor.execute("PRAGMA table_info(ai_reports)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add grouped_by_file column if it doesn't exist
        if 'grouped_by_file' not in columns:
            print("Adding grouped_by_file column...")
            cursor.execute("ALTER TABLE ai_reports ADD COLUMN grouped_by_file TEXT")
            print("✓ Added grouped_by_file column")
        else:
            print("✓ grouped_by_file column already exists")
        
        # Add issues_with_suggestions column if it doesn't exist
        if 'issues_with_suggestions' not in columns:
            print("Adding issues_with_suggestions column...")
            cursor.execute("ALTER TABLE ai_reports ADD COLUMN issues_with_suggestions TEXT")
            print("✓ Added issues_with_suggestions column")
        else:
            print("✓ issues_with_suggestions column already exists")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()