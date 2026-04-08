import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Key found: {bool(key)}")
if key:
    print(f"Key preview: {key[:4]}...{key[-2:]}")

paper = {
    "title": "Test Paper Title",
    "authors": ["Author One"],
    "abstract": "This is a test abstract about artificial intelligence."
}

def test_summary():
    if not key:
        return
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("Sending prompt to Gemini...")
        response = model.generate_content("Say 'Hello, I am working' in 5 sections: **PROBLEM:**, **SOLUTION:**, **RESULTS:**, **LIMITATIONS:**, **IMPACT:**")
        print("Response received:")
        print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

test_summary()
