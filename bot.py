import os
from dotenv import load_dotenv
from mastodon import Mastodon
import openai

# Load environment variables from .env
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

def generate_word():
    prompt = (
        "Generate a random Italian word, an example sentence using it, and its English translation. "
        "Format the output as:\n\nWord: <word>\nExample: <example sentence>\nTranslation: <translation>"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def post_to_mastodon(text):
    mastodon = Mastodon(access_token=MASTODON_ACCESS_TOKEN, api_base_url="https://mastodon.social")
    mastodon.status_post(text)

if __name__ == "__main__":
    content = generate_word()
    post_content = f"📖 Word of the Day:\n{content}\n\n#ItalianWord #LearnItalian"

    post_to_mastodon(post_content)
    print("Post sent!")
