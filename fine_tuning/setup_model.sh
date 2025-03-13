#!/bin/bash
# Setup script for Lemon River fine-tuning

set -e  # Exit on error

echo "Setting up Lemon River fine-tuned model..."

# root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# if not exists
mkdir -p fine_tuning/data

echo "Generating training data..."
python3 -m fine_tuning.fine_tuning --create-data-only

echo "Creating base model from Modelfile..."
if ollama list | grep -q "lemon-cmd"; then
  echo "Model lemon-cmd already exists. Removing..."
  ollama rm lemon-cmd
fi

echo "Creating new model..."
ollama create lemon-cmd -f Modelfile

echo "Testing the model with demo..."
python3 -m fine_tuning.demo

echo "Testing the model with test suite..."
python3 -m tests.test_modelfile

if [ -f .env ]; then
  echo "Updating .env file..."
  if grep -q "^LLM_MODEL=" .env; then
    sed -i.bak 's/^LLM_MODEL=/#LLM_MODEL=/' .env
    echo 'LLM_MODEL="lemon-cmd"' >> .env
  else
    echo 'LLM_MODEL="lemon-cmd"' >> .env
  fi
  
  if grep -q "^FINE_TUNING_ENABLED=" .env; then
    sed -i.bak 's/^FINE_TUNING_ENABLED=.*/FINE_TUNING_ENABLED=true/' .env
  else
    echo 'FINE_TUNING_ENABLED=true' >> .env
  fi
  
  if ! grep -q "^LLM_TEMPERATURE=" .env; then
    echo 'LLM_TEMPERATURE=0.1' >> .env
  fi
  if ! grep -q "^LLM_TOP_P=" .env; then
    echo 'LLM_TOP_P=0.95' >> .env
  fi
  if ! grep -q "^LLM_TOP_K=" .env; then
    echo 'LLM_TOP_K=40' >> .env
  fi
else
  echo "Creating new .env file..."
  cp .env.example .env
  sed -i.bak 's/^LLM_MODEL=.*/#LLM_MODEL=/' .env
  echo 'LLM_MODEL="lemon-cmd"' >> .env
  echo 'FINE_TUNING_ENABLED=true' >> .env
fi

echo "Setup complete! Model is ready to use."
echo "To test the model, run: python -m fine_tuning.demo"