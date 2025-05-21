import sqlite3
import chardet # Thư viện để tự động phát hiện encoding

def execute_sql_from_file(db_name, sql_file_path):
    """
    Executes SQL commands from a given .sql file against an SQLite database.
    Automatically detects the file encoding.

    Args:
        db_name (str): The name of the SQLite database file.
        sql_file_path (str): The path to the .sql file.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Detect the file's encoding
        with open(sql_file_path, 'rb') as f: # Mở file ở chế độ binary để đọc bytes
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']

        print(f"Detected encoding: {encoding} with confidence: {confidence}") #in ra encoding

        # Read the SQL file with the detected encoding
        with open(sql_file_path, 'r', encoding=encoding) as f:
            sql_script = f.read()

        # Execute the SQL script
        cursor.executescript(sql_script)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print(f"SQL script from '{sql_file_path}' executed successfully on database '{db_name}'.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: File not found at path '{sql_file_path}'.")
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}")
        print(f"Failed to decode file '{sql_file_path}' with detected encoding '{encoding}'.")
        print("You may need to try a different encoding, such as 'utf-8', 'latin-1', or 'cp1252'.")
    finally:
        if conn:
            conn.close()

sql_file_path = 'createdatabase.sql'
db_name = 'my_database.db'
execute_sql_from_file(db_name, sql_file_path)
