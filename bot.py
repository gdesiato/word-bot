import requests
import os
from mastodon import Mastodon

# Load API Keys from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")

def generate_word():
    """Fetches a random Italian word, an example sentence, and an English translation from Mistral AI."""
    prompt = """
Generate a random Italian word and provide the following format:

Word: [Italian word]
Example sentence: "[Example sentence in Italian]"

Translation: "[English translation]"

Hashtags: #Italian #LearnItalian #ItalianWord

Ensure the output follows this exact format with no additional text.
"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "mistral-medium",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=json_data)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.json()}"

def post_to_mastodon(text):
    """Posts the generated word and sentence to Mastodon."""
    mastodon = Mastodon(
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url="https://mastodon.social"  # Change if your bot is on a different instance
    )
    mastodon.status_post(text)
    print("Post sent to Mastodon!")

if __name__ == "__main__":
    content = generate_word()
    print("Generated Content:", content)  # Debugging: Print content before posting

    if "Error" not in content:  # Prevents posting if Mistral API fails
        post_to_mastodon(f"📖 Word of the Day:\n{content}\n\n#ItalianWord #LearnItalian")
    else:
        print("Error detected, not posting.")
