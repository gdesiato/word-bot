import requests
import os
from mastodon import Mastodon
import subprocess  # To push updates to GitHub

# Load API keys from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
HISTORY_FILE = "history.txt"  # File to store past words

def load_history():
    """Loads past words from history.txt to prevent duplicates."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return {line.strip() for line in file if line.strip()}  # Only store words
    except FileNotFoundError:
        return set()  # If the file doesn't exist, start with an empty set

def save_word(word):
    """Saves the new word to history.txt and commits it to GitHub."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(f"{word}\n")  # Saves only the word, not the full post

    # Commit & push changes to GitHub if a new word is found
    subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions Bot"])
    subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
    subprocess.run(["git", "add", HISTORY_FILE])
    subprocess.run(["git", "commit", "-m", f"Updated history with new word: {word}"])
    subprocess.run(["git", "push"])

def generate_word():
    """Fetches a random Italian word, ensuring uniqueness."""
    prompt = """
    Generate a random Italian word and provide the following format with clear spacing:

    Word: [Italian word]

    Example sentence:
    "[Example sentence in Italian]"

    Translation:
    "[English translation]"

    Hashtags:
    #Italian #LearnItalian #ItalianWord #Italy

    Ensure the output follows this exact format with line breaks and no extra text.
    """

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    history = load_history()  # Load past words
    attempts = 0
    max_attempts = 5  # Prevent infinite loops

    while attempts < max_attempts:
        response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json={"model": "mistral-medium", "messages": [{"role": "user", "content": prompt}]})

        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            lines = content.split("\n")
            word = lines[0].replace("Word: ", "").strip()  # Extract only the word

            if word not in history:  # Prevent duplicates
                save_word(word)  # Save only the word
                return content  # Return full content for posting
        else:
            print("Mistral API Error:", response.json())

        attempts += 1

    return None  # Return None if no new word is found

def post_to_mastodon(text):
    """Posts the generated word and sentence to Mastodon."""
    mastodon = Mastodon(
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url="https://mastodon.social"
    )
    mastodon.status_post(text)
    print("Post sent to Mastodon!")

if __name__ == "__main__":
    content = generate_word()

    if content:
        print("Generated Content:\n", content)  # Debugging: Print content before posting
        post_to_mastodon(f"📖 Word of the Day:\n\n{content}")
    else:
        print("No new word found. Nothing will be posted.")
