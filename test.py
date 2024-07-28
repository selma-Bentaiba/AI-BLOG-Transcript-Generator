#openai.api_key = 'sk-proj-zos24CmhyBO99r81UiAuT3BlbkFJr9OvjuNSy1IrP4pzyzWA'
#gmini = AIzaSyBY2MR2Pud5feT-DI8IX4p5a11U4P4dKF8
import os
import requests
import assemblyai as aai
import google.generativeai as genai

# Set your API keys here
ASSEMBLYAI_API_KEY = 'e923464c9bc74edab43a336ddadb093d'
GOOGLE_API_KEY = 'AIzaSyBY2MR2Pud5feT-DI8IX4p5a11U4P4dKF8'

aai.settings.api_key = ASSEMBLYAI_API_KEY
genai.configure(api_key=os.getenv("API_KEY"))

model = genai.GenerativeModel('gemini-pro')

def transcribe_audio(audio_file):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text

def generate_blog_from_transcription(transcription):
    prompt = f"""
    Based on the following transcript from an audio file, write a comprehensive blog article. Write it based on the transcript, but don't make it look like it came from an audio file; make it look like a proper blog article:

    {transcription}

    Article:
    """

    try:
        response = model.generate_content(prompt)
        generated_text = response.candidates[0].content.parts[0].text.strip()
        return generated_text
    except Exception as e:
        print(f"API request error: {e}")
        return None

if __name__ == "__main__":
    audio_file = 'media/the art of showing up.mp3'  # Replace with your audio file path
    if not os.path.exists(audio_file):
        print(f"Audio file not found: {audio_file}")
    else:
        transcription = transcribe_audio(audio_file)
        print(f"Transcription: {transcription}")

        blog_content = generate_blog_from_transcription(transcription)
        if blog_content:
            print(f"Generated Blog Article:\n{blog_content}")
        else:
            print("Failed to generate blog article.")
