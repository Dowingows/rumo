import re
from pathlib import Path

CONFIG_PATH = Path.home() / ".rumo" / "config.md"
CREDENTIALS_PATH = Path.home() / ".rumo" / ".env"

TYPES = {
    "max_iterations": int,
    "backend": str,
    "modelo_agente": str,
    "modelo_executar": str,
    "modelo_diagnosticar": str,
    "confirmar_criticas": lambda v: v.lower() in ("true", "yes", "1"),
    "verbose": lambda v: v.lower() in ("true", "yes", "1"),
}

DEFAULTS = {
    "max_iterations": 10,
    "backend": "",
    "modelo_agente": "qwen3:4b",
    "modelo_executar": "qwen3:4b",
    "modelo_diagnosticar": "qwen3:4b",
    "confirmar_criticas": True,
    "verbose": False,
}

DEFAULT_CONFIG = """# Configuração do Rumo

## Agente
- **max_iterations**: 10
- **modelo_agente**: qwen3:4b
  Modelos recomendados: qwen3:4b (padrão), qwen3:8b (mais capaz), qwen2.5:7b

## Comandos
- **modelo_executar**: qwen3:4b
- **modelo_diagnosticar**: qwen3:4b

## Comportamento
- **confirmar_criticas**: true
- **verbose**: false
"""


def _parse_markdown(text: str) -> dict:
    resultado = {}
    for match in re.finditer(r"- \*\*(\w+)\*\*:\s+(\S+)", text):
        chave, valor = match.group(1), match.group(2).strip()
        if chave in TYPES:
            try:
                resultado[chave] = TYPES[chave](valor)
            except (ValueError, AttributeError):
                pass
    return resultado


def carregar() -> dict:
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    try:
        texto = CONFIG_PATH.read_text()
        parsed = _parse_markdown(texto)
        return {**DEFAULTS, **parsed}
    except OSError:
        return dict(DEFAULTS)


def salvar(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    backend = cfg.get("backend", DEFAULTS["backend"]) or "ollama"
    conteudo = f"""# Configuração do Rumo

## Backend
- **backend**: {backend}
  Opções: ollama (local), groq (API gratuita), opencode (OpenCode Go)

## Agente
- **max_iterations**: {cfg.get('max_iterations', DEFAULTS['max_iterations'])}
- **modelo_agente**: {cfg.get('modelo_agente', DEFAULTS['modelo_agente'])}

## Comandos
- **modelo_executar**: {cfg.get('modelo_executar', DEFAULTS['modelo_executar'])}
- **modelo_diagnosticar**: {cfg.get('modelo_diagnosticar', DEFAULTS['modelo_diagnosticar'])}

## Comportamento
- **confirmar_criticas**: {str(cfg.get('confirmar_criticas', DEFAULTS['confirmar_criticas'])).lower()}
- **verbose**: {str(cfg.get('verbose', DEFAULTS['verbose'])).lower()}
"""
    CONFIG_PATH.write_text(conteudo)


def salvar_credencial(chave: str, valor: str) -> None:
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    conteudo = CREDENTIALS_PATH.read_text() if CREDENTIALS_PATH.exists() else ""
    if re.search(rf"^{chave}=", conteudo, re.MULTILINE):
        conteudo = re.sub(rf"^{chave}=.*$", f"{chave}={valor}", conteudo, flags=re.MULTILINE)
    else:
        conteudo = conteudo.rstrip("\n") + f"\n{chave}={valor}\n"
    CREDENTIALS_PATH.write_text(conteudo.lstrip("\n"))


def ler_credencial(chave: str) -> str:
    if not CREDENTIALS_PATH.exists():
        return ""
    for linha in CREDENTIALS_PATH.read_text().splitlines():
        if linha.startswith(f"{chave}="):
            return linha[len(chave) + 1:].strip()
    return ""


def garantir_config_padrao() -> None:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(DEFAULT_CONFIG)
