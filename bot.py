import requests
import os

# Load API Key from environment variables
API_KEY = os.getenv("MISTRAL_API_KEY")

def generate_word():
    prompt = "Generate a random Italian word, an example sentence using it, and its English translation."
    headers = {
        "Authorization": f"Bearer {API_KEY}",
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

if __name__ == "__main__":
    word = generate_word()
    print(word)  # Print to check output (optional)
