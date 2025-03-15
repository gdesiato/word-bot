import os
import openai
from dotenv import load_dotenv
from mastodon import Mastodon

# Load environment variables
load_dotenv()

# Get API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")

# Set OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_word():
    prompt = (
        "Generate a random Italian word, an example sentence using it, and its English translation. "
        "Format the output as:\n\nWord: <word>\nExample: <example sentence>\nTranslation: <translation>"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def post_to_mastodon(text):
    mastodon = Mastodon(access_token=MASTODON_ACCESS_TOKEN, api_base_url="https://mastodon.social")
    mastodon.status_post(text)

if __name__ == "__main__":
    content = generate_word()
    post_content = f"📖 Word of the Day:\n{content}\n\n#ItalianWord #LearnItalian"

    post_to_mastodon(post_content)
    print("Post sent!")
