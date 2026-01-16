import datetime
import requests
import os
import time
from mastodon import Mastodon
import subprocess

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
HISTORY_FILE = "history.txt"

def load_history():
    """Loads past words from history.txt to prevent duplicates."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            past_words = [l.strip() for l in f if l.strip()][-100:]
    except FileNotFoundError:
        past_words = []

def save_word(word):
    """Saves the new word to history.txt and commits it to GitHub."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(f"{word}\n")

    try:
        subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions Bot"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", HISTORY_FILE], check=True)
        subprocess.run(["git", "commit", "-m", f"Updated history with new word: {word}"], check=True)
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError:
        print("Git commit failed, but execution will continue.")

def is_valid_italian_word(word):
    url = f"https://it.wiktionary.org/w/api.php?action=query&titles={word}&format=json"
    try:
        r = requests.get(url, timeout=5)
        pages = r.json().get("query", {}).get("pages", {})
        return not any("missing" in page for page in pages.values())
    except Exception as e:
        print("Wiktionary check failed:", e)
        return True

def generate_word():
    """Fetches a random Italian word, ensuring uniqueness and validity."""
    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY is not set! Exiting.")
        exit(1)

    history = load_history()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        past_words = [l.strip() for l in f if l.strip()][-100:]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
    As of {timestamp}, generate a random Italian word that is commonly used but not overly basic.
    Do NOT use these words: {', '.join(past_words)}

    The word MUST be different from previous outputs and MUST be a real word in the Italian language.

    If the word is a verb, the example sentence MUST use the verb exactly as it was generated.
    If the word is NOT a verb, the sentence MUST use the word itself (not a related verb or derivative).
    The generated word needs to be reported in the sentence as is.

    Format the response exactly as follows:

    Word: [Italian word]

    Example sentence:
    "[Example sentence in Italian using that word exactly]"

    Translation:
    "[English translation]"

    #Italian #LearnItalian #ItalianWord #Italy #Language

    Ensure the output follows this exact format with line breaks and no extra text.
    """

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    attempts = 0
    max_attempts = 5

    while attempts < max_attempts:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json={"model": "mistral-small","messages": [{"role": "user", "content": prompt}],"temperature": 0.8
                 }
        )

        if response.status_code == 200:
            json_response = response.json()
            print("Full Mistral API JSON Response:", json_response)

            content = json_response.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            print("Extracted Content from API:\n", content)

            lines = [line.strip() for line in content.split("\n") if line.strip()]

            word = None
            for i, line in enumerate(lines):
                if line.lower().startswith("word:"):
                    parts = line.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        word = parts[1].strip()
                    elif i + 1 < len(lines):
                        word = lines[i + 1].strip()
                    break

            if word:
                if word not in past_words:
                    if is_valid_italian_word(word):  # Check if word is real
                        save_word(word)
                        return content
                    else:
                        print(f"Invalid Italian word ({word}). Retrying...")
                else:
                    print(f"Duplicate word ({word}). Retrying...")
            else:
                print("Invalid response format. Retrying...")

        elif response.status_code == 401:
            print("ERROR: Unauthorized! Check if your MISTRAL_API_KEY is correct.")
            exit(1)

        elif response.status_code == 429:
            print("Rate limit exceeded! Waiting 60 seconds before retrying...")
            time.sleep(60)
            continue 
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
        print("Failed after retries — API never returned a valid response.")
