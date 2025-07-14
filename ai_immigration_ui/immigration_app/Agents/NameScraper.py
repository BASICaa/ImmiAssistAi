import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from pydantic_ai import Agent, ModelRetry
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Union, List, Optional
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import os
from dotenv import load_dotenv
import json
import ollama
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .Classes import output_agent
import datetime
from .logging_config import AppLogger
import logfire
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")

logger = AppLogger().get_logger()

print("Debug: Environment loaded")

class InfoTemplate(BaseModel):

    name: str = Field(description="The name of user")
    age: Union[int, str] = Field(description="The age of user")
    current_country: str = Field(description="The current location of user")
    reason_for_immigration: Union[Dict[str, Union[list, str]], str] = Field(description="The reason for immigration of user")
    target_country: str = Field(description="The target location of user")

    target_job: Union[Dict[str, Union[list, str]], str] = Field(description="if user wants to immigrate for job: The target job of user")
    experience: Union[Dict[str, Union[list, str]], str] = Field(description="User Experiences he has")

    target_education_field: Union[Dict[str, Union[list, str]], str] = Field(description="if user wants to immigrate for Education: The target field of study")
    previous_degrees: Union[Dict[str, Union[list, str]], str] = Field(description="Previous academic degrees and qualifications obtained by the user")
    target_education_degree: Union[Dict[str,str], str] =  Field(description="Target Degree the user want to apply for")
    target_position: Union[Dict[str,str], str] =  Field(description="Target Position the user want to apply for")
    language_proficiency: Union[Dict[str, Union[list, str, float]], str] = Field(description="User IELTS or Toffle or any kind of related test Score")

    financial_status: Union[Dict[str, Union[list, str]], str] = Field(description="Details about the user's financial means to support themselves during the immigration process")

    family_ties: Union[Dict[str, Union[list, str]], str] = Field(default=None, description="Information about family members in the target country, if any")
    
    health_status: Union[Dict[str, Union[list, str]], str] = Field(default=None, description="General health condition and any pertinent medical information")
    
    criminal_record: Union[Dict[str, Union[list, str]], str] = Field(default=None, description="Information regarding any criminal history")

class Job_or_University_Search(BaseModel):
    Job_or_Education: str = Field(description="The job or Education field that the user wants to search for")
    Location: str = Field(description="The location of the job or university")
    Degree_or_position: str = Field(description="Target degree or position the user want to take")
    Reason: str = Field(description="The reason for immigration of user")


class SearchResult(BaseModel):
    List_of_OverllExtraactednames: list[str] = Field(
        description="The list of all extracted names (company or university)"
    )
    total_results: int = Field(
        description="The total number of results found"
    )
    File_name: str = Field(description="The name of the file to save the extracted names")

class LLM_extracted_list(BaseModel):
    LLM_Extracted_list: list[str] = Field(
        description="The List of searched names Extracted by llm"
    )


Name_Scraper_Prompt = """
You are an Name Scraper Agent responsible for managing searches for education or job opportunities in specific countries based on user data.

Task Flow:
1. Validate Input Data:
   - Check if Ready_to_use_data.json exists and contains valid data
   - If no data exists, return "No data found, please provide data first"
   - Validate the data structure and required fields

2. Determine Search Type:
   - Based on the Reason_for_immigration field, determine if this is a job or education search
   - Extract relevant search parameters (field of study, job title, location, etc.)

3. Perform Search:
   - Use the appropriate search parameters to find up to 100 relevant opportunities
   - For education searches: focus on universities and programs
   - For job searches: focus on companies and positions
   - Handle any errors or rate limiting appropriately

4. Format and Return Results:
   - Return results in SearchResult format {SearchResult}

Error Handling:
- If data validation fails, return specific error messages
- If search fails, return appropriate error messages
- If partial results are obtained, indicate this in the response
"""
openai_model = OpenAIModel('gpt-4.1', provider=OpenAIProvider(api_key=os.getenv("Sub_Agent_Key")))


Name_Scraper_Agent = Agent(model= openai_model,
                            system_prompt=Name_Scraper_Prompt,
                            model_settings={"timeout": 5})
class BodyExtract(BaseModel):
    Extracted_names: List[str] = Field(
        description="Every distinct university or company name found in the snippet"
    )

logfire.configure()
logfire.instrument_pydantic_ai(Name_Scraper_Agent)

Extractor_prompt = """
You are an expert entity extraction AI. Your primary task is to identify and extract the full names of universities or companies from the provided text snippet(Depends on the {Immi_Reason}). Focus solely on extracting organizational names.
follow these steps:
 1. Analyze the Received HTML format {body}
 2. Extract organization Names (if {Immi_Reason} is job related. Then extract companies and job oportunities. But if it is Education related. Extract Universities)
 3. Compare the extracted names and names within {List_of_SearchResult}
    - If extracted name was not in list the add it to the list
 4. Return **ONLY** a single JSON object. This object must contain a single key named "Extracted_names", and its value must be a JSON list of strings, where each string is a unique university or company name found.

Example of the expected JSON format:
```json
{{
  "Extracted_names": ["Example University Name", "Another Example Inc.", "Technical University Example"]
}}

"""


@Name_Scraper_Agent.tool_plain
def check_data() -> Job_or_University_Search:
    """
    Load Ready_to_use_data.json which contain needed info and validate into Job_or_University_Search.
    """
    logger.debug("Starting check_data tool")
    path = os.path.join(DATA_DIR, "Ready_to_use_data.json")
    
    with open(path, "r") as file:
        data = json.load(file)
        if not data:
            raise ModelRetry("No data found, please provide data first")
    
    recovered_data = {
        "Job_or_Education": list(data["target_education_field"].values())[0] if isinstance(data["target_education_field"], dict) else data["target_education_field"] if "education" in data["reason_for_immigration"].lower() else data["target_job"],
        "Location": data["target_country"],
        "Degree_or_position": data["target_education_degree"] if "education" in data["reason_for_immigration"].lower() else data["target_position"],
        "Reason": data["reason_for_immigration"]
    }
    logger.debug("check_data completed. Recovered data:", recovered_data)
    return Job_or_University_Search.model_validate(recovered_data)


