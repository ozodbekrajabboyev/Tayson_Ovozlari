import sqlite3

class Database:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db, check_same_thread=False)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        data = None

        try:
            cursor.execute(sql, parameters)
            if commit:
                connection.commit()
            if fetchall:
                data = cursor.fetchall()
            if fetchone:
                data = cursor.fetchone()
        except sqlite3.OperationalError as e:
            print(f"SQLite xatosi: {e}")
        finally:
            cursor.close()
            connection.close()
        
        return data

    def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS USERS(
        full_name TEXT,
        telegram_id NUMBER unique );
        """
        self.execute(sql, commit=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ?" for item in parameters
        ])
        return sql, tuple(parameters.values())

    def add_user(self, telegram_id:int, full_name:str):
        sql = """
        INSERT INTO Users(telegram_id, full_name) VALUES(?, ?)
        """
        self.execute(sql, parameters=(telegram_id, full_name), commit=True)

    def select_all_users(self):
        sql = "SELECT * FROM Users"
        return self.execute(sql, fetchall=True)

    def check_user_exists(self, user_id: int) -> bool:
        sql = "SELECT 1 FROM Users WHERE telegram_id = ?"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result is not None
        
    def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def count_users(self):
        return self.execute("SELECT COUNT(*) FROM Users;", fetchone=True)

    def delete_users(self):
        self.execute("DELETE FROM Users WHERE TRUE", commit=True)
    
    def all_users_id(self):
        return self.execute("SELECT telegram_id FROM Users;", fetchall=True)

    # ==== Audio bo‘limi ====
    def create_table_audios(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Audio (
            id INTEGER PRIMARY KEY,
            voice_file_id VARCHAR(50) UNIQUE,
            title VARCHAR(20)
        );
        """
        self.execute(sql, commit=True)

    def add_audio(self, voice_file_id: str, title: str):  
        sql = """
        INSERT INTO Audio(voice_file_id, title) VALUES(?, ?)
        """
        self.execute(sql, parameters=(voice_file_id, title), commit=True)

    def get_audio_by_id(self, audio_id: int):
        sql = "SELECT * FROM Audio WHERE id = ?"
        return self.execute(sql, parameters=(audio_id,), fetchone=True)

    def select_all_audios(self, sort_by_usage=False, ok = False, ok1 = False):
        if sort_by_usage:
            sql = """
                SELECT 
                    a.id,
                    a.voice_file_id,
                    a.title,
                    COALESCE(vs.usage_count, 0) as usage_count
                FROM Audio a
                LEFT JOIN VoiceStats vs ON a.id = vs.audio_id
                WHERE a.voice_file_id IS NOT NULL  
                ORDER BY usage_count DESC, a.title
                """
        elif ok:
            sql = "SELECT * FROM Audio"
        elif ok1:
            sql = """
            SELECT a.id, a.title, COALESCE(vs.usage_count, 0) as usage_count
            FROM Audio a
            LEFT JOIN VoiceStats vs ON a.id = vs.audio_id
            """
        elif sort_by_usage == False:
            sql = "SELECT id, title FROM Audio"
        return self.execute(sql, fetchall=True)





    def search_audios_title(self, title):
        sql = """
        SELECT 
            a.id,
            a.voice_file_id,
            a.title,
            COALESCE(vs.usage_count, 0) as usage_count
        FROM Audio a
        LEFT JOIN VoiceStats vs ON a.id = vs.audio_id
        WHERE a.title LIKE ?
        ORDER BY usage_count DESC, a.title
        """
        return self.execute(sql, parameters=(f"%{title}%",), fetchall=True)

    # ==== Voice Stats bo‘limi ====
    def create_table_voice_stats(self):
        sql = """
        CREATE TABLE IF NOT EXISTS VoiceStats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_id TEXT UNIQUE NOT NULL,
            usage_count INTEGER DEFAULT 0 NOT NULL,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (audio_id) REFERENCES Audio (id)
        );
        """
        self.execute(sql, commit=True)

    def increment_voice_usage(self, audio_id: int):
        sql = """
        INSERT INTO VoiceStats(audio_id, usage_count)
        VALUES(?, 1)
        ON CONFLICT(audio_id) DO UPDATE SET
            usage_count = usage_count + 1,
            last_used = CURRENT_TIMESTAMP
        """
        self.execute(sql, parameters=(audio_id,), commit=True)

    def get_voice_stats(self, audio_id: int):
        sql = """
        SELECT vs.usage_count, vs.last_used, a.title 
        FROM VoiceStats vs
        JOIN Audio a ON vs.audio_id = a.id
        WHERE vs.audio_id = ?
        """
        result = self.execute(sql, parameters=(audio_id,), fetchone=True)
        if result:
            return {
                'usage_count': result[0],
                'last_used': result[1],
                'title': result[2]
            }
        return None

    def get_top_voices(self, limit: int = 10):
        sql = """
            SELECT a.id, a.title, vs.usage_count, vs.last_used 
            FROM VoiceStats vs
            JOIN Audio a ON vs.audio_id = a.id
            ORDER BY vs.usage_count DESC
            LIMIT ?
        """
        return self.execute(sql, parameters=(limit,), fetchall=True)

    def upgrade_audio_table(self):
        columns_to_add = [
            ("telegram_id", "INTEGER"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        for column, col_type in columns_to_add:
            try:
                self.execute(f"ALTER TABLE Audio ADD COLUMN {column} {col_type}", commit=True)
            except sqlite3.OperationalError:
                pass  # Column already exists

def logger(statement):
    print(f"""
_____________________________________________________        
Executing: 
{statement}
_____________________________________________________
""")
