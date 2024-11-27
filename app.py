import os
import pandas as pd
import re
import unicodedata
import streamlit as st
import requests
from io import BytesIO
from urllib.parse import urlparse
import logging
import json
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to clean text
def clean_text(text):
    if not isinstance(text, str):
        return text
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if c.isprintable())
    text = re.sub(r'\(TM\)', '', text)
    text = re.sub(r'â€', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Function to parse pasted URLs
def parse_pasted_urls(urls_text):
    urls = re.split(r'[,\n\s]+', urls_text)
    return [url.strip() for url in urls if url.strip()]

# Function to validate URLs
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Function to fetch content using Jina Reader API
def fetch_content_jina(url, headers=None):
    # Directly append the raw URL without encoding
    jina_read_url = f"https://r.jina.ai/{url}"

    try:
        response = requests.get(jina_read_url, headers=headers, timeout=30)
        response.raise_for_status()
        # Assuming the response is in text format
        return response.text if response.text else "n/a"
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred for {url}: {http_err}")
        logger.error(f"Response Content: {http_err.response.text}")
        return "n/a"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return "n/a"

# Function to get OpenAI response
def get_openai_response(user_message):
    # OpenAI API Call (Copied exactly from Script 2)
    import streamlit as st
    from openai import OpenAI

    # Initialize OpenAI client
    try:
        openai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    except Exception as e:
        st.error("Failed to initialize OpenAI client. Please make sure you've set up the OpenAI API key in your Streamlit secrets.")
        st.stop()

    # OpenAI model and system message
    model = "ft:gpt-4o-mini-2024-07-18:raptive-nonprod:aug-coneval-v2-w:AEDc7Xng"  # Using the specified finetuned GPT-4o model
    system_message = """
    You are a helpful assistant that helps to analyze the content as winner, loser or neutral content.
    """

    chat_completion = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )
    return chat_completion.choices[0].message.content

# Streamlit App
def main():
    st.title("🔗 Webpage Scraper and GPT-4o Processor")

    # Display the accuracy table
    st.subheader("📊 Model Accuracy by Vertical")
    data = {
        'Vertical': [
            'food', 'clean', 'gaming', 'crafts', 'womens', 'home', 'family',
            'pets', 'travel', 'deals', 'mens', 'personal', 'tech', 'education',
            'beauty', 'lifestyle', 'business', 'green', 'arts', 'history',
            'science', 'entertainment', 'sports', 'wedding', 'professional',
            'health', 'hobbies', 'news', 'Overall'
        ],
        'aug-coneval-v2-w (%)': [
            85.07, 85.00, 80.07, 76.70, 75.28, 74.89, 74.48, 71.90, 70.57,
            67.76, 64.42, 63.97, 63.56, 63.16, 62.92, 62.64, 60.98, 60.58,
            60.45, 58.97, 58.72, 56.19, 53.47, 52.38, 51.05, 50.69, 50.49,
            49.90, 65.21
        ]
    }
    df_accuracy = pd.DataFrame(data)
    st.table(df_accuracy)

    # Initialize session state for failed URLs
    if 'failed_urls' not in st.session_state:
        st.session_state.failed_urls = []

    # URL input
    st.subheader("🖊️ Enter a URL to Process")
    manual_url = st.text_input("Enter a URL")

    # Button to start processing
    if st.button("🚀 Process URL"):
        if not manual_url:
            st.error("❌ Please enter a URL.")
            return

        if not is_valid_url(manual_url):
            st.error("❌ The entered URL is invalid.")
            return

        # Fetch content using Jina Reader API
        scraped_content = fetch_content_jina(manual_url)

        if scraped_content == "n/a":
            st.error(f"❌ Failed to fetch content for URL: {manual_url}")
            return

        # Display scraped content
        st.subheader("📝 Scraped Content")
        st.markdown(scraped_content)

        # Pass the content to GPT-4o model
        st.subheader("🤖 GPT-4o Model Response")
        response = get_openai_response(scraped_content)
        st.markdown(response)

if __name__ == "__main__":
    main()
