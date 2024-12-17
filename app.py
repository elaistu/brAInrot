from flask import Flask, request, render_template, jsonify, url_for
import os
import brAInrot
import sqlite3

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def get_top_5_music_images_url(self, top_5_music):
        result = []
        for song_title in top_5_music:
            self.cursor.execute("""
                SELECT "Song Title", Thumbnail, URL FROM songs WHERE "Song Title" = ?
            """, (song_title,))
            row = self.cursor.fetchone()
            if row:
                result.append({
                    "SongTitle": row[0],
                    "Thumbnail": row[1],
                    "URL": row[2]
                })
        return result

    def close(self):
        self.conn.close()

# Load the model once when the application starts
tokenizer, model, image_processor = brAInrot.load_model()
device = "cuda"  # or "cpu" depending on your setup

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"message": "No video file part"}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({"message": "No selected video file"}), 400
    
    if video_file and allowed_file(video_file.filename):
        # Save the file to the static/uploads folder
        filename = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        video_file.save(filename)
        
        # Process the video using the saved file path
        descriptor = brAInrot.describeVideo(filename, tokenizer, model, image_processor, device)
        video_url = url_for('static', filename='uploads/' + video_file.filename)

        top_5_music = [
            "OCEAN WAVES",
            "RIVER SONG",
            "TROPICAL VIBES",
            "FOREST HARMONY",
            "MEADOW SERENADE"
        ]

        db = Database('Music.db')
        top_5_music_images = db.get_top_5_music_images_url(top_5_music)
        db.close()
        print(top_5_music_images)
        
        return render_template('index.html', video_url=video_url, description=descriptor, top_5_music_images=top_5_music_images, enumerate=enumerate)
    else:
        return jsonify({"message": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)