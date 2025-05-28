import os
import psycopg2
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv(dotenv_path="/Users/alphy/Python Files/TheraCareHx/.env")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        try:
            # First create users table (no dependencies)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Then create profiles table (depends on users)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    gorilla_id VARCHAR(255) NOT NULL,
                    profile_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            """)
            
            # Finally create conditions table (depends on users)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conditions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    gorilla_id VARCHAR(255) NOT NULL,
                    api_response JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            """)
            
            # Create family history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS family_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    gorilla_id VARCHAR(255),
                    api_response JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {e}")
        finally:
            cur.close()
            conn.close()

def create_user(username, email, password_hash):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            print(f"Error creating user: {e}")
            return None
        finally:
            cur.close()
            conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, username, email, password_hash FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            return user
        finally:
            cur.close()
            conn.close()
    return None

def save_profile(user_id, gorilla_id, profile_data):
    """
    Save or update a user's profile
    """
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Check if profile exists
            cur.execute("SELECT id FROM profiles WHERE user_id = %s", (user_id,))
            profile = cur.fetchone()
            
            if profile:
                # Update existing profile
                cur.execute("""
                    UPDATE profiles 
                    SET gorilla_id = %s, 
                        profile_data = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING id
                """, (gorilla_id, json.dumps(profile_data), user_id))
            else:
                # Create new profile
                cur.execute("""
                    INSERT INTO profiles (user_id, gorilla_id, profile_data)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (user_id, gorilla_id, json.dumps(profile_data)))
            
            profile_id = cur.fetchone()[0]
            conn.commit()
            return profile_id
        except Exception as e:
            conn.rollback()
            print(f"Error saving profile: {e}")
            return None
        finally:
            cur.close()
            conn.close()

def get_profile_by_user_id(user_id):
    """
    Get a user's profile by their user ID
    """
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, gorilla_id, profile_data, created_at, updated_at 
                FROM profiles 
                WHERE user_id = %s
            """, (user_id,))
            profile = cur.fetchone()
            if profile:
                return {
                    'id': profile[0],
                    'gorilla_id': profile[1],
                    'profile_data': profile[2],
                    'created_at': profile[3],
                    'updated_at': profile[4]
                }
            return None
        finally:
            cur.close()
            conn.close()
    return None

