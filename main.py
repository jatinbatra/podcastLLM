import os
import requests
import markdown2
from flask import Flask, request, render_template
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__, template_folder="templates")

DEEPSEEK_PROMPT = """Create a podcast summary in {format}. Structure it with:
- **Key Discussion Points** (in bullet points)
- **Noteworthy Quotes**
- **Main Takeaways**
- **Break paragraphs for readability**
- **Avoid long walls of text**

Transcript excerpt: {text}"""

SUMMARY_FORMATS = {
    "short": "a concise summary (1-minute read) with bullet points",
    "balanced": "a structured summary (5-minute read) with headings & key insights",
    "long": "a detailed, well-explained article (10-minute read) with analysis",
    "twitter": "a Twitter thread with short, engaging posts",
    "story": "a journalistic, engaging news-style article",
    "academic": "an academic-style analysis with citations"
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/summarize", methods=["POST"])
def summarize():
    youtube_url = request.form.get("youtube_url")
    summary_type = request.form.get("summary_type")

    video_id = extract_video_id(youtube_url)
    if not video_id:
        return "Invalid YouTube URL. Please try again."

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([t['text'] for t in transcript])[:5000]

        headers = {"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"}
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": DEEPSEEK_PROMPT.format(format=SUMMARY_FORMATS[summary_type], text=text)}]
            },
            timeout=120
        )

        if response.status_code == 200:
            raw_summary = response.json()['choices'][0]['message']['content']
            formatted_summary = format_summary(raw_summary)
            return render_template("summary.html", formatted_summary=formatted_summary)

        return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error: {e}"

def extract_video_id(youtube_url):
    if "youtu.be" in youtube_url:
        return youtube_url.split("/")[-1]
    elif "youtube.com/watch?v=" in youtube_url:
        return youtube_url.split("v=")[-1].split("&")[0]
    return None

def format_summary(raw_text):
    """Converts text into readable HTML with bullet points, bold headers, and spacing."""
    formatted_text = markdown2.markdown(raw_text)
    return formatted_text

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
