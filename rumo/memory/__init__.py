"""
API pública de memória — compatível com a interface do memory.py original.
Delega para long_term.py (persistente) e session.py (sessão atual).
"""
from rumo.memory.long_term import get as _lt
from rumo.memory.session import get as _session


# --- API compatível com memory.py ---

def salvar(descricao: str, comando: str) -> None:
    _lt().salvar_comando(descricao, comando)


def buscar_exato(descricao: str) -> str | None:
    return _lt().buscar_exato(descricao)


def contexto_para_llm() -> str:
    return _lt().contexto_para_llm()


def listar() -> list[dict]:
    return _lt().listar_comandos()


def remover(descricao: str) -> bool:
    return _lt().remover_comando(descricao)


# --- API de sessão (nova) ---

def iniciar_sessao(cwd: str, shell: str, os_info: str) -> None:
    _session().iniciar(cwd, shell, os_info)


def registrar_comando(comando: str, saida: str, sucesso: bool) -> None:
    _session().registrar_comando(comando, saida, sucesso)


def registrar_erro(erro: str) -> None:
    _session().registrar_erro(erro)


def contexto_sessao_para_llm() -> str:
    return _session().contexto_para_llm()