def check_and_init_db():
    """
    Check if database exists and initialize it if it doesn't
    """
    try:
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if users table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        users_exists = cur.fetchone()[0]
        
        # Check if profiles table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'profiles'
            );
        """)
        profiles_exists = cur.fetchone()[0]
        
        # Check if conditions table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'conditions'
            );
        """)
        conditions_exists = cur.fetchone()[0]
        
        # Check if family_history table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'family_history'
            );
        """)
        family_history_exists = cur.fetchone()[0]
        
        # Create users table if it doesn't exist
        if not users_exists:
            cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # Create profiles table if it doesn't exist
        if not profiles_exists:
            cur.execute("""
                CREATE TABLE profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    gorilla_id VARCHAR(50),
                    profile_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # Create conditions table if it doesn't exist
        if not conditions_exists:
            cur.execute("""
                CREATE TABLE conditions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    gorilla_id VARCHAR(50),
                    api_response JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            # Alter existing conditions table to make gorilla_id nullable
            cur.execute("""
                ALTER TABLE conditions 
                ALTER COLUMN gorilla_id DROP NOT NULL;
            """)
        
        # Create family_history table if it doesn't exist
        if not family_history_exists:
            cur.execute("""
                CREATE TABLE family_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    gorilla_id VARCHAR(50),
                    api_response JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

def save_conditions(user_id, gorilla_id, api_response):
    """
    Save conditions API response for a user
    """
    # Ensure database is initialized
    check_and_init_db()
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Check if conditions exist for this user
            cur.execute("SELECT id FROM conditions WHERE user_id = %s", (user_id,))
            existing = cur.fetchone()
            
            if existing:
                # Update existing conditions
                cur.execute("""
                    UPDATE conditions 
                    SET api_response = %s,
                        gorilla_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING id
                """, (json.dumps(api_response), gorilla_id, user_id))
            else:
                # Insert new conditions
                cur.execute("""
                    INSERT INTO conditions (
                        user_id, gorilla_id, api_response
                    ) VALUES (%s, %s, %s)
                    RETURNING id
                """, (user_id, gorilla_id, json.dumps(api_response)))
            
            condition_id = cur.fetchone()[0]
            conn.commit()
            return condition_id
        except Exception as e:
            conn.rollback()
            print(f"Error saving conditions: {e}")
            return None
        finally:
            cur.close()
            conn.close()

def get_conditions_by_user_id(user_id):
    """
    Get conditions API response for a user
    """
    # Ensure database is initialized
    check_and_init_db()
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, gorilla_id, api_response, created_at, updated_at
                FROM conditions
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            if result:
                return {
                    'id': result[0],
                    'gorilla_id': result[1],
                    'api_response': result[2],  # No need for json.loads as it's already in JSON format
                    'created_at': result[3],
                    'updated_at': result[4]
                }
            return None
        finally:
            cur.close()
            conn.close()
    return None

def check_duplicate_condition(user_id, new_condition):
    """
    Check if a condition already exists in the database for a user
    Returns True if duplicate found, False otherwise
    """
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Get existing conditions
            cur.execute("""
                SELECT api_response 
                FROM conditions 
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            
            if not result or not result[0]:
                return False
                
            existing_conditions = result[0]
            
            # Extract key fields from new condition
            new_resource = new_condition.get('resource', {}) if isinstance(new_condition, dict) else {}
            new_code = new_resource.get('code', {}) if isinstance(new_resource, dict) else {}
            new_name = new_code.get('text', '')
            if not new_name and isinstance(new_code.get('coding'), list) and new_code.get('coding'):
                new_name = new_code['coding'][0].get('display', '')
            
            new_date = new_resource.get('assertedDate', '')
            new_status = new_resource.get('clinicalStatus', '')
            
            # Check each existing condition
            for entry in existing_conditions:
                # Ensure entry is a dictionary
                if not isinstance(entry, dict):
                    continue
                    
                existing_resource = entry.get('resource', {}) if isinstance(entry.get('resource'), dict) else entry
                existing_code = existing_resource.get('code', {}) if isinstance(existing_resource, dict) else {}
                existing_name = existing_code.get('text', '')
                if not existing_name and isinstance(existing_code.get('coding'), list) and existing_code.get('coding'):
                    existing_name = existing_code['coding'][0].get('display', '')
                
                existing_date = existing_resource.get('assertedDate', '') if isinstance(existing_resource, dict) else ''
                existing_status = existing_resource.get('clinicalStatus', '') if isinstance(existing_resource, dict) else ''
                
                # Compare key fields
                if (new_name == existing_name and 
                    new_date == existing_date and 
                    new_status == existing_status):
                    return True
            
            return False
        finally:
            cur.close()
            conn.close()
    return False

def save_family_history(user_id, gorilla_id, api_response):
    """
    Save family history API response for a user
    """
    # Ensure database is initialized
    check_and_init_db()
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Check if family history exists for this user
            cur.execute("SELECT id FROM family_history WHERE user_id = %s", (user_id,))
            existing = cur.fetchone()
            
            if existing:
                # Update existing family history
                cur.execute("""
                    UPDATE family_history 
                    SET api_response = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING id
                """, (json.dumps(api_response), user_id))
            else:
                # Insert new family history
                cur.execute("""
                    INSERT INTO family_history (
                        user_id, gorilla_id, api_response
                    ) VALUES (%s, %s, %s)
                    RETURNING id
                """, (user_id, gorilla_id, json.dumps(api_response)))
            
            history_id = cur.fetchone()[0]
            conn.commit()
            return history_id
        except Exception as e:
            conn.rollback()
            print(f"Error saving family history: {e}")
            return None
        finally:
            cur.close()
            conn.close()

def get_family_history_by_user_id(user_id):
    """
    Get family history API response for a user
    """
    # Ensure database is initialized
    check_and_init_db()
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, gorilla_id, api_response, created_at, updated_at
                FROM family_history
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            if result:
                return {
                    'id': result[0],
                    'gorilla_id': result[1],
                    'api_response': result[2],  # No need for json.loads as it's already in JSON format
                    'created_at': result[3],
                    'updated_at': result[4]
                }
            return None
        finally:
            cur.close()
            conn.close()
    return None

def check_duplicate_family_history(user_id, new_history):
    """
    Check if a family history entry already exists in the database for a user
    Returns True if duplicate found, False otherwise
    """
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Get existing family history
            cur.execute("""
                SELECT api_response 
                FROM family_history 
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            
            if not result or not result[0]:
                return False
                
            existing_history = result[0]
            
            # Extract key fields from new history entry
            new_resource = new_history.get('resource', {})
            new_relationship = new_resource.get('relationship', {})
            new_relationship_text = new_relationship.get('text', '')
            if not new_relationship_text and 'coding' in new_relationship:
                new_relationship_text = new_relationship['coding'][0].get('display', '')
            
            new_gender = new_resource.get('gender', '')
            new_born_date = new_resource.get('bornDate', '')
            
            # Check each existing history entry
            for entry in existing_history.get('entry', []):
                existing_resource = entry.get('resource', {})
                existing_relationship = existing_resource.get('relationship', {})
                existing_relationship_text = existing_relationship.get('text', '')
                if not existing_relationship_text and 'coding' in existing_relationship:
                    existing_relationship_text = existing_relationship['coding'][0].get('display', '')
                
                existing_gender = existing_resource.get('gender', '')
                existing_born_date = existing_resource.get('bornDate', '')
                
                # Compare key fields
                if (new_relationship_text == existing_relationship_text and 
                    new_gender == existing_gender and 
                    new_born_date == existing_born_date):
                    return True
            
            return False
        finally:
            cur.close()
            conn.close()
    return False

def get_all_user_data(user_id):
    """
    Get all data for a user from all tables
    Returns a dictionary containing all user data
    """
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Initialize result dictionary
            user_data = {
                "user_info": None,
                "profile": None,
                "conditions": None,
                "family_history": None
            }
            
            # Get user info
            cur.execute("""
                SELECT id, username, email, created_at 
                FROM users 
                WHERE id = %s
            """, (user_id,))
            user = cur.fetchone()
            if user:
                user_data["user_info"] = {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "created_at": user[3].isoformat() if user[3] else None
                }
            
            # Get profile data
            cur.execute("""
                SELECT gorilla_id, profile_data, created_at, updated_at 
                FROM profiles 
                WHERE user_id = %s
            """, (user_id,))
            profile = cur.fetchone()
            if profile:
                user_data["profile"] = {
                    "gorilla_id": profile[0],
                    "profile_data": profile[1],
                    "created_at": profile[2].isoformat() if profile[2] else None,
                    "updated_at": profile[3].isoformat() if profile[3] else None
                }
            
            # Get conditions data
            cur.execute("""
                SELECT gorilla_id, api_response, created_at, updated_at 
                FROM conditions 
                WHERE user_id = %s
            """, (user_id,))
            conditions = cur.fetchone()
            if conditions:
                user_data["conditions"] = {
                    "gorilla_id": conditions[0],
                    "api_response": conditions[1],
                    "created_at": conditions[2].isoformat() if conditions[2] else None,
                    "updated_at": conditions[3].isoformat() if conditions[3] else None
                }
            
            # Get family history data
            cur.execute("""
                SELECT gorilla_id, api_response, created_at, updated_at 
                FROM family_history 
                WHERE user_id = %s
            """, (user_id,))
            family_history = cur.fetchone()
            if family_history:
                user_data["family_history"] = {
                    "gorilla_id": family_history[0],
                    "api_response": family_history[1],
                    "created_at": family_history[2].isoformat() if family_history[2] else None,
                    "updated_at": family_history[3].isoformat() if family_history[3] else None
                }
            
            return user_data
        except Exception as e:
            print(f"Error getting all user data: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    return None 