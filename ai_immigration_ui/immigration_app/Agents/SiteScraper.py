import os
from .Classes import output_agent
from pydantic_ai import Agent, ModelRetry, Tool, RunContext
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Union, List, Optional
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
import json
import ollama
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import re
import requests
import openai
import json
from pydantic import ValidationError
from pydantic_ai import ModelRetry
import datetime
from .logging_config import AppLogger
import logfire

load_dotenv()

# Ensure logger is defined at the top (after imports)
logger = AppLogger().get_logger()

Detail_Scraper_model_prompt = """
You are a detail scraper agent responsible for extracting data from websites.

Your workflow:
1. You will receive data in the `Name_SearchResult` format, which contains a list of organization names.
2. Divide the list of organization names into smaller chunks, each in the `Chunk_list` format.
3. Assign each chunk to the tool responsible for finding the official URLs of the organizations, returning results in the `Chunk_urls` format one by one and then each time you receive a chunk_urls pass it to the Scraping_data tool.
4. repeat the process until you chunked the whole list and scraped the data from all the organizations.
5. Save each `Scraped_data` result to a file named after the organization.
6. after scraping all of the chunks, read the `llm_extracted_data.json` file and return the data in the `output_agent` format.

repeat the process of chunking, url_finder and scraping_data until you have scraped the data from all the organizations.
Always follow this workflow and ensure that data is passed between steps using the specified formats.
"""

Detail_Scraper_model = OpenAIModel('o3-mini', provider=OpenAIProvider(api_key=os.getenv("Sub_Agent_Key")))

Detail_Scraper_Agent = Agent(Detail_Scraper_model, 
                        system_prompt=Detail_Scraper_model_prompt,
                        model_settings={"timeout": 5})

class Name_SearchResult(BaseModel):
    List_of_OverllExtraactednames: list[str] = Field(
        description="The list of all extracted names (company or university)"
    )
    total_results: int = Field(
        description="The total number of results found"
    )
    File_name: str = Field(description="The name of the file to save the extracted names")

class Chunk_list(BaseModel):
    Chunk_list: list[str] = Field(
        description="The list of Names to be scraped by one agent"
    )

class Chunk_urls(BaseModel):
    Chunk_urls: dict[str, str] = Field(
        description="The Dictionary of Organization and their Official Website"
    )
    programme_name: str = Field(description="The name of the programme to be scraped")
    degree_name: str = Field(description="The name of the degree to be scraped")

class Scraped_data(BaseModel):
    name: str
    requirements: str
    deadlines: str

class ScrapedDataList(BaseModel):
    items: list[Scraped_data]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CUSTOM_SEARCH_ENGINE_ID = os.getenv("GOOGLE_ID")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
Extractor_prompt = """
You are an expert entity extraction AI. Your primary task is to identify and extract the Deadline and Requirements from the provided text snippet.
follow these steps:
 1. Analyze the Received Data which is urls for deadlien and application and its contents which you need to analyze and extract the Deadline and Requirements from the contents in the:\n{body}
 2. Extract the Deadline and Requirements from the text snippet
 3. Return a Json whchi contain 3 keys name of the university, deadline and requirements

Example of the expected JSON format:
```json
{{
  "name": "Example University Name",
  "deadline": "A date or dates related to the deadline extracted from the content",
  "requirements": "A text related to the requirements extracted from the content"
}}

"""
def google_custom_search(query, num_results=3):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CUSTOM_SEARCH_ENGINE_ID,
        "q": query,
        "num": num_results,
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    results = response.json()
    items = results.get("items", [])
    return items

logfire.configure()
logfire.instrument_pydantic_ai(Detail_Scraper_Agent)

@Detail_Scraper_Agent.tool
def Divingding_data(ctx: RunContext[output_agent]) -> Chunk_list:
    logger.info("[Timestamp] Divingding_data started at: %s", datetime.datetime.now())
    list_of_names = ctx.deps.outputs_recieved.List_of_OverllExtraactednames
    logger.debug("\nDebug: Input context: %s", list_of_names)
    logger.info("[Timestamp] Divingding_data ended at: %s", datetime.datetime.now())
    return _chunk(list_of_names, 2)
    

