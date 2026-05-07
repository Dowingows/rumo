import json
import os
import re
import httpx
from pathlib import Path
from dotenv import load_dotenv

# carrega credenciais do usuário (~/.rumo/.env) antes do .env do projeto
load_dotenv(Path.home() / ".rumo" / ".env")
load_dotenv()

OLLAMA_URL = os.getenv("RUMO_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("RUMO_MODEL", "qwen3:4b")
OLLAMA_TEMPERATURE = float(os.getenv("RUMO_TEMPERATURE", "0.1"))
GROQ_API_KEY = os.getenv("RUMO_GROQ_KEY", "")
GROQ_MODEL = os.getenv("RUMO_GROQ_MODEL", "llama3-8b-8192")
OPENCODE_API_KEY = os.getenv("RUMO_OPENCODE_KEY", "")
OPENCODE_MODEL = os.getenv("RUMO_OPENCODE_MODEL", "kimi-k2.6")
OPENCODE_URL = "https://opencode.ai/zen/go/v1/chat/completions"


def _backend() -> str:
    from rumo.config import carregar
    cfg = carregar()
    escolha = cfg.get("backend", "")
    if escolha in ("ollama", "groq", "opencode"):
        return escolha
    # auto-detect por chaves presentes
    if OPENCODE_API_KEY:
        return "opencode"
    if GROQ_API_KEY:
        return "groq"
    return "ollama"


def complete(prompt: str, system: str = "", model: str = "") -> str:
    backend = _backend()
    if backend == "opencode":
        return _opencode(prompt, system, model)
    if backend == "groq":
        return _groq(prompt, system)
    return _ollama(prompt, system, model or OLLAMA_MODEL)


def complete_with_tools(messages: list[dict], tools: list[dict], model: str = "", debug: bool = False) -> dict:
    """Retorna {"type": "text", "content": str} ou {"type": "tool_call", "name": str, "arguments": dict}."""
    backend = _backend()
    if backend == "opencode":
        return _opencode_tools(messages, tools, model, debug=debug)
    if backend == "groq":
        return _groq_tools(messages, tools, debug=debug)
    return _ollama_tools(messages, tools, model or OLLAMA_MODEL, debug=debug)


def _ollama(prompt: str, system: str, model: str = "") -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": model or OLLAMA_MODEL, "messages": messages, "stream": False,
              "options": {"temperature": OLLAMA_TEMPERATURE, "think": False}},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def _groq(prompt: str, system: str) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": GROQ_MODEL, "messages": messages},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _opencode(prompt: str, system: str, model: str = "") -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = httpx.post(
        OPENCODE_URL,
        headers={"Authorization": f"Bearer {OPENCODE_API_KEY}"},
        json={"model": model or OPENCODE_MODEL, "messages": messages},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _opencode_tools(messages: list[dict], tools: list[dict], model: str = "", debug: bool = False) -> dict:
    """Tool calling nativo via OpenCode Go API (OpenAI-compatible)."""
    modelo = model or OPENCODE_MODEL
    if debug:
        print(f"\n\033[90m[DEBUG] Enviando {len(messages)} mensagens ao OpenCode Go (modelo={modelo})\033[0m")

    response = httpx.post(
        OPENCODE_URL,
        headers={"Authorization": f"Bearer {OPENCODE_API_KEY}"},
        json={"model": modelo, "messages": messages, "tools": tools, "tool_choice": "auto"},
        timeout=60,
    )
    response.raise_for_status()
    msg = response.json()["choices"][0]["message"]

    if debug:
        import json as _json
        print(f"\033[90m[DEBUG] Resposta raw do OpenCode Go:\033[0m")
        print(f"\033[93m{_json.dumps(msg, ensure_ascii=False, indent=2)}\033[0m\n")

    if msg.get("tool_calls"):
        tc = msg["tool_calls"][0]
        return {
            "type": "tool_call",
            "name": tc["function"]["name"],
            "arguments": json.loads(tc["function"]["arguments"]),
            "tool_call_id": tc["id"],
            "assistant_message": msg,
        }
    return {"type": "text", "content": msg.get("content", "").strip()}


