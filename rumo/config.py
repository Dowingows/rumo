import re
from pathlib import Path

CONFIG_PATH = Path.home() / ".rumo" / "config.md"

TYPES = {
    "max_iterations": int,
    "modelo_agente": str,
    "confirmar_criticas": lambda v: v.lower() in ("true", "yes", "1"),
    "verbose": lambda v: v.lower() in ("true", "yes", "1"),
}

DEFAULTS = {
    "max_iterations": 10,
    "modelo_agente": "qwen3:4b",
    "confirmar_criticas": True,
    "verbose": False,
}

DEFAULT_CONFIG = """# Configuração do Rumo

## Agente
- **max_iterations**: 10
- **modelo_agente**: qwen3:4b
  Modelos recomendados: qwen3:4b (padrão), qwen3:8b (mais capaz), qwen2.5:7b

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


def garantir_config_padrao() -> None:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(DEFAULT_CONFIG)
