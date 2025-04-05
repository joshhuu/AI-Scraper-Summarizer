import time
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from io import BytesIO
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global cache for scraped data
cache = {}

def extract_pdf_text(url):
    response = requests.get(url)
    pdf = PdfReader(BytesIO(response.content))
    # Extract text from each page (ignore pages that return None)
    text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text() is not None])
    return text

def scrape_pdf(url):
    # Check if the URL ends with '.pdf' and process accordingly.
    if url.endswith('.pdf'):
        text = extract_pdf_text(url)
        # Build a data structure similar to HTML scraping so that the summarizer works uniformly.
        return {
            "title": "PDF Document",
            "description": "Extracted PDF content",
            "main_content": text,
            "links": [],
            "type": "pdf"
        }
    else:
        # Fallback to the HTML scraper if not a PDF
        return scrape_hyperlinks(url)

def scrape_hyperlinks(url):
    if url in cache:
        print("Using cached data...")
        return cache[url]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Failed to retrieve content: {e}"
    
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title').get_text(strip=True) if soup.find('title') else "No Title"
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    description = meta_desc['content'] if meta_desc else "No meta description available."
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 30]
    main_content = " ".join(paragraphs[:5])
    
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True) or "No Text"
        if "privacy" in href.lower() or "terms" in href.lower() or "login" in href.lower():
            continue
        links.append({'text': text, 'url': href})
    
    links = links[:20] if len(links) > 20 else links
    data = {"title": title, "description": description, "main_content": main_content, "links": links, "type": "html"}
    cache[url] = data
    time.sleep(2)
    return data

def get_summary_template(format_type):
    templates = {
        "paragraph": """
            Provide a concise summary in one clear paragraph.
        """,
        "bullet_points": """
            Provide a summary in 5-7 bullet points, each highlighting a key aspect.
            Format each point with a • symbol at the start.
        """,
        "emoji": """
            Provide a summary using emojis followed by brief descriptions.
            Use 5-7 key points, each starting with a relevant emoji.
            Example format:
            🎯 Main purpose: [description]
            💡 Key feature: [description]
        """,
        "table": """
            Provide a summary in a markdown table format with two columns:
            | Aspect | Description |
            |--------|-------------|
            Include 5-7 key aspects.
        """,
        "detailed": """
            Provide a comprehensive summary with these sections:
            - Overview
            - Key Features
            - Methodology/Key Findings
            - Notable Elements
            
            Use clear headings and detailed explanations for each section.
        """
    }
    return templates.get(format_type, templates["paragraph"])

def summarize_website(site_data, llm_chain, format_type="paragraph"):
    title = site_data["title"]
    description = site_data["description"]
    main_content = site_data["main_content"]
    links = site_data["links"]
    
    links_info = "\n".join([f"Text: {link['text']}, URL: {link['url']}" for link in links])
    summary_instruction = get_summary_template(format_type)
    
    prompt_template = PromptTemplate(
        input_variables=["title", "description", "main_content", "links"],
        template=f"""
You are an AI that summarizes content. Analyze the following information and generate a summary of its purpose, key content, methodology, and key findings.
{summary_instruction}

Title: {{title}}
Description: {{description}}
Main Content: {{main_content}}

Additional Links:
{{links}}

Based on this information, provide the summary in the requested format.
"""
    )
    
    llm_chain = LLMChain(llm=llm_chain.llm, prompt=prompt_template)
    summary = llm_chain.run(title=title, description=description, main_content=main_content, links=links_info)
    return summary

def process_manual_content(content):
    soup = BeautifulSoup(content, 'html.parser')
    title = soup.find('title').get_text(strip=True) if soup.find('title') else "No Title"
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    description = meta_desc['content'] if meta_desc else "No meta description available."
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 30]
    main_content = " ".join(paragraphs[:5])
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True) or "No Text"
        if "privacy" in href.lower() or "terms" in href.lower() or "login" in href.lower():
            continue
        links.append({'text': text, 'url': href})
    links = links[:20] if len(links) > 20 else links
    return {"title": title, "description": description, "main_content": main_content, "links": links, "type": "html"}

# Initialize the LLM instance
llm_instance = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=os.getenv('GOOGLE_API_KEY')
)
dummy_chain = LLMChain(
    llm=llm_instance,
    prompt=PromptTemplate(input_variables=["title", "description", "main_content", "links"], template="")
)

@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.json
    if not data.get("accept_disclaimer"):
        return jsonify({"error": "You must accept the disclaimer to use this tool."}), 400

    input_type = data.get("input_type")
    format_type = data.get("format", "paragraph")
    
    try:
        if input_type == "manual":
            content = data.get("manual", "")
            site_data = process_manual_content(content)
        else:
            url = data.get("url", "").strip()
            # Check if the URL is a PDF
            if url.endswith('.pdf'):
                site_data = scrape_pdf(url)
            else:
                site_data = scrape_hyperlinks(url)
                if not (isinstance(site_data, dict) and site_data.get("links")):
                    return jsonify({"error": f"Error processing URL: {site_data}"}), 400
        
        summary = summarize_website(site_data, dummy_chain, format_type=format_type)
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
