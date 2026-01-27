import sqlite3
import os


def migrate():
    db_path = "elyon.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Rename column if it exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if "last_workspace_id" in columns and "active_workspace_id" not in columns:
            print("Renaming last_workspace_id to active_workspace_id in users table...")
            # SQLite 3.25+ supports RENAME COLUMN
            cursor.execute(
                "ALTER TABLE users RENAME COLUMN last_workspace_id TO active_workspace_id"
            )
            print("✓ Column renamed successfully.")
        elif "active_workspace_id" in columns:
            print("✓ users.active_workspace_id column already exists.")
        else:
            print(
                "! Could not find last_workspace_id to rename, and active_workspace_id doesn't exist."
            )

        # 2. Create archived_panes table
        print("Ensuring archived_panes table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archived_panes (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id INTEGER,
                pane_data JSON NOT NULL,
                archived_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("✓ archived_panes table verified.")

        conn.commit()
        print("\nMigration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
