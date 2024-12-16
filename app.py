from flask import Flask, request, render_template, jsonify
import os
import brAInrot

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        # Save the video to the server
        filename = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        video_file.save(filename)
        descriptor = brAInrot.describeVideo(filename)
        # this message needs to be pumped into a gpt thingy
        return jsonify({"message": descriptor}), 200 
    else:
        return jsonify({"message": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)