import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import os
from dotenv import load_dotenv
from typing import Dict, Union, Optional, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from pydantic_ai import Agent, Tool, RunContext
import json
from openai import OpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import ollama
import re, string
import time
from .Classes import output_agent, ImmigrationProfileModel, ImmigrationProfileModelparse
import datetime
from .logging_config import AppLogger
import logfire
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")

# Ensure logger is defined at the top (after imports)
logger = AppLogger().get_logger()

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

class CommandGen(BaseModel):
    Command: str = Field(description="The command to be executed by the agent")
    Context: Union[str, InfoTemplate, dict] = Field(description="Additional context or information needed to execute the command")

system_prompt = """
you will be given a {ImmigrationProfileModel} of keys and the answers to the keys from user.
You will parse the {ImmigrationProfileModel} into {InfoTemplate} format.
answers should be clear and short
if the input is short, you should return the input itself.
if the input is long, you should return the parsed version of the input.
if the input has multi parts parse it into dictionary in json format.
if the input is adding new data, you should first give request for adding new data and then save the data.
*Dont add any additional text before or after the parsed string.
*All parsing should be base on the question
"""

def parser_with_llm(user_input: str) -> Union[Dict[str, str], str]:
    """
    Parse user input using an LLM to extract structured information
    """
    logger.debug("Starting parser_with_llm")
    logger.debug("Input user text:", user_input)
    logger.debug(f"[Timestamp] ollama.chat started at: {datetime.datetime.now()}")
    response = ollama.chat(
        model="magistral:latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
    )
    logger.debug(f"[Timestamp] ollama.chat ended at: {datetime.datetime.now()}")
    content = response.message['content'].strip()
    logger.debug("LLM response received:", content)
    try:
        extracted_json = re.search(r'\{[\s\S]*?\}', content)
        if extracted_json:
            logger.debug("JSON extracted successfully")
            return json.loads(extracted_json.group(0))
        else:
            logger.debug("No JSON found, returning content as is")
            return content
    except json.JSONDecodeError:
        logger.debug("JSON decode error")
        return {"error": "Failed to parse response"}

LLMParsedDict = Annotated[Union[Dict[str, Union[list, str]], str], BeforeValidator(parser_with_llm)]

openai_model = OpenAIModel('gpt-4.1', provider=OpenAIProvider(api_key=os.getenv("Sub_Agent_Key")))
Assistant_Agent_prompt ="""
You are a helpful assistant that executes actions by calling the appropriate tool based on the received command.

- If the command is to add new data, you MUST use the `request_adding_new_data` tool.
- If the command is to save new data, you MUST use the `save_new_data` tool.

Only call the single tool that directly corresponds to the command you were given. Do not chain multiple tool calls together.
"""
Assistant_Agent = Agent(openai_model, system_prompt=Assistant_Agent_prompt, model_settings={"timeout": 5})

logfire.configure()
logfire.instrument_pydantic_ai(Assistant_Agent)

@Assistant_Agent.tool_plain
def See_files() -> output_agent:
    """
    This tool will return the list of files in the Data folder
    """
    logger.info("[Timestamp] See_files started at: %s", datetime.datetime.now())
    files = os.listdir(DATA_DIR)
    logger.debug("See_files completed. Found files: %s", files)

    output_return = output_agent(request="See_files", outputs_recieved=files)

    logger.info("[Timestamp] See_files ended at: %s", datetime.datetime.now())
    return output_agent.model_validate(output_return)

@Assistant_Agent.tool
def load_data(ctx: RunContext[str]) -> output_agent:
    """
    This tool will load the data from the Data folder
    args:
    - filename: the name of the file to be loaded
    """
    logger.info("[Timestamp] load_data started at: %s", datetime.datetime.now())
    logger.debug("Input context:", ctx.deps)
    if not ctx.deps:
        raise ValueError("No filename provided to load_data. ctx.deps is None.")
    path = os.path.join(DATA_DIR, ctx.deps)
    with open(path, "r") as file:
        data = json.load(file)
        logger.debug("File loaded successfully")
        Data = InfoTemplate.model_validate(data)
        saving_data(Data, "Ready_to_use_data.json")
    logger.info("[Timestamp] load_data ended at: %s", datetime.datetime.now())
    return output_agent(request="load_data", outputs_recieved=Data.model_dump())
    
@Assistant_Agent.tool_plain
def request_adding_new_data() -> output_agent:
    """ If the user asked for adding new user first you will send the request"""
    logger.info("[Timestamp] request_adding_new_data started at: %s", datetime.datetime.now())
    output = output_agent(request="adding_new_data", outputs_recieved=None)
    logger.debug("adding_new_data completed successfully")
    logger.info("[Timestamp] request_adding_new_data ended at: %s", datetime.datetime.now())
    return output

@Assistant_Agent.tool
def save_new_data(ctx: RunContext[ImmigrationProfileModel]) -> output_agent:
    """
    if user asked for saving new data
    This tool saves the user's complete profile data, received from a form, to a JSON file.
    The user's name is used as the filename. The profile data comes from the context.
    """
    logger.info(f"[Timestamp] save_new_data tool started at: %s", datetime.datetime.now())
    
    try:
        with open('output.json', 'r') as json_file:
            data = json.load(json_file)
        
        profile_data = ImmigrationProfileModelparse.model_validate(data)
        
        info_to_save = InfoTemplate.model_validate(profile_data.model_dump())

        filename = "Ready_to_use_data.json"
        result_message = saving_data(info_to_save, filename)
        
        logger.info(f"save_new_data completed. {result_message}")
        logger.info("[Timestamp] save_new_data tool ended at: %s", datetime.datetime.now())
        
        return output_agent(request="save_new_data", outputs_recieved=info_to_save.model_dump())

    except Exception as e:
        logger.error(f"Failed to validate data against InfoTemplate: {e}", exc_info=True)
        return output_agent(request="error", outputs_recieved="Data structure mismatch after parsing.")

def saving_data(data: InfoTemplate, file_name: str) -> str:
    """
    Saves the data in the Data folder with the given file name.
    """
    logger.debug(f"Starting saving_data for file: {file_name}")
    json_content = json.dumps(data.model_dump(), indent=4)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, file_name), "w") as file:
        file.write(json_content)
    # Also update the 'Ready_to_use_data.json' to reflect the latest profile
    with open(os.path.join(DATA_DIR, "Ready_to_use_data.json"), "w") as file:
        file.write(json_content)
    logger.debug(f"Data saved successfully to {file_name} and Ready_to_use_data.json")
    return f"File {file_name} saved successfully."