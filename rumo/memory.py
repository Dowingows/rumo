import json
import os
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(os.getenv("RUMO_MEMORY", Path.home() / ".rumo" / "memory.json"))


def _carregar() -> list[dict]:
    if not MEMORY_FILE.exists():
        return []
    try:
        return json.loads(MEMORY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _salvar_arquivo(entradas: list[dict]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(entradas, ensure_ascii=False, indent=2))


def salvar(descricao: str, comando: str) -> None:
    entradas = _carregar()
    # atualiza se já existe entrada para essa descrição
    for entrada in entradas:
        if entrada["descricao"].lower() == descricao.lower():
            entrada["comando"] = comando
            entrada["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
            _salvar_arquivo(entradas)
            return
    entradas.append({
        "descricao": descricao,
        "comando": comando,
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    })
    _salvar_arquivo(entradas)


def buscar_exato(descricao: str) -> str | None:
    for entrada in _carregar():
        if entrada["descricao"].lower() == descricao.lower():
            return entrada["comando"]
    return None


def contexto_para_llm() -> str:
    entradas = _carregar()
    if not entradas:
        return ""
    linhas = [f'- "{e["descricao"]}" → {e["comando"]}' for e in entradas]
    return (
        "Correções salvas pelo usuário (use como prioridade máxima se for relevante):\n"
        + "\n".join(linhas)
    )


def listar() -> list[dict]:
    return _carregar()


def remover(descricao: str) -> bool:
    entradas = _carregar()
    novas = [e for e in entradas if e["descricao"].lower() != descricao.lower()]
    if len(novas) == len(entradas):
        return False
    _salvar_arquivo(novas)
    return True
