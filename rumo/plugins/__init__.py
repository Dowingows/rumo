from pathlib import Path

PLUGINS_DIR = Path.home() / ".rumo" / "plugins"


def carregar_plugin(nome: str) -> str | None:
    """Lê e retorna o conteúdo do plugin, ou None se não existir."""
    for candidato in [PLUGINS_DIR / f"{nome}.md", PLUGINS_DIR / nome / "index.md"]:
        if candidato.exists():
            return candidato.read_text()
    return None


def listar_plugins() -> list[dict]:
    """Retorna lista de plugins instalados com metadados básicos."""
    if not PLUGINS_DIR.exists():
        return []
    result = []
    for f in sorted(PLUGINS_DIR.glob("*.md")):
        nome = f.stem
        conteudo = f.read_text()
        primeira_linha = next(
            (l.lstrip("# ").strip() for l in conteudo.splitlines() if l.strip()),
            nome,
        )
        result.append({
            "nome": nome,
            "path": str(f),
            "tamanho_kb": round(f.stat().st_size / 1024, 1),
            "titulo": primeira_linha,
        })
    return result


def plugin_para_tarefa(tarefa: str) -> str | None:
    """Detecta se algum plugin instalado é relevante para a tarefa, por palavras-chave."""
    if not PLUGINS_DIR.exists():
        return None
    tokens = set(tarefa.lower().split())
    for f in PLUGINS_DIR.glob("*.md"):
        nome = f.stem.lower()
        if nome in tokens or any(t.startswith(nome) or nome.startswith(t) for t in tokens if len(t) > 2):
            return f.read_text()
    return None


def contexto_plugins_para_llm(tarefa: str) -> str:
    """Retorna o conteúdo do(s) plugin(s) relevante(s) para injetar no system prompt."""
    if not PLUGINS_DIR.exists():
        return ""
    tokens = set(tarefa.lower().split())
    blocos = []
    for f in PLUGINS_DIR.glob("*.md"):
        nome = f.stem.lower()
        if nome in tokens or any(t.startswith(nome) or nome.startswith(t) for t in tokens if len(t) > 2):
            blocos.append(f"## Plugin Ativo: {f.stem.capitalize()}\n{f.read_text()}")
    return "\n\n".join(blocos)
