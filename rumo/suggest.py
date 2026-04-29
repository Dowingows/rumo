import os
import platform
from rumo import llm

SYSTEM = """Você é um especialista em linha de comando.
Dado um pedido em linguagem natural, responda APENAS com:
1. O comando exato (em uma linha, sem markdown, sem backticks)
2. Uma linha em branco
3. Uma explicação curta em português (máximo 2 linhas)

Sistema operacional: {os}
Shell: {shell}
Use APENAS comandos nativos disponíveis neste sistema. Não sugira comandos de outros sistemas operacionais.
Não inclua mais nada na resposta."""


def sugerir(descricao: str) -> tuple[str, str]:
    sistema = SYSTEM.format(os=_os_info(), shell=_shell())
    resposta = llm.complete(descricao, system=sistema)
    partes = resposta.split("\n\n", 1)
    comando = partes[0].strip().strip("`")
    explicacao = partes[1].strip() if len(partes) > 1 else ""
    return comando, explicacao


def _os_info() -> str:
    system = platform.system()
    if system == "Darwin":
        version = platform.mac_ver()[0]
        arch = platform.machine()
        return f"macOS {version} ({arch}) — use ifconfig, not ip; use brew para instalar pacotes"
    if system == "Linux":
        try:
            info = platform.freedesktop_os_release()
            return f"Linux {info.get('PRETTY_NAME', platform.version())} ({platform.machine()})"
        except Exception:
            return f"Linux {platform.version()} ({platform.machine()})"
    return f"{system} {platform.version()}"


def _shell() -> str:
    return os.getenv("SHELL", "bash").split("/")[-1]
