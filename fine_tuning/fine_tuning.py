"""
Fine-tuning module for Lemon River's voice command model.

This module provides utilities to prepare a dataset for fine-tuning
Ollama models to better recognize and process voice commands for
job application tracking.
"""

import os
import json
import logging
import argparse
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FineTuningDataPreparer:
    """Prepares data for fine-tuning the voice command model"""
    
    def __init__(self, output_dir: str = "fine_tuning/data"):
        """Initialize the data preparer"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    def create_training_data(self, output_file: str = "voice_commands_training.jsonl"):
        """Create a dataset for fine-tuning with voice command examples"""
        data = []
        
        for example in self.get_process_command_examples():
            data.append({
                "prompt": example[0],
                "completion": f"{{\"name\": \"process_command\", \"parameters\": {{\"command_type\": \"{example[1]}\", \"reasoning\": \"{example[2]}\"}}}}"
            })
            
        for example in self.get_wait_completion_examples():
            data.append({
                "prompt": example[0],
                "completion": f"{{\"name\": \"wait_for_completion\", \"parameters\": {{\"command_type\": \"{example[1]}\", \"reasoning\": \"{example[2]}\"}}}}"
            })
            
        for example in self.get_no_tool_examples():
            data.append({
                "prompt": example,
                "completion": "I don't need to use any tools for this request."
            })
        
        output_path = os.path.join(self.output_dir, output_file)
        with open(output_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        
        logger.info(f"Created training data with {len(data)} examples at {output_path}")
        return output_path
    
    def get_process_command_examples(self) -> List[tuple]:
        """
        Get examples where process_command should be called.
        Each tuple contains (user_input, command_type, reasoning)
        """
        return [
            ("add title from clipboard", "ADD_TITLE", "User clearly said 'add title'"),
            ("add the company name", "ADD_COMPANY", "User explicitly mentioned 'add' and 'company'"),
            ("add url", "ADD_URL", "User explicitly said 'add url'"),
            ("add link please", "ADD_LINK", "User explicitly said 'add link'"),
            ("add description from clipboard", "ADD_DESCRIPTION", "User explicitly said 'add description'"),
            ("add the job description", "ADD_DESCRIPTION", "User explicitly mentioned 'add' and 'job description'"),
            ("add location", "ADD_LOCATION", "User explicitly said 'add location'"),
            ("add the location", "ADD_LOCATION", "User explicitly mentioned 'add location'"),
            ("add duration", "ADD_DURATION", "User explicitly said 'add duration'"),
            ("add a question", "ADD_QUESTION", "User explicitly said 'add' and 'question'"),
            ("add answer", "ADD_ANSWER", "User explicitly said 'add answer'"),
            ("add note", "ADD_NOTE", "User explicitly said 'add note'"),
            ("add notes", "ADD_NOTES", "User explicitly said 'add notes'"),
            
            ("update title", "ADD_TITLE", "User said 'update title' which is equivalent to 'add title'"),
            ("update the job title", "ADD_TITLE", "User mentioned 'update' and 'job title'"),
            ("store company name", "ADD_COMPANY", "User said 'store company name' which is equivalent to 'add company'"),
            ("store the url", "ADD_URL", "User said 'store url' which is equivalent to 'add url'"),
            ("paste title", "ADD_TITLE", "User said 'paste title' which is equivalent to 'add title'"),
            ("paste the company", "ADD_COMPANY", "User said 'paste company' which is equivalent to 'add company'"),
            
            ("I want to add the title", "ADD_TITLE", "User expressed intent to 'add title'"),
            ("I need to add the job description to this", "ADD_DESCRIPTION", "User expressed intent to add job description"),
            ("please add the url from clipboard", "ADD_URL", "User asked to 'add url'"),
            ("I should add the company name", "ADD_COMPANY", "User expressed intent to 'add company'"),
            ("could you add the job location", "ADD_LOCATION", "User asked to 'add location'"),
            ("let's add the position duration", "ADD_DURATION", "User expressed intent to 'add duration'"),
            
            ("add role", "ADD_ROLE", "User explicitly said 'add role' which is an alias for 'add title'"),
            ("add job title from clipboard", "ADD_JOB_TITLE", "User explicitly mentioned 'add job title'"),
            ("add the link", "ADD_LINK", "User explicitly mentioned 'add link' which is an alias for 'add url'"),
            
            ("um add title please", "ADD_TITLE", "User said 'add title' despite filler words"),
            ("so I want to add the company now", "ADD_COMPANY", "User expressed intent to 'add company'"),
            ("hmm I think I need to add the job description", "ADD_DESCRIPTION", "User expressed intent to 'add description'"),
            ("well actually add location from clipboard", "ADD_LOCATION", "User said 'add location' despite filler words"),
            
            ("the clipboard has the title so add title", "ADD_TITLE", "User explicitly said 'add title'"),
            ("I copied the company so add company", "ADD_COMPANY", "User explicitly said 'add company'"),
            ("this description looks good, add description", "ADD_DESCRIPTION", "User explicitly said 'add description'"),
            ("this url is what I want, add url", "ADD_URL", "User explicitly said 'add url'"),
            
            ("add the job's title", "ADD_TITLE", "User mentioned 'add' and 'job's title'"),
            ("add the name of the company", "ADD_COMPANY", "User expressed intent to 'add company'"),
            ("add where the job is located", "ADD_LOCATION", "User expressed intent to 'add location'"),
            ("add how long the job lasts", "ADD_DURATION", "User expressed intent to 'add duration'"),
            ("add what the job entails", "ADD_DESCRIPTION", "User expressed intent to 'add description'"),
            ("add the query from the application", "ADD_QUESTION", "User expressed intent to 'add question'"),
            ("add my response to their question", "ADD_ANSWER", "User expressed intent to 'add answer'"),
            ("add an important comment", "ADD_NOTE", "User expressed intent to 'add note'"),
            
            ("I've copied the title from the website so add title", "ADD_TITLE", "User explicitly said 'add title'"),
            ("I found the company name on LinkedIn so add company", "ADD_COMPANY", "User explicitly said 'add company'"),
            ("this job is in Seattle so add location", "ADD_LOCATION", "User explicitly said 'add location'"),
            ("it's a 6-month contract so add duration", "ADD_DURATION", "User explicitly said 'add duration'"),
            ("I've copied all the requirements so add description", "ADD_DESCRIPTION", "User explicitly said 'add description'"),
            
            ("I'm looking at the application form now and need to add a question", "ADD_QUESTION", "User mentioned 'add a question'"),
            ("I've written a response to their question and want to add answer", "ADD_ANSWER", "User mentioned 'add answer'"),
            ("I should make a note about the interview process so add note", "ADD_NOTE", "User mentioned 'add note'"),
            
            ("oh I see they're asking for Python experience I should add this to description", "ADD_DESCRIPTION", "User mentioned 'add' and 'description'"),
            ("this looks like a great role at Google I'll add the company", "ADD_COMPANY", "User mentioned 'add the company'"),
            ("they want 5 years of experience so I'll add that to the note", "ADD_NOTE", "User mentioned 'add' and 'note'"),
        ]
    
    def get_wait_completion_examples(self) -> List[tuple]:
        """
        Get examples where wait_for_completion should be called.
        Each tuple contains (user_input, command_type, reasoning)
        """
        return [
            ("add", "UNKNOWN", "User only said 'add' without specifying what to add"),
            ("add the", "UNKNOWN", "User started to specify but didn't complete the command"),
            ("I need to add", "UNKNOWN", "User expressed intent to add something but didn't specify what"),
            ("add something", "UNKNOWN", "User didn't specify what type of information to add"),
            ("update", "UNKNOWN", "User only said 'update' without specifying what to update"),
            ("store", "UNKNOWN", "User only said 'store' without specifying what to store"),
            ("I want to add the", "UNKNOWN", "User started to specify but didn't complete the command"),
            
            ("add link wait", "ADD_URL", "User said 'add link' but then said 'wait'"),
            ("add title but I need to check first", "ADD_TITLE", "User seems uncertain about adding the title"),
            ("hmm add company or maybe add location", "UNKNOWN", "User is uncertain about what to add"),
            ("add note or maybe I should add a question", "UNKNOWN", "User is uncertain about what to add"),
            
            ("add the company but let me check the spelling", "ADD_COMPANY", "User wants to add company but seems to want to wait"),
            ("add location but I'm not sure if it's remote", "ADD_LOCATION", "User is uncertain about adding the location"),
            
            ("add the job um let me think", "UNKNOWN", "User started to give a command but interrupted themselves"),
            ("add I forget what I was going to say", "UNKNOWN", "User started to give a command but lost their train of thought"),
            
            ("add resume", "UNKNOWN", "User mentioned 'add resume' which is not a valid command"),
            ("add salary", "UNKNOWN", "User mentioned 'add salary' which is not a valid command"),
            ("add deadline", "UNKNOWN", "User mentioned 'add deadline' which is not a valid command"),
            
            ("title add", "UNKNOWN", "User mentioned 'title' and 'add' but in the wrong order"),
            ("company add please", "UNKNOWN", "User mentioned 'company' and 'add' but in the wrong order"),
            ("description add from clipboard", "UNKNOWN", "User mentioned 'description' and 'add' but in the wrong order"),
            
            ("maybe add", "UNKNOWN", "User is uncertain about whether to add something"),
            ("I could add but", "UNKNOWN", "User is uncertain about whether to add something"),
            ("should I add", "UNKNOWN", "User is asking a question rather than giving a command"),
            
            ("add to the title", "ADD_TITLE", "User's command syntax is unusual but seems to want to add to title"),
            ("add in the description", "ADD_DESCRIPTION", "User's command syntax is unusual but seems to want to add description"),
            ("please to add the company", "ADD_COMPANY", "User's command syntax is unusual but seems to want to add company"),
        ]
    
    def get_no_tool_examples(self) -> List[str]:
        """Get examples where no tool should be called"""
        return [
            "this job has good benefits",
            "I like this company",
            "the salary seems competitive",
            "this job requires Python experience",
            "they want someone with five years of experience",
            "the location is perfect for me",
            "this seems like a good opportunity",
            "the job description mentions agile methodology",
            "I'm qualified for this position",
            
            "what does this company do?",
            "I wonder if I should apply",
            "do I have the skills for this?",
            "is this a remote position?",
            "when is the application deadline?",
            "how should I tailor my resume for this?",
            "should I mention my project experience?",
            
            "looking at the job requirements",
            "reading through the company description",
            "checking the company website",
            "researching this company on LinkedIn",
            "finding more information about the role",
            "comparing this to other opportunities",
            "thinking about my qualifications",
            
            "job title looks interesting",
            "company has good reviews",
            "description mentions teamwork",
            "location is in Seattle",
            "duration is six months",
            "question about leadership experience",
            "answer should focus on my project management",
            "note that they require security clearance",
            
            "I think I'll apply for this position",
            "this job aligns with my career goals",
            "I need to update my resume for this",
            "I should highlight my Python experience",
            "they're looking for someone with database knowledge",
            "this would be a good step in my career",
            
            "the title is Software Engineer",
            "company is Google",
            "job location is New York",
            "position is for 12 months",
            "description mentions machine learning",
            "they're asking about my experience with AWS",
            "I'll mention my team leadership experience in my answer",
            "I should remember to follow up after applying",
        ]

def setup_ollama_config():
    """Create an optimized Ollama config file"""
    config_dir = os.path.expanduser("~/.ollama")
    os.makedirs(config_dir, exist_ok=True)
    
    config = {
        "gpu_layers": 35, # Based on GPU memory
        "num_ctx": 8192,  # Context window size
        "num_batch": 512, # Batch size for processing
        "num_thread": 8,  # Number of CPU threads to use
        "rope_frequency_base": 10000.0,
        "rope_frequency_scale": 1.0,
        "cache": True    # Enable caching
    }
    
    config_path = os.path.join(config_dir, "config")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created optimized Ollama config at {config_path}")
    return config_path

def fine_tune_model(
    base_model: str = "llama3.2", 
    modelfile: str = "Modelfile", 
    dataset_path: Optional[str] = None,
    output_model: str = "lemon-cmd"
):
    """Run the fine-tuning process for the model"""
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("Ollama is not installed or not in PATH. Please install Ollama first.")
        return False
    
    if not dataset_path:
        preparer = FineTuningDataPreparer()
        dataset_path = preparer.create_training_data()
    
    setup_ollama_config()
    
    logger.info(f"Creating base model from {modelfile}")
    subprocess.run(["ollama", "create", output_model, "-f", modelfile], check=True)
    
    logger.info(
        f"To fine-tune with an external tool, use:\n"
        f"- Dataset path: {dataset_path}\n"
        f"- Base model: {base_model}\n"
        f"- Output model name: {output_model}"
    )
    
    logger.info(
        "Since Ollama doesn't have official fine-tuning support yet, consider:\n"
        "1. Use llama.cpp or text-generation-webui for fine-tuning\n"
        "2. Convert your model to Ollama format\n"
        "3. Import the fine-tuned model to Ollama"
    )
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Ollama model for voice commands")
    parser.add_argument("--base-model", default="llama3.2", help="Base model to fine-tune")
    parser.add_argument("--modelfile", default="Modelfile", help="Path to Modelfile")
    parser.add_argument("--output-model", default="lemon-cmd", help="Name for the output model")
    parser.add_argument("--create-data-only", action="store_true", help="Only create training data, don't fine-tune")
    args = parser.parse_args()
    
    if args.create_data_only:
        preparer = FineTuningDataPreparer()
        dataset_path = preparer.create_training_data()
        print(f"Created training data at: {dataset_path}")
    else:
        fine_tune_model(args.base_model, args.modelfile, output_model=args.output_model) 