def _ollama_tools(messages: list[dict], tools: list[dict], model: str, debug: bool = False) -> dict:
    """Tool calling via prompt engineering para Ollama."""
    tools_desc = _formatar_tools(tools)
    system_base = next((m["content"] for m in messages if m["role"] == "system"), "")
    system_com_tools = f"{system_base}\n\n{tools_desc}" if system_base else tools_desc

    msgs_com_system = [m for m in messages if m["role"] != "system"]
    msgs_final = [{"role": "system", "content": system_com_tools}] + msgs_com_system

    if debug:
        import json as _json
        print(f"\n\033[90m[DEBUG] Mensagens enviadas ao LLM ({len(msgs_final)} msgs, modelo={model}):\033[0m")
        for m in msgs_final:
            role = m["role"]
            conteudo_preview = m["content"][:300] + ("…" if len(m["content"]) > 300 else "")
            print(f"\033[90m  [{role}] {conteudo_preview}\033[0m")

    payload = {
        "model": model,
        "messages": msgs_final,
        "stream": False,
        "format": "json",
        "options": {"temperature": OLLAMA_TEMPERATURE, "think": False},
    }

    response = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    response.raise_for_status()
    conteudo = response.json()["message"]["content"].strip()

    if debug:
        print(f"\n\033[90m[DEBUG] Resposta raw do LLM:\033[0m")
        print(f"\033[93m{conteudo}\033[0m")

    resultado = _parsear_resposta_tools(conteudo)

    if debug:
        print(f"\n\033[90m[DEBUG] Parsed: {resultado}\033[0m\n")

    return resultado


def _groq_tools(messages: list[dict], tools: list[dict], debug: bool = False) -> dict:
    """Tool calling nativo via Groq API."""
    if debug:
        print(f"\n\033[90m[DEBUG] Enviando {len(messages)} mensagens ao Groq (modelo={GROQ_MODEL})\033[0m")

    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": GROQ_MODEL, "messages": messages, "tools": tools, "tool_choice": "auto"},
        timeout=30,
    )
    response.raise_for_status()
    msg = response.json()["choices"][0]["message"]

    if debug:
        import json as _json
        print(f"\033[90m[DEBUG] Resposta raw do Groq:\033[0m")
        print(f"\033[93m{_json.dumps(msg, ensure_ascii=False, indent=2)}\033[0m\n")

    if msg.get("tool_calls"):
        tc = msg["tool_calls"][0]
        return {
            "type": "tool_call",
            "name": tc["function"]["name"],
            "arguments": json.loads(tc["function"]["arguments"]),
            "tool_call_id": tc["id"],
            "assistant_message": msg,
        }
    return {"type": "text", "content": msg.get("content", "").strip()}


def _formatar_tools(tools: list[dict]) -> str:
    linhas = [
        "Você tem acesso às seguintes ferramentas. Para usar uma, responda APENAS com JSON válido no formato:",
        '{"tool": "<nome>", "arguments": {<parametros>}}',
        "",
        "Para responder sem usar ferramenta:",
        '{"tool": null, "response": "<sua resposta>"}',
        "",
        "Ferramentas disponíveis:",
    ]
    for t in tools:
        fn = t.get("function", t)
        params = fn.get("parameters", {}).get("properties", {})
        desc_params = ", ".join(
            f'{k}: {v.get("description", v.get("type", ""))}' for k, v in params.items()
        )
        linhas.append(f'- {fn["name"]}({desc_params}): {fn.get("description", "")}')
    return "\n".join(linhas)


def _parsear_resposta_tools(conteudo: str) -> dict:
    # limpa blocos markdown
    conteudo = re.sub(r"```(?:json)?\s*", "", conteudo).strip().rstrip("`").strip()
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", conteudo, re.DOTALL)
        if match:
            try:
                dados = json.loads(match.group())
            except json.JSONDecodeError:
                return {"type": "text", "content": conteudo}
        else:
            return {"type": "text", "content": conteudo}

    if dados.get("tool") and dados["tool"] is not None:
        return {
            "type": "tool_call",
            "name": dados["tool"],
            "arguments": dados.get("arguments", {}),
        }
    return {"type": "text", "content": dados.get("response", conteudo)}
