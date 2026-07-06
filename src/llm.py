from typing import Optional

from ollama import chat


def ollama_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    host: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Send a single chat request to a local Ollama model and return text.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    kwargs = {
        "model": model,
        "messages": messages,
        "options": {"temperature": temperature},
    }
    if host:
        from ollama import Client

        client = Client(host=host)
        response = client.chat(**kwargs)
    else:
        response = chat(**kwargs)

    return response["message"]["content"].strip()


def ollama_chat_stream(
    model: str,
    system_prompt: str,
    user_prompt: str,
    host: Optional[str] = None,
    temperature: float = 0.2,
):
    """
    Stream tokens from Ollama; yields text chunks.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    kwargs = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature},
    }
    if host:
        from ollama import Client

        client = Client(host=host)
        return client.chat(**kwargs)
    return chat(**kwargs)
