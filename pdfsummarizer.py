import time
import os
import requests
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from io import BytesIO
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Global cache for scraped data
cache = {}

def scrape_pdf(url):
    if url in cache:
        print("Using cached PDF data...")
        return cache[url]
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Failed to retrieve content: {e}"

    # Extract text from PDF
    pdf = PdfReader(BytesIO(response.content))
    text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Cache the result
    data = {"content": text}
    cache[url] = data
    time.sleep(2)
    return data

def get_summary_template(format_type):
    templates = {
        "paragraph": """
            Provide a concise summary in one clear paragraph.
        """,
        "bullet_points": """
            Provide a summary in 5-7 bullet points, each highlighting a key aspect of the PDF.
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
            Include 5-7 key aspects of the PDF.
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

def summarize_pdf(pdf_data, llm_chain, format_type="paragraph"):
    content = pdf_data["content"]

    summary_instruction = get_summary_template(format_type)

    prompt_template = PromptTemplate(
        input_variables=["content"],
        template=f"""
You are an AI that summarizes PDF documents. Your task is to read the document's content and generate a summary of its purpose, key content, and findings.
{summary_instruction}

PDF Content: {{content}}

Based on this content, provide the summary in the requested format.
"""
    )

    llm_chain = LLMChain(llm=llm_chain.llm, prompt=prompt_template)
    summary = llm_chain.run(content=content)
    return summary

def main():
    url = input("Enter the PDF URL: ").strip()

    if not url:
        print("No URL provided. Exiting.")
        return

    # Scrape the PDF content
    pdf_data = scrape_pdf(url)
    if not isinstance(pdf_data, dict) or not pdf_data.get("content"):
        print(f"Error processing PDF: {pdf_data}")
        return

    format_type = input("Enter the summary format (paragraph, bullet_points, emoji, table, detailed): ").strip() or "paragraph"

    # Initialize the LLM instance
    llm_instance = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        api_key=os.getenv('GOOGLE_API_KEY')
    )
    dummy_chain = LLMChain(llm=llm_instance, prompt=PromptTemplate(input_variables=["content"], template=""))

    try:
        summary = summarize_pdf(pdf_data, dummy_chain, format_type=format_type)
        print("\nGenerated Summary:")
        print(summary)
    except Exception as e:
        print(f"Error generating summary: {e}")

if __name__ == "__main__":
    main()
