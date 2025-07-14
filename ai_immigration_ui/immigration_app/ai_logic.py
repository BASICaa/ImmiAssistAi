import json
import os
from typing import Dict
from django.conf import settings
from .Agents.Orchestrator import Orchestrator_agent, Command_evaluation_agent,CommandGen, Assistant_Agent
from pydantic_ai.messages import ModelMessage
from immigration_app.Agents.Classes import output_agent
from typing import Union
from .Agents.Classes import ImmigrationProfileModelparse, CommandGen, ImmigrationProfileModel
from .Agents.logging_config import AppLogger

logger = AppLogger(log_file='ai_logic_debug.log').get_logger()

def process_request(user_input: Union[str, dict]) -> output_agent:
    """
    Processes user input (string from chat or dict from a form) by passing it
    through the full AI agent chain.

    The returned 'output_agent' object has a 'request' field. As per the project's
    design, the frontend UI is responsible for interpreting this field:
    - If request == 'adding_new_data', the UI should display the profile form.
    - Otherwise, the UI should display the content from 'outputs_recieved'.
    """
    logger.info(f"Processing user input of type: {type(user_input)}")

    try:
        # The Command_evaluation_agent handles both strings (chat) and
        # dictionaries (form submissions) to create an appropriate command.
        Command_result_raw = Command_evaluation_agent.run_sync(user_input, model_settings={"timeout": 60})
        logger.debug(f"Raw command from agent: {Command_result_raw.output}")

        Json_ver = json.loads(Command_result_raw.output)
        Command_result = CommandGen.model_validate(Json_ver)
        logger.debug(f"Validated Command: {Command_result}")

        # The Orchestrator_agent executes the command.
        agent_res = Orchestrator_agent.run_sync(
            Command_result.Command,
            deps=Command_result,
            model_settings={"timeout": 60},
            output_type=output_agent
        )
        logger.debug(f"Raw agent response: {agent_res.output}")

        # The final output is validated against the output_agent class.
        response = output_agent.model_validate(agent_res.output)
        logger.info(f"Successfully processed request. Final output: {response}")

        return response

    except Exception as e:
        logger.error(f"An error occurred in the AI processing chain: {e}", exc_info=True)
        return output_agent(request="error", outputs_recieved="An error occurred while processing your request.")