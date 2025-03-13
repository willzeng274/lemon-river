"""
Test script for verifying the enhanced Modelfile with proper tool calling.

This script creates a model using the Modelfile and tests it with various voice command scenarios
to ensure it correctly uses tool calling.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from fine_tuning.fine_tuning import setup_ollama_config

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_NAME = "lemon-cmd-test"

def create_test_model(modelfile_path: str = "Modelfile") -> bool:
    """Create a test model using the enhanced Modelfile"""
    try:
        # Check if the model already exists and remove it
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if MODEL_NAME in result.stdout:
            logger.info(f"Removing existing model {MODEL_NAME}")
            subprocess.run(["ollama", "rm", MODEL_NAME], check=True)
        
        # Create the model
        logger.info(f"Creating model {MODEL_NAME} from {modelfile_path}")
        subprocess.run(["ollama", "create", MODEL_NAME, "-f", modelfile_path], check=True)
        return True
    except Exception as e:
        logger.error(f"Error creating test model: {str(e)}")
        return False


def test_command(prompt: str) -> Dict[str, Any]:
    """Test a voice command with the model"""
    try:
        import ollama
        
        # Define tool specifications
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
        
        # Define the tools array
        tools = [process_command_spec, wait_for_completion_spec]
        
        # Make the API call
        logger.info(f"Testing command: '{prompt}'")
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.1,
            },
            tools=tools
        )
        
        # Debug: Print response message
        logger.debug(f"Response message: {response['message']}")
        
        return response
    except Exception as e:
        logger.error(f"Error testing command: {str(e)}")
        return {"error": str(e)}


def run_test_suite():
    """Run a series of tests with different voice commands"""
    test_cases = [
        # Complete commands
        {"prompt": "add title from clipboard", "expected_tool": "process_command", "expected_type": "ADD_TITLE"},
        {"prompt": "add the company name", "expected_tool": "process_command", "expected_type": "ADD_COMPANY"},
        {"prompt": "update description", "expected_tool": "process_command", "expected_type": "ADD_DESCRIPTION"},
        {"prompt": "store url please", "expected_tool": "process_command", "expected_type": "ADD_URL"},
        
        # Incomplete commands
        {"prompt": "add", "expected_tool": "wait_for_completion", "expected_type": "UNKNOWN"},
        {"prompt": "I need to add", "expected_tool": "wait_for_completion", "expected_type": "UNKNOWN"},
        {"prompt": "add the", "expected_tool": "wait_for_completion", "expected_type": "UNKNOWN"},
        
        # Ambiguous commands
        {"prompt": "add title but I'm not sure", "expected_tool": "wait_for_completion", "expected_type": "ADD_TITLE"},
        {"prompt": "add link wait", "expected_tool": "wait_for_completion", "expected_type": "ADD_URL"},
        
        # Non-commands
        {"prompt": "this job has good benefits", "expected_tool": None, "expected_type": None},
        {"prompt": "I like this company", "expected_tool": None, "expected_type": None},
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        prompt = test_case["prompt"]
        expected_tool = test_case["expected_tool"]
        expected_type = test_case["expected_type"]
        
        logger.info(f"Test {i+1}/{len(test_cases)}: '{prompt}'")
        response = test_command(prompt)
        
        result = {
            "prompt": prompt,
            "expected_tool": expected_tool,
            "expected_type": expected_type,
            "passed": False,
            "details": {}
        }
        
        if "error" in response:
            logger.error(f"  Error: {response['error']}")
            result["details"] = {"error": response["error"]}
        else:
            # Check if the model called a tool
            tool_calls = response["message"].get("tool_calls", [])
            actual_tool = None
            actual_type = None
            
            if tool_calls:
                actual_tool = tool_calls[0]["function"]["name"]
                # Check if arguments is already a dict or a JSON string
                arguments = tool_calls[0]["function"]["arguments"]
                logger.debug(f"Raw arguments: {arguments}")
                
                if isinstance(arguments, dict):
                    args = arguments
                else:
                    try:
                        args = json.loads(arguments)
                    except (json.JSONDecodeError, TypeError):
                        logger.error(f"Failed to parse arguments: {arguments}")
                        args = {"command_type": None, "reasoning": ""}
                
                # Debug: Print arguments
                logger.debug(f"Parsed arguments: {args}")
                
                # Look for command_type in different places or try to convert from alternative keys
                actual_type = None
                
                # Direct match
                if "command_type" in args:
                    actual_type = args["command_type"]
                # Nested parameters
                elif "parameters" in args and "command_type" in args["parameters"]:
                    actual_type = args["parameters"]["command_type"]
                # Try alternative keys
                elif "cmd" in args:
                    cmd_val = args["cmd"]
                    # Check if it looks like a command type
                    if cmd_val.upper().startswith("ADD_") or cmd_val == "UNKNOWN":
                        actual_type = cmd_val.upper()
                    # Try to convert type if present
                    elif "type" in args:
                        type_val = args["type"]
                        if type_val.upper() in ["URL", "TITLE", "COMPANY", "LOCATION", "DURATION", 
                                             "DESCRIPTION", "QUESTION", "ANSWER", "NOTE"]:
                            actual_type = f"ADD_{type_val.upper()}"
                elif "command" in args:
                    cmd_val = args["command"]
                    if isinstance(cmd_val, str) and (cmd_val.upper().startswith("ADD_") or cmd_val == "UNKNOWN"):
                        actual_type = cmd_val.upper()
                else:
                    logger.warning(f"Could not determine command_type from arguments: {args}")
                
                # Similarly for reasoning
                reasoning = ""
                if "reasoning" in args:
                    reasoning = args["reasoning"]
                elif "parameters" in args and "reasoning" in args["parameters"]:
                    reasoning = args["parameters"]["reasoning"]
                
                result["details"] = {
                    "actual_tool": actual_tool,
                    "actual_type": actual_type,
                    "reasoning": reasoning
                }
                
                # Determine if the test passed
                if expected_tool is None:
                    # Expected no tool call but got one
                    logger.warning(f"  Expected no tool call but got: {actual_tool}")
                    result["passed"] = False
                elif actual_tool == expected_tool and actual_type == expected_type:
                    logger.info(f"  PASSED: Called {actual_tool} with type {actual_type}")
                    result["passed"] = True
                else:
                    logger.warning(f"  FAILED: Expected {expected_tool} with {expected_type}, got {actual_tool} with {actual_type}")
                    result["passed"] = False
            else:
                result["details"] = {"content": response["message"]["content"]}
                
                # If we expected no tool call and got none, it's a pass
                if expected_tool is None:
                    logger.info("  PASSED: No tool call as expected")
                    result["passed"] = True
                else:
                    logger.warning(f"  FAILED: Expected {expected_tool} but got no tool call")
                    result["passed"] = False
        
        results.append(result)
        logger.info("---------------------------------------------------")
    
    # Summarize results
    passed = sum(1 for r in results if r["passed"])
    logger.info(f"Test summary: {passed}/{len(results)} tests passed ({passed/len(results)*100:.1f}%)")
    
    # Print details of failed tests
    failed = [r for r in results if not r["passed"]]
    if failed:
        logger.info("Failed tests:")
        for i, test in enumerate(failed):
            logger.info(f"  {i+1}. Prompt: '{test['prompt']}'")
            logger.info(f"     Expected: {test['expected_tool']} with {test['expected_type']}")
            logger.info(f"     Got: {test['details']}")
    
    return results


if __name__ == "__main__":
    logger.info("Testing enhanced Modelfile")
    
    # Setup optimized Ollama config
    setup_ollama_config()
    
    # Create the test model
    if create_test_model():
        # Run the test suite
        results = run_test_suite()
        
        # Clean up
        logger.info(f"Cleaning up - removing model {MODEL_NAME}")
        try:
            subprocess.run(["ollama", "rm", MODEL_NAME], check=True)
        except Exception as e:
            logger.error(f"Error removing test model: {str(e)}")
    else:
        logger.error("Failed to create test model. Tests aborted.") 