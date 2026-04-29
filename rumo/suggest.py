import platform
from rumo import llm

SYSTEM = """Você é um especialista em linha de comando.
Dado um pedido em linguagem natural, responda APENAS com:
1. O comando exato (em uma linha, sem markdown, sem backticks)
2. Uma linha em branco
3. Uma explicação curta em português (máximo 2 linhas)

Sistema operacional: {os}
Shell: {shell}
Não inclua mais nada na resposta."""


def sugerir(descricao: str) -> tuple[str, str]:
    sistema = SYSTEM.format(os=platform.system(), shell=_shell())
    resposta = llm.complete(descricao, system=sistema)
    partes = resposta.split("\n\n", 1)
    comando = partes[0].strip().strip("`")
    explicacao = partes[1].strip() if len(partes) > 1 else ""
    return comando, explicacao


def _shell() -> str:
    import os
    return os.getenv("SHELL", "bash").split("/")[-1]
