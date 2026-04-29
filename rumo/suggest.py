import os
import platform
from rumo import llm

SYSTEM = """Você é um especialista em linha de comando.
Dado um pedido em linguagem natural, responda APENAS com:
1. O comando exato (em UMA única linha, sem markdown, sem backticks, sem quebra de linha)
2. Uma linha em branco
3. Uma explicação curta em português (máximo 2 linhas)

Sistema operacional: {os}
Shell: {shell}
Diretório home do usuário: {home}
Use APENAS comandos nativos disponíveis neste sistema. Não sugira comandos de outros sistemas operacionais.
Use o caminho real do home ({home}) em vez de /Users/username ou ~.
Não inclua mais nada na resposta."""


def sugerir(descricao: str) -> tuple[str, str]:
    sistema = SYSTEM.format(os=_os_info(), shell=_shell(), home=os.path.expanduser("~"))
    resposta = llm.complete(descricao, system=sistema)
    partes = resposta.split("\n\n", 1)
    # garante apenas a primeira linha não-vazia como comando
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
            "- Bateria: pmset -g batt\n"
            "- Hardware info: system_profiler SPHardwareDataType\n"
            "- Instalar pacotes: brew install <pacote>"
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
