import streamlit as st
import requests
from bs4 import BeautifulSoup
import trafilatura
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate


from langchain.chains import LLMChain

from langchain_groq import ChatGroq


url = ''
# Function to get the page source
def fetch_page_source(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception as e:
        return str(e)

# Function to extract links from a page
def extract_links(page_source):
    global url
    st.write(url)
    soup = BeautifulSoup(page_source, 'html.parser')
    links = []
    # Find all anchor tags with href
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        # Filter out non-HTTP or relative links
        if link.startswith('http') or link.startswith('/'):
            # Handle relative URLs by converting them to absolute
            if link.startswith('/'):
                link = f"{url}{link}"
            links.append(link)
        if len(links) == 10:  # Stop when 5 links are found
            break
        links = list(set(links))
        
    return links

# Function to extract text content from a page using Trafilatura
def extract_text(url):
    page_source = fetch_page_source(url)
    if page_source:
        text = trafilatura.extract(page_source)
        return text if text else "No readable content found."
    return "Error fetching the page."

# Streamlit UI
def main():
    global url
    st.title("Web Scraper and Content Extractor")

    # Input URL
    url = st.text_input("Enter URL to scrape:")

    content = ''

    if url:
        
        GROQ_API_KEY = st.secrets['GROQ_API_KEY']
        llm = ChatGroq(temperature=0.8, groq_api_key=GROQ_API_KEY, model_name="llama3-70b-8192")

        # st.write(f"Fetching links from: {url}")

        # Get the page source from the URL
        page_source = fetch_page_source(url)

        if page_source:
            # Extract links from the page
            links = extract_links(page_source)
            st.write(links)

            if links:
                st.write("Found the following links:")
                for i, link in enumerate(links, 1):
                    st.write(f"{i}. {link}")

                st.write("Extracting text from these pages...")
                for link in links:
                    st.write(f"Fetching content from: {link}")
                    page_text = extract_text(link)
                    st.write(f"Content from {link}:")
                    st.write(page_text[:1000])  # Display the first 1000 characters
                    content = content + '\n' + page_text[:1000]
                    # st.write("\n\n")
                # st.write(f'Final content - {content}')

                prompt = f"""
                You are an expert in summarizing the {content} provided to tell what a wesbite is about.
                Detect the language of {content}.  So, summarize the {content} in English language
                and return the result as to what the website is about.'
                """

                
                template = PromptTemplate(
                input_variables=["content"],
                template=prompt,
            )

            # Create the LLMChain to manage the model and prompt interaction
                llm_chain = LLMChain(prompt=template, llm=llm)
                response = llm_chain.invoke({
                    "content" : content

                })          
                    
                st.write("Summary is..")
                st.write(response["text"])


            else:
                st.write("No links found on the provided page.")
        else:
            st.write("Error fetching the page. Please check the URL and try again.")

if __name__ == "__main__":
    main()
