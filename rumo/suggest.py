import os
import platform
import re
import shutil
import subprocess
from rumo import llm

_FERRAMENTAS_EXTRAS = [
    "ollama", "docker", "kubectl", "git", "gh", "brew", "node", "python3",
    "pip", "uv", "cargo", "go", "java", "ruby", "php", "ffmpeg", "yt-dlp",
    "jq", "fzf", "ripgrep", "rg", "bat", "htop", "tmux", "nvim", "code",
]

SYSTEM = """Você é um especialista em linha de comando.
Dado um pedido em linguagem natural, responda APENAS com:
1. O comando exato (em UMA única linha, sem markdown, sem backticks, sem quebra de linha)
2. Uma linha em branco
3. Uma explicação curta em português (máximo 2 linhas)

Se o pedido for ambíguo ou você precisar de mais detalhes para gerar o comando correto, responda APENAS com:
PERGUNTA: <sua pergunta objetiva em português>

Sistema operacional: {os}
Shell: {shell}
Diretório home do usuário: {home}
Use APENAS comandos nativos disponíveis neste sistema. Não sugira comandos de outros sistemas operacionais.
Use o caminho real do home ({home}) em vez de /Users/username ou ~.
Não inclua mais nada na resposta.{memoria}{help}"""


def sugerir(descricao: str) -> tuple[str, str]:
    from rumo import memory

    # memória tem prioridade — retorna imediatamente se há correspondência exata
    salvo = memory.buscar_exato(descricao)
    if salvo:
        return salvo, "(da memória)"

    ctx_memoria = memory.contexto_para_llm()
    ctx_help = _help_da_ferramenta(descricao)
    sistema = SYSTEM.format(
        os=_os_info(),
        shell=_shell(),
        home=os.path.expanduser("~"),
        memoria=f"\n{ctx_memoria}" if ctx_memoria else "",
        help=f"\n{ctx_help}" if ctx_help else "",
    )
    resposta = llm.complete(descricao, system=sistema)

    linha = resposta.strip().splitlines()[0].strip() if resposta.strip() else ""
    if linha.upper().startswith("PERGUNTA:"):
        pergunta = linha[len("PERGUNTA:"):].strip()
        return f"PERGUNTA:{pergunta}", ""

    partes = resposta.split("\n\n", 1)
    comando = next((l.strip().strip("`") for l in partes[0].splitlines() if l.strip()), "")
    explicacao = partes[1].strip() if len(partes) > 1 else ""
    return comando, explicacao


def _os_info() -> str:
    system = platform.system()
    if system == "Darwin":
        version = platform.mac_ver()[0]
        arch = platform.machine()
        return (
            f"macOS {version} ({arch})\n"
            "Comandos nativos obrigatórios no macOS (NÃO use equivalentes Linux):\n"
            "- RAM/memória: vm_stat ou sysctl hw.memsize ou top -l 1 | grep PhysMem\n"
            "- Rede/IP: ifconfig (nunca ip addr)\n"
            "- Processos: ps aux ou top (nunca free)\n"
            "- Disco: df -h ou diskutil\n"
            "- Data e hora: date (ex: date '+%H:%M:%S' para hora, date '+%d/%m/%Y' para data)\n"
            "- Bateria: pmset -g batt\n"
            "- Hardware info: system_profiler SPHardwareDataType\n"
            "- Instalar pacotes: brew install <pacote>"
            + _ferramentas_instaladas()
        )
    if system == "Linux":
        try:
            info = platform.freedesktop_os_release()
            return f"Linux {info.get('PRETTY_NAME', platform.version())} ({platform.machine()})"
        except Exception:
            return f"Linux {platform.version()} ({platform.machine()})"
    return f"{system} {platform.version()}"


def _shell() -> str:
    return os.getenv("SHELL", "bash").split("/")[-1]


def _ferramentas_instaladas() -> str:
    encontradas = [t for t in _FERRAMENTAS_EXTRAS if shutil.which(t)]
    if not encontradas:
        return ""
    return "\nFerramentas instaladas neste sistema: " + ", ".join(encontradas)


def _detectar_ferramenta(descricao: str) -> str | None:
    palavras = set(re.findall(r"[a-zA-Z0-9_.-]+", descricao.lower()))
    for palavra in palavras:
        if shutil.which(palavra):
            return palavra
    return None


def _help_da_ferramenta(descricao: str) -> str:
    ferramenta = _detectar_ferramenta(descricao)
    if not ferramenta:
        return ""
    try:
        resultado = subprocess.run(
            [ferramenta, "--help"],
            capture_output=True, text=True, timeout=5,
        )
        saida = (resultado.stdout or resultado.stderr or "").strip()
        if not saida:
            return ""
        linhas = saida.splitlines()[:60]
        return f"\nDocumentação de '{ferramenta}' (--help):\n" + "\n".join(linhas)
    except Exception:
        return ""