@Detail_Scraper_Agent.tool_plain
def url_finder(TaskList: Chunk_list) -> Chunk_urls:
    logger.info("[Timestamp] url_finder started at: %s", datetime.datetime.now())
    urls = {}
    try:
        data = load_data()
        # Extract programme_name and degree_name safely
        programme_name = None
        degree_name = None
        if isinstance(data, dict):
            # Programme name logic
            if "Target_education_field" in data:
                if isinstance(data["Target_education_field"], dict):
                    programme_name = list(data["Target_education_field"].values())[0]
                else:
                    programme_name = data["Target_education_field"]
            elif "Target_job" in data:
                programme_name = data["Target_job"]
            else:
                programme_name = "Unknown"
            # Degree name logic
            degree_name = data.get("Target_education_degree", "Unknown")
        else:
            programme_name = "Unknown"
            degree_name = "Unknown"
    except Exception as e:
        logger.debug("\nDebug: Error loading data: %s", e)
        programme_name = "Unknown"
        degree_name = "Unknown"

    for org in TaskList.Chunk_list:
        try:
            query = f"{org} official university website for {programme_name} {degree_name}"
            search_results = google_custom_search(query, num_results=5)
            url_found = None
            for item in search_results:
                link = item.get("link", "")
                # Basic filter for university-like domains
                if any(domain in link.lower() for domain in ['.edu', '.ac.', 'university', 'uni-']):
                    url_found = link
                    break
            if not url_found and search_results:
                url_found = search_results[0].get("link", "Not found")
            if not url_found:
                url_found = "Not found"
            urls[org] = url_found
            logger.debug("\nDebug: Found URL for %s: %s", org, url_found)
        except Exception as e:
            logger.debug("\nDebug: Error finding URL for %s: %s", org, e)
            urls[org] = "Error"
            continue

    urls_model = Chunk_urls(
        Chunk_urls=urls,
        programme_name=programme_name,
        degree_name=degree_name
    )

    logger.debug("\nDebug: url_finder completed. Found URLs: %s", urls_model)
    logger.info("[Timestamp] url_finder ended at: %s", datetime.datetime.now())
    return urls_model

@Detail_Scraper_Agent.tool_plain
def Scraping_data(Urls_list:Chunk_urls) -> str:
    logger.info("[Timestamp] Scraping_data started at: %s", datetime.datetime.now())
    Urls_list = Chunk_urls.model_validate(Urls_list)
    logger.debug("\nDebug: Input Urls_list: %s", Urls_list)
    scraped_data_list = []
    for name, url in Urls_list.Chunk_urls.items():
        try:
            response = requests.get(url)
            html_data = response.text
            soup = BeautifulSoup(html_data, "html.parser")

            # Find all links
            all_links = soup.find_all(name="a")
            logger.debug("\nDebug: All links found on the page:")

            # Filter links that are related to deadlines and application requirements
            deadline_links = []
            application_links = []

            for link in all_links:
                link_text = link.get_text().lower()  # Get the text from each link and make it lowercase for easier matching
                if len(deadline_links) < 5:
                    if 'deadline' in link_text:
                        deadline_links.append(link.get('href'))
                if len(application_links) < 5:
                    if 'application' in link_text:
                        application_links.append(link.get('href'))

            # Print the extracted links for deadlines and application requirements
            logger.debug("\nDebug: Deadline-related links: %s", deadline_links)
            logger.debug("\nDebug: Application-related links: %s", application_links)

            # Additional scraping for the content on those pages can be added here if needed
            # For example, we can visit the deadline/application links and extract the relevant text:
            # Create a dictionary to store the scraped data
            Scraping_Htmls_data = {
                "deadlines": [],
                "requirements": []
            }

            # Scrape deadline information
            for deadline_link in deadline_links:
                deadline_url = requests.compat.urljoin(url, deadline_link)
                response = requests.get(deadline_url)
                deadline_soup = BeautifulSoup(response.text, "html.parser")
                deadline_text = deadline_soup.get_text()
                cleaned_deadline_text = clean_text(deadline_text)
                Scraping_Htmls_data["deadlines"].append({
                    "url": deadline_url,
                    "content": cleaned_deadline_text
                })

            # Scrape application requirements
            for app_link in application_links:
                app_url = requests.compat.urljoin(url, app_link)
                response = requests.get(app_url)
                app_soup = BeautifulSoup(response.text, "html.parser")
                app_text = app_soup.get_text()
                cleaned_app_text = clean_text(app_text)
                Scraping_Htmls_data["requirements"].append({
                    "url": app_url,
                    "content": cleaned_app_text
                })
            llm_extracted_data = LLM_extractor(name, Scraping_Htmls_data)
            logger.debug("\nDebug: LLM extracted data output: %s", llm_extracted_data)
            scraped_data_list.append(llm_extracted_data)
        except Exception as e:
            logger.debug("\nDebug: Error scraping %s from %s: %s", name, url, e)
            continue

    # Save to JSON file
    output_file = "llm_extracted_data.json"
    try:
        # Read existing data if file exists
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        # Append new data
        existing_data.extend([item.model_dump() for item in scraped_data_list])
        # Write back to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        logger.debug("\nDebug: Appended scraped data to %s", output_file)
    except Exception as e:
        logger.debug("\nDebug: Error saving data to %s: %s", output_file, e)
    logger.info("[Timestamp] Scraping_data ended at: %s", datetime.datetime.now())
    return "Data saved successfully"

