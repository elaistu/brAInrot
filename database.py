import sqlite3
class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def get_top_5_music_images_url(self, video_ids):
        result = []
        for video_id in video_ids:
            self.cursor.execute("""
                SELECT video_id, thumbnail_base64, title FROM songs WHERE id = ?
            """, (video_id,))
            row = self.cursor.fetchone()
            if row:
                result.append({
                    "SongTitle": row[0],
                    "Thumbnail": row[1],
                    "URL": "https://www.youtube.com/watch?v=" + row[2]
                })

        return result
    
    def get_all_songs_info(self):
        self.cursor.execute("""
            SELECT video_id, Genre, music_description FROM songs
        """)
        rows = self.cursor.fetchall()
        result = [[row[0], row[1], row[2]] for row in rows]
        return result

    def close(self):
        self.conn.close()