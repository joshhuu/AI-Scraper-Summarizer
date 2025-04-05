import time
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Global cache for scraped data
cache = {}

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
    data = {"title": title, "description": description, "main_content": main_content, "links": links}
    cache[url] = data
    time.sleep(2)
    return data

def get_summary_template(format_type):
    templates = {
        "paragraph": """
            Provide a concise summary in one clear paragraph.
        """,
        "bullet_points": """
            Provide a summary in 5-7 bullet points, each highlighting a key aspect of the website.
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
            Include 5-7 key aspects of the website.
        """,
        "detailed": """
            Provide a comprehensive summary with the following sections:
            - Overview
            - Key Features
            - Target Audience
            - Main Offerings
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
You are an AI that summarizes websites. Your task is to analyze the homepage of a website and generate a summary of its purpose, key content, and offerings.
{summary_instruction}

Website Title: {{title}}
Meta Description: {{description}}
Main Page Content: {{main_content}}

Here are some key links found on the site:
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
    return {"title": title, "description": description, "main_content": main_content, "links": links}

def main():
    url = input("Enter the website URL or 'manual' for manual content: ").strip()

    if url.lower() == 'manual':
        content = input("Enter the content to summarize: ").strip()
        site_data = process_manual_content(content)
    else:
        site_data = scrape_hyperlinks(url)
        if not (isinstance(site_data, dict) and site_data.get("links")):
            print(f"Error processing URL: {site_data}")
            return

    format_type = input("Enter the summary format (paragraph, bullet_points, emoji, table, detailed): ").strip() or "paragraph"

    # Initialize the LLM instance
    llm_instance = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        api_key=os.getenv('GOOGLE_API_KEY')
    )
    dummy_chain = LLMChain(llm=llm_instance, prompt=PromptTemplate(input_variables=["title", "description", "main_content", "links"], template=""))

    try:
        summary = summarize_website(site_data, dummy_chain, format_type=format_type)
        print("\nGenerated Summary:")
        print(summary)
    except Exception as e:
        print(f"Error generating summary: {e}")

if __name__ == "__main__":
    main()
