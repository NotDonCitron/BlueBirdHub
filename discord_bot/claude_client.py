import subprocess
import json
import os

# --- Configuration ---
ZEN_SERVER_URL = "http://localhost:8000/v1/chat/completions"
TARGET_MODEL = "claude-code"

def send_to_claude(user_content: str) -> str:
    """
    Sends a request to the Claude model via the Zen Server and returns the response.

    Args:
        user_content: The content of the user's message.

    Returns:
        The model's reply as a string, or an error message if something went wrong.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    system_prompt_path = os.path.join(script_dir, "..", "claude_interface", "system_prompt.txt")

    try:
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        return "Error: 'system_prompt.txt' not found."

    payload = {
        "model": TARGET_MODEL,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_content}],
        "stream": False
    }

    payload_json = json.dumps(payload).replace("'", "''")

    command = [
        "powershell",
        "-Command",
        f"Invoke-WebRequest -Uri '{ZEN_SERVER_URL}' -Method 'POST' -ContentType 'application/json' -Body '{payload_json}' -UseBasicParsing | Select-Object -ExpandProperty Content"
    ]

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True,
            timeout=300
        )
        response_data = json.loads(process.stdout)
        model_reply = response_data['choices'][0]['message']['content']
        return model_reply
    except subprocess.TimeoutExpired:
        return "Error: The request timed out."
    except subprocess.CalledProcessError as e:
        return f"Error executing web request: {e.stderr}"
    except (KeyError, IndexError, json.JSONDecodeError):
        return f"Error: The model's response was in an unexpected format. Response: {process.stdout}"

if __name__ == '__main__':
    # Example usage for testing
    test_prompt = "Hello Claude, please write a simple python hello world."
    print(f"Sending test prompt: '{test_prompt}'")
    response = send_to_claude(test_prompt)
    print("\nReceived response:\n---")
    print(response)
    print("---") 