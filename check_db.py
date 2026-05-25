import sqlite3
import os

print('Database file exists:', os.path.exists('storage/test_sessions.db'))
if os.path.exists('storage/test_sessions.db'):
    conn = sqlite3.connect('storage/test_sessions.db')
    c = conn.cursor()
    
    # Get table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print('Tables:', tables)
    
    # Get columns for actions table
    try:
        c.execute('PRAGMA table_info(actions)')
        columns = c.fetchall()
        print('Actions table columns:')
        for col in columns:
            print(f'  {col}')
    except Exception as e:
        print('Error getting table info:', e)
    
    # Check if we have any data for session 10
    try:
        c.execute('SELECT COUNT(*) FROM actions WHERE session_id = 10')
        count = c.fetchone()[0]
        print(f'Number of actions for session 10: {count}')
        
        if count > 0:
            c.execute('SELECT id, action_type, selector, value, element_name, element_type FROM actions WHERE session_id = 10 ORDER BY timestamp')
            rows = c.fetchall()
            print('Actions for session 10:')
            for row in rows:
                print(f'  {row}')
    except Exception as e:
        print('Error querying actions:', e)
    
    conn.close()
else:
    print('Database file not found')