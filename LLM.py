from database import Database
from ollama import chat
import json

class LLM:
    def __init__(self, db_path):
        self.db = Database(db_path)
        self.song_info = self.generate_song_info_string()

    def generate_song_info_string(self):
        songs_info = self.db.get_all_songs_info()
        result = ""
        for i, song in enumerate(songs_info, start=1):
            result += f"Song Title {i}: {song[0]}, Genre: {song[1]}, music_description: {song[2]}\n"
        return result
    
    def generate_song_title(self):
        song_title = self.db.get_all_songs_info()
        result = ""
        for i, song in enumerate(song_title, start=1):
            result += f"Song Index {i}: {song[0]}\n"
        return result
    
    def create_query(self, video_description):
        query = f"""
        {self.song_info}
        Using the attached database, recommend 5 different **music titles** for the given video description: {video_description}.
        """
        
        # Save the query to a text file
        with open('query.txt', 'w', encoding='utf-8') as file:
            file.write(query)
        
        return query
    
    def generate_top_song(self, video_description):
        stream = chat(
            model='vanilj/Phi-4:Q8_0',
            messages=[{'role': 'user', 'content': self.create_query(video_description)}],
            stream=True,
        )

        response = ""
        for chunk in stream:
            response += chunk['message']['content']
        print("Response:\n", response)  # Print the response
        return response
    
    def clean_string(self, input):
        
        song_title = self.generate_song_title()

        query = f"""
        ###Song Information: {song_title} 
        ###Recommended song: {input} 
        ###Output the corresponding Song Indexes of the Recommended song titles in a list of 5 values in this format:[1,2,3,4,5]. No other text."""
        print(query)
        stream = chat(
            model='vanilj/Phi-4:Q8_0',
            messages=[{'role': 'user', 'content': query}],
            stream=True,
        )

        response = ""
        for chunk in stream:
            response += chunk['message']['content']
        return response
    
    def get_json_format(self, input):
        # Step 1: Remove the markdown code block delimiters
        cleaned_string = input.strip('```json\n').strip('```')

        # Step 2: Convert the cleaned string into a JSON object
        try:
            json_response = json.loads(cleaned_string)
            print("####\njson_response = ", json.dumps(json_response, indent=2))
            print(type(json_response))  # This will show <class 'dict'>
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
        print("json_response = ", json_response)    
        return json_response

    def close(self):
        self.db.close()

# Example usage
if __name__ == "__main__":
    llm = LLM('Music.db')
    llm.create_query("At a hospital in Greece, 10-year-old Michael Morbius welcomes his surrogate brother Lucien, whom he renames Milo; they bond over their shared blood illness and desire to be normal")
    response = llm.generate_top_song("At a hospital in Greece, 10-year-old Michael Morbius welcomes his surrogate brother Lucien, whom he renames Milo; they bond over their shared blood illness and desire to be normal")
    
    clean_response = llm.clean_string(response)

    print("####\nclean_response=", clean_response)
    print("####")


    llm.close()