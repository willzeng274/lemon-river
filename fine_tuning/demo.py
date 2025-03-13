"""
Demonstration script for the fine-tuning module.

This script shows how to create a fine-tuning dataset and use a fine-tuned model.
"""

import os
import sys
import logging
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from fine_tuning.fine_tuning import (
    FineTuningDataPreparer, setup_ollama_config, fine_tune_model
)
from utils import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_create_training_data():
    """Demonstrate how to create training data"""
    logger.info("Creating fine-tuning training data...")
    
    preparer = FineTuningDataPreparer()
    dataset_path = preparer.create_training_data()
    
    logger.info(f"Created training dataset at: {dataset_path}")
    
    num_examples = 5
    logger.info(f"First {num_examples} examples from the dataset:")
    
    import json
    with open(dataset_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_examples:
                break
            example = json.loads(line)
            logger.info(f"Example {i+1}:")
            logger.info(f"  Prompt: {example['prompt']}")
            logger.info(f"  Completion: {example['completion']}")
            logger.info("")
    
    return dataset_path

def demo_model_setup():
    """Demonstrate how to set up a model with the Modelfile"""
    logger.info("Setting up Ollama model with Modelfile...")
    
    config_path = setup_ollama_config()
    logger.info(f"Created optimized Ollama config at: {config_path}")
    
    model_name = "lemon-cmd"
    
    try:
        import subprocess
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if model_name in result.stdout:
            logger.info(f"Model {model_name} already exists")
        else:
            logger.info(f"Creating model {model_name} from Modelfile...")
            modelfile_path = os.path.join(parent_dir, "Modelfile")
            if os.path.exists(modelfile_path):
                subprocess.run(
                    ["ollama", "create", model_name, "-f", modelfile_path], 
                    check=True
                )
                logger.info(f"Created model {model_name}")
            else:
                logger.error(f"Modelfile not found at {modelfile_path}")
    except Exception as e:
        logger.error(f"Error setting up model: {str(e)}")
    
    return model_name

def demo_test_commands(model_name="lemon-cmd"):
    """Demonstrate testing the model with sample commands"""
    logger.info(f"Testing model {model_name} with sample commands...")
    
    test_commands = [
        "add title from clipboard",
        "add the company name",
        "I need to add",
        "this job has good benefits",
        "I should add the job description to this"
    ]
    
    try:
        import ollama
        
        process_command_spec = {
            "name": "process_command",
            "description": "Process a complete voice command",
            "parameters": {
                "type": "object",
                "required": ["command_type", "reasoning"],
                "properties": {
                    "command_type": {
                        "type": "string",
                        "description": "The type of command to execute",
                        "enum": [
                            "ADD_URL", "ADD_TITLE", "ADD_COMPANY", "ADD_LOCATION", 
                            "ADD_DURATION", "ADD_DESCRIPTION", "ADD_QUESTION", 
                            "ADD_ANSWER", "ADD_NOTE", "ADD_CHECK_URL", "ADD_LINK", 
                            "ADD_NOTES", "ADD_ROLE", "ADD_NODES", "ADD_JOB_TITLE", "UNKNOWN"
                        ]
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "The reason why what the user said was a command"
                    }
                }
            }
        }
        
        wait_for_completion_spec = {
            "name": "wait_for_completion",
            "description": "Indicate a command needs more information",
            "parameters": {
                "type": "object",
                "required": ["command_type", "reasoning"],
                "properties": {
                    "command_type": {
                        "type": "string",
                        "description": "The type of command detected",
                        "enum": [
                            "ADD_URL", "ADD_TITLE", "ADD_COMPANY", "ADD_LOCATION", 
                            "ADD_DURATION", "ADD_DESCRIPTION", "ADD_QUESTION", 
                            "ADD_ANSWER", "ADD_NOTE", "ADD_CHECK_URL", "ADD_LINK", 
                            "ADD_NOTES", "ADD_ROLE", "ADD_NODES", "ADD_JOB_TITLE", "UNKNOWN"
                        ]
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "The reason why what the user said was not a command"
                    }
                }
            }
        }
        
        tools = [process_command_spec, wait_for_completion_spec]
        
        system_prompt = """<BEGIN SYSTEM PROMPT>
You are a voice command processor for a job application tracking system.
Your task is to identify explicit commands and determine if they are complete. You also must provide a reason for your decision.

When calling tools, ALWAYS use the EXACT parameter names:
- "command_type": Must be one of these exact values: ADD_URL, ADD_TITLE, ADD_COMPANY, ADD_LOCATION, ADD_DURATION, ADD_DESCRIPTION, ADD_QUESTION, ADD_ANSWER, ADD_NOTE, ADD_CHECK_URL, ADD_LINK, ADD_NOTES, ADD_ROLE, ADD_NODES, ADD_JOB_TITLE, UNKNOWN
- "reasoning": A brief explanation for your decision

STRICT RULES FOR USING TOOLS:
1. ONLY call process_command when the user explicitly mentions "add", "paste", or "update" followed by a specific, complete type (like "title", "url", "company")
2. Convert any "update" or "store" commands to their "ADD_" equivalents (e.g., "update title" should use command_type "ADD_TITLE")
3. ALWAYS call wait_for_completion (NOT process_command) when:
   - The user ONLY said "add" without specifying what to add
   - The user said something like "I need to add" without specifying what
   - The user said "add the" without completing the command
   - The command is unclear or ambiguous
   - The user expressed uncertainty about the command (e.g., "add title but I'm not sure")
   - The user said "add link wait" or similar with "wait" indicating uncertainty
4. DO NOT call ANY tool if the user is just making a statement or asking a question 
   - For example: "this job has good benefits" or "I like this company" should NOT trigger ANY tool calls
   - DO NOT respond with ANY tool call for casual conversation

ONLY USE THE EXACT TOOLS PROVIDED - NO CUSTOM FUNCTION NAMES!
<END SYSTEM PROMPT>"""
        
        for cmd in test_commands:
            logger.info(f"Testing command: '{cmd}'")
            
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": cmd}
                ],
                options={
                    "temperature": 0.1,
                },
                tools=tools
            )
            
            logger.info(f"Response type: {type(response['message'])}")
            if 'tool_calls' in response['message']:
                tool_call = response['message']['tool_calls'][0]
                logger.info(f"Tool call: {tool_call['function']['name']}")
                logger.info(f"Parameters: {tool_call['function']['arguments']}")
                
                if isinstance(tool_call['function']['arguments'], dict):
                    args = tool_call['function']['arguments']
                else:
                    try:
                        args = json.loads(tool_call['function']['arguments'])
                    except:
                        args = {}
                
                command_type = None
                if 'command_type' in args:
                    command_type = args['command_type']
                elif 'parameters' in args and 'command_type' in args['parameters']:
                    command_type = args['parameters']['command_type']
                
                logger.info(f"Command type: {command_type}")
                
                # Show if this is correct
                expected_tools = ["process_command", "wait_for_completion"]
                if tool_call['function']['name'] not in expected_tools:
                    logger.error(f"ERROR: '{tool_call['function']['name']}' is NOT one of the expected tools: {expected_tools}")
                else:
                    logger.info(f"SUCCESS: Used correct tool: {tool_call['function']['name']}")
                
                # Show consistency with command_handler.py behavior
                if command_type is not None:
                    valid_types = ["ADD_URL", "ADD_TITLE", "ADD_COMPANY", "ADD_LOCATION", "ADD_DURATION", 
                                   "ADD_DESCRIPTION", "ADD_QUESTION", "ADD_ANSWER", "ADD_NOTE", "ADD_CHECK_URL", 
                                   "ADD_LINK", "ADD_NOTES", "ADD_ROLE", "ADD_JOB_TITLE", "ADD_NODES", "UNKNOWN"]
                    if command_type in valid_types:
                        logger.info(f"SUCCESS: Used correct command_type: {command_type}")
                    else:
                        logger.error(f"ERROR: '{command_type}' is NOT a valid command type")
                else:
                    logger.error("ERROR: Missing command_type parameter")
            else:
                logger.info(f"No tool call, content: {response['message']['content']}")
                if cmd in ["this job has good benefits", "I like this company"]:
                    logger.info("SUCCESS: Correctly did not call a tool for casual conversation")
                else:
                    logger.warning("WARNING: No tool called but might be needed for this command")
            
            logger.info("")
    except Exception as e:
        logger.error(f"Error testing commands: {str(e)}")

if __name__ == "__main__":
    logger.info("Demonstrating fine-tuning workflow")
    
    dataset_path = demo_create_training_data()
    
    model_name = demo_model_setup()
    
    demo_test_commands(model_name)
    
    logger.info("Demonstration complete!")
    logger.info(
        "To use the fine-tuned model in your application:\n"
        "1. Set LLM_MODEL to your model name in .env\n"
        "2. Set FINE_TUNING_ENABLED=true in .env\n"
    ) 