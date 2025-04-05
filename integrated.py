from flask import Flask, request, jsonify
from scrape import scrape_hyperlinks
from pdfsummarizer import scrape_pdf
from summarizer import scrape_hyperlinks
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/summarize/webpage', methods=['POST'])
def summarize_webpage():
    data = request.json
    url = data.get("url")
    format_type = data.get("format", "paragraph")
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    site_data = scrape_hyperlinks(url)
    if isinstance(site_data, str):
        return jsonify({"error": site_data}), 400
    
    summary = summarize_content(site_data, format_type)
    return jsonify({"summary": summary})

@app.route('/summarize/pdf', methods=['POST'])
def summarize_pdf():
    data = request.json
    url = data.get("url")
    format_type = data.get("format", "paragraph")
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    pdf_data = scrape_pdf(url)
    if isinstance(pdf_data, str):
        return jsonify({"error": pdf_data}), 400
    
    summary = summarize_content(pdf_data, format_type)
    return jsonify({"summary": summary})

@app.route('/summarize/manual', methods=['POST'])
def summarize_manual():
    data = request.json
    content = data.get("content")
    format_type = data.get("format", "paragraph")
    
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    summary = summarize_content({"content": content}, format_type)
    return jsonify({"summary": summary})

if __name__ == '__main__':
    app.run(debug=True)
