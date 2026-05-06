from pathlib import Path
from rumo.plugins import PLUGINS_DIR


def adicionar_plugin(nome: str, conteudo: str | None = None) -> Path:
    """Cria ~/.rumo/plugins/<nome>.md. Se conteudo=None, cria template vazio."""
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    path = PLUGINS_DIR / f"{nome}.md"
    path.write_text(conteudo if conteudo is not None else gerar_template(nome))
    return path


def remover_plugin(nome: str) -> bool:
    """Remove ~/.rumo/plugins/<nome>.md. Retorna True se removido."""
    path = PLUGINS_DIR / f"{nome}.md"
    if path.exists():
        path.unlink()
        return True
    return False


def listar_detalhado() -> list[dict]:
    """Retorna metadados de cada plugin instalado."""
    if not PLUGINS_DIR.exists():
        return []
    result = []
    for f in sorted(PLUGINS_DIR.glob("*.md")):
        conteudo = f.read_text()
        descricao = ""
        linhas = conteudo.splitlines()
        for i, linha in enumerate(linhas):
            if linha.strip() == "## Descrição" and i + 1 < len(linhas):
                descricao = linhas[i + 1].strip()
                break
        stat = f.stat()
        result.append({
            "nome": f.stem,
            "path": str(f),
            "tamanho_kb": round(stat.st_size / 1024, 1),
            "descricao": descricao,
        })
    return result


def gerar_template(nome: str) -> str:
    nome_capitalizado = nome.capitalize()
    return (
        f"# Plugin: {nome_capitalizado}\n\n"
        f"## Descrição\n"
        f"Descreva o que esta ferramenta faz.\n\n"
        f"## Comandos Essenciais\n"
        f"- `{nome} --help` — mostra ajuda\n\n"
        f"## Exemplos\n"
        f"```bash\n"
        f"# Exemplo de uso\n"
        f"{nome} --version\n"
        f"```\n\n"
        f"## Notas de Segurança\n"
        f"Nenhuma nota especial.\n"
    )