@Detail_Scraper_Agent.tool_plain
def read_data() -> output_agent:
    logger.info("[Timestamp] read_data started at: %s", datetime.datetime.now())
    with open("llm_extracted_data.json", "r") as file:
        data = json.load(file)
    list_of_data_model = []
    for item in data:
        data_model = Scraped_data.model_validate(item)
        list_of_data_model.append(data_model)
    data_model_final = ScrapedDataList(items=list_of_data_model)
    output_data = output_agent(request="read_data", outputs_recieved=data_model_final.model_dump())
    output_data = output_agent.model_validate(output_data)
    logger.info("[Timestamp] read_data ended at: %s", datetime.datetime.now())
    return output_data

def clean_text(text_html):
    soup = BeautifulSoup(text_html, "html.parser")

    # 1. drop tags that never contain main text
    for tag in soup(["script", "style", "noscript", "iframe",
                     "header", "footer", "nav", "form", "aside"]):
        tag.decompose()

    # 2. if the site uses <main>, prefer it; else fall back to <body>
    container = soup.find("main") or soup.body or soup
    text = container.get_text(" ", strip=True)

    # 3. collapse whitespace and get rid of duplicates such as
    #    "jump to content" that appear on every page
    text = re.sub(r'\s+', ' ', text)
    noise_patterns = [
        r"jump to content.*?jump to footer",
        r"University of Stuttgart.*?close navigation",
    ]
    for pat in noise_patterns:
        text = re.sub(pat, " ", text, flags=re.I)

    return text.strip()

def load_data():
    path = os.path.join(DATA_DIR, "Ready_to_use_data.json")
    with open(path, "r") as file:
        data = json.load(file)
        if not data:
            raise ModelRetry("No data found, please provide data first")
    return data

def Creating_driver():
    """Create a headless Chrome browser using Selenium."""
    logger.debug("\nDebug: Setting up Selenium driver")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    logger.debug("\nDebug: Selenium driver setup completed")
    return driver

