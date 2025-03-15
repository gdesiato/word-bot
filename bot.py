import time
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
            return {line.strip() for line in file if line.strip()}
    except FileNotFoundError:
        return set()

def save_word(word):
    """Saves the new word to history.txt and commits it to GitHub."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(f"{word}\n")

    # Commit & push changes to GitHub if a new word is found
    subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions Bot"])
    subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])
    subprocess.run(["git", "add", HISTORY_FILE])
    subprocess.run(["git", "commit", "-m", f"Updated history with new word: {word}"])
    subprocess.run(["git", "push"])

def generate_word():
    """Fetches a random Italian word, ensuring uniqueness."""
    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY is not set! Exiting.")
        exit(1)

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

    history = load_history()
    attempts = 0
    max_attempts = 5

    while attempts < max_attempts:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json={"model": "mistral-medium", "messages": [{"role": "user", "content": prompt}]}
        )

        if response.status_code == 200:
            print("Full Mistral API JSON Response:", response.json())

            content = response.json()['choices'][0]['message']['content']
            print("Extracted Content from API:\n", content)

            lines = content.split("\n")

            # Fix: Extract the first non-empty word after "Word:"
            word = None
            for i in range(len(lines)):
                if lines[i].strip().lower() == "word:" and i + 1 < len(lines):
                    word = lines[i + 1].strip()  # Get the next line as the word
                    break

            if word:
                if not history or word not in history:
                    save_word(word)
                    return content
                else:
                    print(f"Duplicate word ({word}). Retrying...")
            else:
                print("Invalid response format. Retrying...")

        elif response.status_code == 401:
            print("ERROR: Unauthorized! Check if your MISTRAL_API_KEY is correct.")
            exit(1)

        elif response.status_code == 429:
            print("Rate limit exceeded! Waiting 30 seconds before retrying...")
            time.sleep(30)
        else:
            print("Mistral API Error:", response.json())

        attempts += 1

    return None


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
        print("Generated Content:\n", content)
        post_to_mastodon(f"Word of the Day:\n\n{content}")
    else:
        print("No new word found. Nothing will be posted.")
