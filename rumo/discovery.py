import os
import shutil
import subprocess

TOOL_CATEGORIES: dict[str, list[str]] = {
    "containers": ["docker", "podman", "kubectl", "helm", "k9s", "docker-compose"],
    "linguagens": ["python3", "python", "node", "ruby", "go", "rust", "cargo", "java", "php"],
    "gerenciadores": ["pip", "npm", "yarn", "pnpm", "brew", "apt", "yum", "uv", "cargo"],
    "git": ["git", "gh", "hub", "glab"],
    "editores": ["nvim", "vim", "nano", "code", "cursor", "emacs"],
    "rede": ["curl", "wget", "http", "nc", "nmap", "ssh", "rsync"],
    "busca": ["rg", "fzf", "fd", "ag", "grep"],
    "dados": ["jq", "yq", "sqlite3", "psql", "mysql"],
    "monitoramento": ["htop", "btop", "glances", "tmux", "screen"],
    "infra": ["terraform", "ansible", "vagrant"],
    "ollama": ["ollama"],
}


def descobrir_ferramentas() -> dict[str, list[str]]:
    """Retorna apenas as ferramentas que estão instaladas, por categoria."""
    resultado = {}
    for categoria, ferramentas in TOOL_CATEGORIES.items():
        instaladas = [f for f in ferramentas if shutil.which(f)]
        if instaladas:
            resultado[categoria] = instaladas
    return resultado


def listar_todos_binarios() -> list[str]:
    """Escaneia $PATH e retorna lista ordenada de executáveis."""
    binarios: set[str] = set()
    for diretorio in os.getenv("PATH", "").split(":"):
        try:
            for nome in os.listdir(diretorio):
                if not nome.startswith("."):
                    binarios.add(nome)
        except OSError:
            pass
    return sorted(binarios)


def verificar_ferramenta(nome: str) -> dict:
    """Retorna {instalado, path, versao} para uma ferramenta específica."""
    path = shutil.which(nome)
    if not path:
        return {"instalado": False, "path": "", "versao": ""}
    return {"instalado": True, "path": path, "versao": _versao_ferramenta(nome)}


def contexto_para_llm() -> str:
    """Formata ferramentas instaladas para injetar no system prompt do agente."""
    ferramentas = descobrir_ferramentas()
    if not ferramentas:
        return ""
    linhas = ["Ferramentas instaladas neste sistema:"]
    for categoria, lista in ferramentas.items():
        linhas.append(f"- {categoria}: {', '.join(lista)}")
    return "\n".join(linhas)


def _versao_ferramenta(nome: str) -> str:
    try:
        r = subprocess.run([nome, "--version"], capture_output=True, text=True, timeout=3)
        saida = (r.stdout or r.stderr or "").strip()
        return saida.splitlines()[0] if saida else ""
    except Exception:
        return ""
