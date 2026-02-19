import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import api_key

client = genai.Client(api_key="AIzaSyA-rR8cYHDIjcHUISgVuOh0xClU1brSeRE")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        system_instruction="You are a cat. Your name is Neko."),
    contents="Hello there"
)

print(response.text)

