import os
import subprocess
from yt_dlp import YoutubeDL
import sqlite3
from lyrics_transcriber import LyricsTranscriber
import re
import argparse
from ollama import chat

def call_script(script_name):
    result = subprocess.run(['python32', script_name], capture_output=True, text=True)
    return True

def download_audio(video_url, format='mp3'):
    output_dir = 'music'
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info_dict)
        song_title = info_dict.get('title', 'Unknown Title')

        # Remove the .webm extension and add .mp3
        if downloaded_file.endswith('.webm'):
            downloaded_file = downloaded_file[:-5] + '.' + format

        return downloaded_file, song_title

def run_genre_classifier(wav_file):
    result = subprocess.run(['python37', 'genre_classification.py', '--file', wav_file], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running genre_classifier.py: {result.stderr}")
        return None
    return result.stdout.strip()

def sanitize_filename(filename):
    # Remove invalid characters for Windows filenames
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def transcribe_mp3(mp3_file_path, song_title):
    sanitized_title = sanitize_filename(song_title)
    transcription_dir = f'transcriptions/{sanitized_title}'
    os.makedirs(transcription_dir, exist_ok=True)

    transcriber = LyricsTranscriber(mp3_file_path)
    transcriber.output_dir = transcription_dir
    result_metadata = transcriber.generate()

    return result_metadata["transcription_data_dict"]["text"]

def add_column_if_not_exists(conn, table, column, column_type):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in c.fetchall()]
    if column not in columns:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
    conn.commit()

def update_music_description(video_id, music_description):
    conn = sqlite3.connect('youtube_song_list.db')
    add_column_if_not_exists(conn, 'songs', 'music_description', 'TEXT')
    c = conn.cursor()
    c.execute('UPDATE songs SET music_description = ? WHERE video_id = ?', (music_description, video_id))
    conn.commit()
    conn.close()

def update_genre(video_id, genre):
    conn = sqlite3.connect('youtube_song_list.db')
    add_column_if_not_exists(conn, 'songs', 'genre', 'TEXT')
    c = conn.cursor()
    c.execute('UPDATE songs SET genre = ? WHERE video_id = ?', (genre, video_id))
    conn.commit()
    conn.close()

def update_transcription(video_id, transcription):
    conn = sqlite3.connect('youtube_song_list.db')
    add_column_if_not_exists(conn, 'songs', 'transcription', 'TEXT')
    c = conn.cursor()
    c.execute('UPDATE songs SET transcription = ? WHERE video_id = ?', (transcription, video_id))
    conn.commit()
    conn.close()

def get_youtube_description(video_id):
    conn = sqlite3.connect('youtube_song_list.db')
    c = conn.cursor()
    c.execute('SELECT description FROM songs WHERE video_id = ?', (video_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def generate_music_description(genre, youtube_description, transcription):
    query = f"""
    genre: {genre}
    youtube_description: {youtube_description}
    lyric: {transcription}
    Give a short description of under 50 words of the music based on the lyrics and the youtube_description
    """

    stream = chat(
        model='vanilj/Phi-4:Q8_0',
        messages=[{'role': 'user', 'content': query}],
        stream=True,
    )

    description = ""
    for chunk in stream:
        description += chunk['message']['content']
        print(chunk['message']['content'], end='', flush=True)
    
    return description


def main(start_row, update_db):
    if update_db:
        # Step 1: Call youtube.py to create the database
        if not call_script('youtube.py'):
            return

    # Step 2: Connect to the database and fetch video URLs
    conn = sqlite3.connect('youtube_song_list.db')
    c = conn.cursor()
    c.execute('SELECT video_id FROM songs')
    video_urls = [f"https://www.youtube.com/watch?v={row[0]}" for row in c.fetchall()]
    conn.close()

    for idx, video_url in enumerate(video_urls[start_row:], start=start_row):
        video_id = video_url.split('=')[-1]

        # Step 3: Download the video in both wav and mp3 formats
        wav_file, _ = download_audio(video_url, format='wav')
        mp3_file, song_title = download_audio(video_url, format='mp3')

        print(f"Downloaded {wav_file} and {mp3_file}")

        # Step 4: Run genre_classifier.py on the wav file
        print("RUNNING GENRE CLASSIFICATION")
        genre = run_genre_classifier(wav_file)
        if genre:
            update_genre(video_id, genre)
            print(f"Updated database for {song_title} with genre: {genre}")

        # Step 5: Transcribe the MP3 file
        print("RUNNING TRANSCRIPTION")
        transcription = transcribe_mp3(mp3_file, song_title)
        update_transcription(video_id, transcription)
        print(f"Updated database for {song_title} with transcription.")

        # Step 6: Generate music description
        print("GENERATING MUSIC DESCRIPTION")
        youtube_description = get_youtube_description(video_id)  # Assuming you have a function to get YouTube description
        music_description = generate_music_description(genre, youtube_description, transcription)
        update_music_description(video_id, music_description)
        print(f"Updated database for {song_title} with music description.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process YouTube videos from a certain row onwards.')
    parser.add_argument('--start_row', type=int, default=0, help='The row number to start processing from')
    parser.add_argument('--update_db', action='store_true', help='Update the database by calling youtube.py')
    args = parser.parse_args()

    main(args.start_row, args.update_db)