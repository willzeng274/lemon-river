"""
Test the ollama completion
"""

from unittest.mock import patch, Mock
import pytest
from llm import OllamaClient, OllamaModelConfig

def test_ollama_completion_success():
    """
    Test that the ollama completion is successful
    """

    mock_response = {
        "message": {
            "role": "assistant",
            "content": "This is a test completion"
        },
        "model": "llama3.2"
    }

    config = OllamaModelConfig(model="llama3.2")
    client = OllamaClient(config)

    with patch('llm.chat') as mock_chat:
        mock_chat.return_value = mock_response

        response = client.complete("Write a test")

        call_args = mock_chat.call_args[1]
        assert call_args["model"] == "llama3.2"
        assert len(call_args["messages"]) == 3  # system + user + assistant
        assert call_args["messages"][0] == {"role": "system", "content": config.system_prompt}
        assert call_args["messages"][1] == {"role": "user", "content": "Write a test"}
        assert call_args["options"] == {
            "temperature": config.temperature,
            "num_predict": config.max_tokens,
            "top_p": config.top_p,
        }

        assert response["message"]["content"] == "This is a test completion"
        assert response["model"] == "llama3.2"

def test_ollama_completion_error():
    """
    Test that errors are properly handled
    """
    config = OllamaModelConfig(model="llama3.2")
    client = OllamaClient(config)

    with patch('llm.chat') as mock_chat:
        mock_chat.side_effect = Exception("Connection error")

        with pytest.raises(Exception) as exc_info:
            client.complete("Write a test")

        assert str(exc_info.value) == "Connection error"

def test_ollama_completion_conversation_history():
    """
    Test that conversation history is properly maintained
    """
    config = OllamaModelConfig(model="llama3.2")
    client = OllamaClient(config)

    mock_responses = [
        {
            "message": {
                "role": "assistant",
                "content": "First response"
            },
            "model": "llama3.2"
        },
        {
            "message": {
                "role": "assistant",
                "content": "Second response"
            },
            "model": "llama3.2"
        }
    ]

    with patch('llm.chat') as mock_chat:
        mock_chat.side_effect = mock_responses

        response1 = client.complete("First message")
        assert response1["message"]["content"] == "First response"

        response2 = client.complete("Second message")
        assert response2["message"]["content"] == "Second response"

        last_call_args = mock_chat.call_args[1]
        messages = last_call_args["messages"]

        assert len(messages) == 5  # system + user1 + assistant1 + user2 + assistant2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "First message"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "First response"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "Second message"
        assert messages[4]["role"] == "assistant"
        assert messages[4]["content"] == "Second response"

def test_ollama_completion_with_mock_tracking():
    """
    Test demonstrating advanced Mock usage with call tracking and custom responses
    """
    config = OllamaModelConfig(model="llama3.2")
    client = OllamaClient(config)

    mock_chat = Mock(name='chat_function')

    def chat_side_effect(model, messages, _options):
        chat_side_effect.called_with_prompts.append(messages[-1]["content"])

        if "hello" in messages[-1]["content"].lower():
            return {
                "message": {
                    "role": "assistant",
                    "content": "Hi there! How can I help?"
                },
                "model": model
            }
        else:
            return {
                "message": {
                    "role": "assistant",
                    "content": "I'm not sure how to respond to that."
                },
                "model": model
            }

    chat_side_effect.called_with_prompts = []

    mock_chat.side_effect = chat_side_effect

    with patch('llm.chat', mock_chat):
        response1 = client.complete("Hello!")
        response2 = client.complete("What's the weather?")

        assert response1["message"]["content"] == "Hi there! How can I help?"
        assert response2["message"]["content"] == "I'm not sure how to respond to that."

        assert mock_chat.call_count == 2
        assert chat_side_effect.called_with_prompts == ["Hello!", "What's the weather?"]

        first_call = mock_chat.call_args_list[0]
        second_call = mock_chat.call_args_list[1]

        assert first_call[1]["model"] == "llama3.2"
        assert second_call[1]["model"] == "llama3.2"

        assert first_call[1]["options"]["temperature"] == config.temperature
        assert second_call[1]["options"]["temperature"] == config.temperature