def _chunk(lst: list, n: int) -> list[list]:
    """Split a list into chunks of size n."""
    logger.debug("\nDebug: Chunking list into size: %s", n)
    logger.debug("\nDebug: Input list length: %s", len(lst))
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def LLM_extractor(name_org, Scraping_Htmls_data) -> Scraped_data:
    logger.debug("\nDebug: Starting LLM extraction (multi-content)")
    extracted_deadlines = []
    extracted_requirements = []
    rep_deadline = 0
    rep_requirements = 0
    
    for item in Scraping_Htmls_data.get("deadlines", []):
        rep_deadline += 1
        logger.debug("\nDebug: Repetition of deadlines: %s", rep_deadline)
        content = item.get("content", "")
        if content:
            char_counts_deadline = [len(item) for item in extracted_deadlines]
            total_chars_deadline = sum(char_counts_deadline)
            logger.debug("\n debug: content deadlines %s", content)
            # Count characters in list2, converting dicts to strings
            logger.debug("\nDebug: Total characters in deadlines: %s", total_chars_deadline)
            if total_chars_deadline > 1600:
                logger.debug("\nDebug: Total characters in deadlines: %s", total_chars_deadline)
                continue
            extracted = extract_from_content(content, "deadline")
            logger.debug("\nDebug: Extracted deadlines little bit:\n %s", extracted)
            if isinstance(extracted, list):
                extracted_deadlines.extend(extracted)
            elif isinstance(extracted, str):
                extracted_deadlines.append(extracted)
            logger.debug("\nDebug: Extracted deadlines: %s", extracted_deadlines)

    # Extract requirements
    for item in Scraping_Htmls_data.get("requirements", []):
        rep_requirements += 1
        logger.debug("\nDebug: Repetition of requirements: %s", rep_requirements)
        content = item.get("content", "")
        if content:
            char_counts_requirements = [len(str(item)) for item in extracted_requirements]
            total_chars_requirements = sum(char_counts_requirements)
            logger.debug("\n debug: content requirements %s", content)
            logger.debug("\nDebug: Total characters in requirements: %s", total_chars_requirements)
            if total_chars_requirements > 1600:
                logger.debug("\nDebug: Total characters in requirements: %s", total_chars_requirements)
                continue
            extracted = extract_from_content(content, "requirements")
            logger.debug("\nDebug: Extracted requirements little bit:\n %s", extracted)
            if isinstance(extracted, list):
                extracted_requirements.extend(extracted)
            elif isinstance(extracted, str):
                extracted_requirements.append(extracted)
            logger.debug("\nDebug: Extracted requirements: %s", extracted_requirements)

    # Aggregate results (simple join, can be improved)
    final_deadlines = "\n".join(set(extracted_deadlines))
    final_requirements = "\n".join(set(extracted_requirements))
    logger.debug("\nDebug: Final deadlines: %s", final_deadlines)
    logger.debug("\nDebug: Final requirements: %s", final_requirements)
    
    extracted_data = {
        "name": name_org,
        "requirements": "\n".join(extract_from_content(final_requirements, "requirements")) if isinstance(extract_from_content(final_requirements, "requirements"), list) else extract_from_content(final_requirements, "requirements"),
        "deadlines": "\n".join(extract_from_content(final_deadlines, "deadlines")) if isinstance(extract_from_content(final_deadlines, "deadlines"), list) else extract_from_content(final_deadlines, "deadlines")
    }
    extracted_data = Scraped_data.model_validate(extracted_data)
    logger.debug("\nDebug: LLM extraction completed successfully: %s", extracted_data)
    return extracted_data

def extract_from_content(content, content_type):
        prompt = f"""
        You are an expert entity extraction AI. Your primary task is to identify and extract the {content_type} from the provided text snippet.
        Analyze the following content and extract only the relevant {content_type} information in form of string. Return a JSON with a single key: '{content_type}'.
        Content:
        {content}
        Example:
        {{
        "{content_type}": "..."
        }}
        """
        try:
            logger.debug("[Timestamp] ollama.chat started at: %s", datetime.datetime.now())
            response = ollama.chat(
                model="magistral:latest",
                messages=[{"role": "system", "content": prompt}],
                options={"temperature": 0.1}
            )
            logger.debug("[Timestamp] ollama.chat ended at: %s", datetime.datetime.now())
            content_resp = response.message['content'].strip()
            match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```|(\{[\s\S]*?\})", content_resp)
            if match:
                json_str = match.group(1) or match.group(2)
                try:
                    json_data = json.loads(json_str)
                    return json_data.get(content_type, "")
                except Exception as e:
                    logger.debug("\nDebug: JSON decode error for %s: %s", content_type, e)
                    return ""
            else:
                logger.debug("\nDebug: No JSON found in LLM response for %s", content_type)
                return ""
        except Exception as e:
            logger.debug("\nDebug: Error in LLM extraction for %s: %s", content_type, e)
            return ""