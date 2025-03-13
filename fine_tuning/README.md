# Lemon River Fine-Tuning

This module provides tools for fine-tuning Ollama models to better recognize voice commands for the Lemon River job application assistant.

## Overview

The fine-tuning process improves the model's ability to:

1. Recognize voice commands for adding job information
2. Determine when a command is complete or needs more information
3. Ignore casual conversation that isn't meant as a command

## Directory Structure

```
fine_tuning/
├── fine_tuning.py      # Main script for data preparation and fine-tuning
├── data/               # Generated training data
│   └── voice_commands_training.jsonl  # Training dataset
├── models/             # Fine-tuned models will be stored here
└── README.md           # This file
```

## Usage

### Step 1: Create Training Data

To generate only the training data without performing fine-tuning:

```bash
python -m fine_tuning.fine_tuning --create-data-only
```

This will create a JSONL file in the `data` directory with examples for:
- Complete commands (process_command)
- Incomplete commands (wait_for_completion)
- Non-commands (no tool calls)

### Step 2: Fine-Tune Using External Tools

Since Ollama doesn't currently support fine-tuning directly, you'll need to use external tools like llama.cpp or text-generation-webui.

1. Export the training data:
```bash
python -m fine_tuning.fine_tuning --create-data-only
```

2. Use the generated data with your preferred fine-tuning tool
3. Import the fine-tuned model back into Ollama

### Step 3: Configure the Application

Update your `.env` file to use the fine-tuned model:

```
LLM_MODEL="lemon-cmd"
FINE_TUNING_ENABLED=true
```

## Creating Your Own Modelfile

The root directory contains a `Modelfile` with a carefully crafted system prompt for command recognition. You can customize this by:

1. Edit the `Modelfile` in the root directory
2. Build a new model:
```bash
ollama create lemon-cmd-custom -f Modelfile
```
3. Update your `.env` file to use the new model:
```
LLM_MODEL="lemon-cmd-custom"
```

### Modelfile Format and Function Calling

The `Modelfile` has been updated to support modern function calling format using a JSON structure:

```json
{"name": "function_name", "parameters": {"param1": "value1", "param2": "value2"}}
```

When updating the Modelfile, ensure that:
1. The template section uses `ipython` instead of `tool` for function call responses
2. The tool call format follows the JSON structure above
3. The system prompt doesn't include prompt text that would interfere with function calls

You can test your Modelfile changes by running:
```bash
python -m tests.test_modelfile
```

## Performance Optimization

For better performance with Ollama:

1. The fine-tuning script automatically creates an optimized Ollama config
2. Adjust the temperature, top_p, and top_k parameters in `.env` to get the right balance of determinism vs. creativity
3. For command recognition, lower temperature (0.1-0.2) tends to work better

## Additional Training Examples

The `fine_tuning.py` file contains a comprehensive set of training examples. You can add more examples by:

1. Editing the methods in the `FineTuningDataPreparer` class:
   - `get_process_command_examples()`
   - `get_wait_completion_examples()`
   - `get_no_tool_examples()`
2. Run the script again to generate an updated training dataset

## Troubleshooting

- If the model isn't recognizing commands correctly, try adjusting the temperature in `.env` (lower for more deterministic responses)
- If fine-tuning produces unexpected results, check the training examples for inconsistencies
- For GPU performance issues, adjust the `gpu_layers` parameter in the Ollama config 