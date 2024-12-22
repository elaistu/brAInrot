from database import Database
from ollama import chat

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
            result += f"Song Title {i}: {song[0]}\n"
        return result
    
    def create_query(self, video_description):
        
        query = f"""
        {self.song_info}
        Using the above database, select the top 5 appropriate background songs for the given video description: {video_description}"""
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
        return response
    
    def clean_string(self, input):
        
        song_title = self.generate_song_title()

        query = f"""
        ###Song info: {song_title} 
        ###Recommended song: {input} 
        ###Output the index of the song in the Recommended song in this specified format: [56,73,3,98,68]. Do not include any processes."""

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

    def close(self):
        self.db.close()

# Example usage
if __name__ == "__main__":
    llm = LLM('Music.db')
    # print(llm.create_query("A video of a beach with waves crashing on the shore"))
    response = llm.generate_top_song("A video of a chinchillas fighting")
    print(response + "\n\n\n") 
    clean_response = llm.clean_string(response)
    print(clean_response)
    llm.close()