@Name_Scraper_Agent.tool_plain
def Searching_Job_or_University(data: Job_or_University_Search) -> output_agent:
    """
    Fetch and Scrap sites for Universities based on the query which is going to be generated
    """
    logger.debug("Starting Searching_Job_or_University tool")
    logger.debug(f"\nDebug: Input data: {data}")
    Extracted_names = []
    
    try:
        path = os.path.join(DATA_DIR, "SitesScrapingDic.json")
    
        with open(path, "r") as file:
            sites_scraping_list = json.load(file)
            logger.debug("\nDebug: Loaded sites scraping list")
            
        country_data = None
        for country_dict in sites_scraping_list:
            if data.Location in country_dict:
                country_data = country_dict[data.Location]
                break
                
        if not country_data:
            raise ValueError(f"No configuration found for country: {data.Location}")
        
        logger.debug("\nDebug: Found country data:", country_data)
        page = 1
        while len(Extracted_names) < 4:
            url = URl_fixer(country_data, page)
            body = scrape_site(url)
            if body is None:
                raise ValueError(f"Failed to retrieve {url}")
            
            prompt_with_schma = Extractor_prompt.format(body=body, List_of_SearchResult=Extracted_names, Immi_Reason=data.Reason)
            new_names = LLM_extractor(prompt_with_schma)
            for name in new_names.LLM_Extracted_list:
                if name not in Extracted_names:
                    Extracted_names.append(name)
            page += 1
        logger.debug(f"\nDebug: Extracted names: {Extracted_names}")
        Extracted_names = Extracted_names[:4]
        File_name = f"{data.Reason}_{data.Job_or_Education}_{data.Degree_or_position}_{data.Location}_Extracted_names.json"
        save_extracted_names(File_name, Extracted_names)
        logger.debug("\nDebug: Searching_Job_or_University completed. Total names found:", len(Extracted_names))
        return output_agent(
            request="Searching_Job_or_University",
            outputs_recieved=json.dumps({
                "List_of_OverllExtraactednames": Extracted_names,
                "total_results": len(Extracted_names),
                "File_name": File_name
            })
        )
        
    except Exception as e:
        logger.debug("\nDebug: Error in Searching_Job_or_University:", str(e))
        return output_agent(request="Searching_Job_or_University", outputs_recieved=SearchResult.model_validate({"List_of_OverllExtraactednames": [], "total_results": 0, "File_name": ""}))

def setup_selenium_driver():
    """Set up a headless Chrome browser using Selenium."""
    logger.debug("Setting up Selenium driver")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    logger.debug("Selenium driver setup completed")
    return driver

def scrape_site(url:str):
    logger.debug(f"\nDebug: Starting to scrape site: {url}")
    driver = setup_selenium_driver()

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = ' '.join(text_content.split())
        logger.debug("\nDebug: Site scraping completed successfully")
        return text_content

    except Exception as e:
        logger.debug("\nDebug: Error in scrape_site:", str(e))
        return None

    finally:
        driver.quit()
    
def LLM_extractor(prompt_with_schma):
    logger.debug("Starting LLM extraction")
    try:
        logger.debug(f"[Timestamp] ollama.chat started at: {datetime.datetime.now()}")
        response = ollama.chat(
            model="magistral:latest",
            messages=[{"role": "system", "content": Extractor_prompt}, {"role": "user", "content": prompt_with_schma}]
        )
        logger.debug(f"[Timestamp] ollama.chat ended at: {datetime.datetime.now()}")
        content = response.message['content'].strip()
        
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```|(\{[\s\S]*?\})", content)
        if match:
            json_str = match.group(1) or match.group(2)
            try:
                json_data = json.loads(json_str)
                data_extracted = BodyExtract.model_validate(json_data)
                logger.debug("\nDebug: LLM extraction completed successfully")
                return LLM_extracted_list.model_validate({"LLM_Extracted_list": data_extracted.Extracted_names})
            except ValidationError:
                logger.debug("\nDebug: Validation error in LLM extraction")
                return []
        else:
            logger.debug("\nDebug: No JSON found in LLM response")
            return []
    except Exception as e:
        logger.debug("\nDebug: Error in LLM extraction:", str(e))
        return []

def save_extracted_names(file_name: str, data: list) -> None:
    """Save extracted names to a JSON file in the Data directory."""
    logger.debug("Saving extracted names to file:", file_name)
    logger.debug("\nDebug: Data to save:", data)
    json_content = json.dumps(data, indent=4)
    os.makedirs("Data", exist_ok=True)
    with open(os.path.join("Data", file_name), "w") as file:
        file.write(json_content)
    logger.debug("\nDebug: Names saved successfully")

def URl_fixer(data:dict, page):
    logger.debug("Fixing URL for page:", page)
    logger.debug("\nDebug: Input data:", data)
    FieldName = ((data['field']['Name']).replace(" ",data['space']))
    
    if data['Order'] == 1:
        url = f"https://{data['site']}?{data['field']['Parameter']}={FieldName}&{data['degree']['Parameter']}={data['degree']['Name']}&page={page}"
    else:
        url = f"https://{data['site']}?{data['degree']['Parameter']}={data['degree']['Name']}&{data['field']['Parameter']}={FieldName}&page={page}"
    
    logger.debug("URL fixed:", url)
    return url
