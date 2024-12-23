# brAInrot Music Suggestion Tool

brAInrot is a web-based app for video creators that provides background music suggestions. 

## Usage

Upload a .mp4 video and brAInrot will suggest 5 thematically appropriate and copyright-free tracks in real-time

## Requirements

To run this application, you need to have Python installed. You can install the required packages using pip:

```
pip install -r requirements.txt
```

## Running the Application

To start the Flask application, run the following command:

```
python app.py
```

The application will be available at `http://127.0.0.1:5000/`.

## Features
![Music Analyser Architecture](Music_Analyser_Architecture.png)
- Static files (CSS and JavaScript) for styling and interactivity.
- A main HTML template for rendering the web page.
- Basic Flask application structure with routes and configurations.
- Either uses the local run Phi-4 LLM by microsoft or OpenAI API

## License

This project is licensed under the MIT License.