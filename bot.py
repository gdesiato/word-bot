import requests
import os
from mastodon import Mastodon
import subprocess  # To push updates to GitHub

# Load API keys from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
HISTORY_FILE = "history.txt"  # File to store past words

def load_history():
    try:
        with open("history.txt", "r", encoding="utf-8") as file:
            return {
                line.strip().split(":")[1]  # Extracts words
                for line in file
                if line.strip() and ":" in line
            }
    except FileNotFoundError:
        return set()  # Returns an empty set if history.txt doesn't exist

def save_word(word, content):
    """Saves the new word to the history file and commits it to GitHub."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(f"{word}: {content}\n")

    # Commit & push changes to GitHub
    subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions Bot"])
    subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
    subprocess.run(["git", "add", HISTORY_FILE])
    subprocess.run(["git", "commit", "-m", f"Updated history with new word: {word}"])
    subprocess.run(["git", "push"])

def generate_word():
    """Fetches a random Italian word, example sentence, and English translation from Mistral AI."""
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
            lines = content.split("\n")  # Extract the word
            word = lines[0].replace("Word: ", "").strip()

            if word not in history:  # Check if it's new
                save_word(word, content)  # Save to history & commit to GitHub
                return content
        else:
            print("Mistral API Error:", response.json())

        attempts += 1

    return "Error: Could not generate a new word."

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
    print("Generated Content:\n", content)  # Debugging: Print content before posting

    if "Error" not in content:  # Prevents posting if Mistral API fails
        post_to_mastodon(f"📖 Word of the Day:\n\n{content}")
    else:
        print("Error detected, not posting.")
