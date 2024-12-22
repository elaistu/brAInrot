from flask import Flask, request, render_template, jsonify, url_for
import os
import brAInrot
import sqlite3
from database import Database
from LLM import LLM
import ast

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup()
        self.tokenizer, self.model, self.image_processor = brAInrot.VQAModelHandler().load_model()
        self.device = "cuda"  # or "cpu" depending on your setup
        self.db = Database('Music.db')
        self.llm = LLM('Music.db')

    def setup(self):
        UPLOAD_FOLDER = os.path.join('static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        self.app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
        self.allowed_extensions = ALLOWED_EXTENSIONS

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def home(self):
        return render_template('index.html')
    
    def open_database(self):
        self.db = sqlite3.connect('Music.db')
        self.db.row_factory = sqlite3.Row

    def close_database(self):
        if self.db:
            self.db.close()

    def upload_video(self):
        if 'video' not in request.files:
            return jsonify({"message": "No video file part"}), 400
        
        video_file = request.files['video']
        
        if video_file.filename == '':
            return jsonify({"message": "No selected video file"}), 400
        
        if video_file and self.allowed_file(video_file.filename):
            # Save the file to the static/uploads folder
            filename = os.path.join(self.app.config['UPLOAD_FOLDER'], video_file.filename)
            video_file.save(filename)
            
            # Process the video using the saved file path
            descriptor = brAInrot.VQAModelHandler().describe_video(filename)
            video_url = url_for('static', filename='uploads/' + video_file.filename)

            response = self.llm.generate_top_song(descriptor)
            print("response", response)
            top_5_music = self.llm.clean_string(response)

            string = """[86, 90, 91, 88, 86]"""

            # Convert string to list
            list_from_string = ast.literal_eval(string)

            print("####list_from string\n:",list_from_string, "\n####")  # Output: [86, 90, 91, 88, 86]
            print(type(list_from_string))  # Output: <class 'list'>

            print("######\ntop_5_music\n", top_5_music, "\n######")
            # print(type(top_5_music))
            # top_5_music_list = self.llm.get_json_format(top_5_music)

            # top_5_music_list = [song["index"] for song in top_5_music_list["suggested_songs"]]
            
            top_5_music_images = self.db.get_top_5_music_images_url(list_from_string)
            print("top_5_music_images", top_5_music_images)
            
            return render_template('index.html', video_url=video_url, description=descriptor, top_5_music_images=top_5_music_images, enumerate=enumerate)
        else:
            return jsonify({"message": "Invalid file type"}), 400

    def run(self):
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/upload', 'upload_video', self.upload_video, methods=['POST'])
        self.app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    flask_app = FlaskApp()
    flask_app.run()