#!/usr/bin/env python3
"""
Database migration script to remove enhanced columns from ai_reports table.
This reverts the database structure to the original version.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sonar_advisor.core.database import engine, get_db

def remove_enhanced_columns():
    """Remove the enhanced columns from ai_reports table."""
    
    try:
        with engine.connect() as connection:
            # Clean up any existing temporary table first
            try:
                connection.execute(text("DROP TABLE IF EXISTS ai_reports_new"))
                print("🧹 Cleaned up existing temporary table")
            except:
                pass
            
            # For SQLite, check if columns exist using PRAGMA table_info
            result = connection.execute(text("PRAGMA table_info(ai_reports)"))
            existing_columns = [row[1] for row in result.fetchall()]  # row[1] is the column name
            
            print(f"Current columns in ai_reports: {existing_columns}")
            
            # SQLite doesn't support DROP COLUMN until version 3.35.0
            # We need to recreate the table without the enhanced columns
            if 'grouped_by_file' in existing_columns or 'issues_with_suggestions' in existing_columns:
                print("Recreating ai_reports table without enhanced columns...")
                
                # Create a backup table with original structure (matching actual current schema minus enhanced columns)
                connection.execute(text("""
                    CREATE TABLE ai_reports_new (
                        id INTEGER PRIMARY KEY,
                        analysis_request_id INTEGER NOT NULL,
                        summary TEXT,
                        top_recurring_problems TEXT,
                        suggested_improvements TEXT,
                        prioritized_issues TEXT,
                        total_issues INTEGER,
                        critical_issues INTEGER,
                        major_issues INTEGER,
                        minor_issues INTEGER,
                        code_smells INTEGER,
                        bugs INTEGER,
                        vulnerabilities INTEGER,
                        ai_model_used VARCHAR(100),
                        confidence_score FLOAT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(analysis_request_id) REFERENCES analysis_requests(id)
                    )
                """))
                
                # Copy data from old table to new table (excluding enhanced columns)
                connection.execute(text("""
                    INSERT INTO ai_reports_new 
                    (id, analysis_request_id, summary, top_recurring_problems, suggested_improvements, 
                     prioritized_issues, total_issues, critical_issues, major_issues, minor_issues,
                     code_smells, bugs, vulnerabilities, ai_model_used, confidence_score, created_at)
                    SELECT id, analysis_request_id, summary, top_recurring_problems, suggested_improvements, 
                           prioritized_issues, total_issues, critical_issues, major_issues, minor_issues,
                           code_smells, bugs, vulnerabilities, ai_model_used, confidence_score, created_at
                    FROM ai_reports
                """))
                
                # Drop old table and rename new table
                connection.execute(text("DROP TABLE ai_reports"))
                connection.execute(text("ALTER TABLE ai_reports_new RENAME TO ai_reports"))
                
                print("✅ Recreated ai_reports table with original structure")
                print(f"✅ Removed enhanced columns: grouped_by_file, issues_with_suggestions")
            else:
                print("ℹ️  Enhanced columns do not exist in ai_reports table")
            
            connection.commit()
            print("✅ Database migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Starting database migration to remove enhanced columns...")
    success = remove_enhanced_columns()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("📝 Reverted ai_reports table to original structure")
    else:
        print("❌ Migration failed!")
        sys.exit(1)