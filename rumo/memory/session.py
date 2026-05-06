from datetime import datetime
from pathlib import Path

SESSION_PATH = Path.home() / ".rumo" / "memory" / "session.md"


class SessionMemory:
    def __init__(self, path: Path = SESSION_PATH):
        self.path = path
        self.cwd = ""
        self.shell = ""
        self.os_info = ""
        self.iniciado_em = ""
        self.ultimo_comando = ""
        self.ultima_saida = ""
        self.ultimo_erro = ""

    def iniciar(self, cwd: str, shell: str, os_info: str) -> None:
        self.cwd = cwd
        self.shell = shell
        self.os_info = os_info
        self.iniciado_em = datetime.now().isoformat(timespec="seconds")
        self.ultimo_comando = ""
        self.ultima_saida = ""
        self.ultimo_erro = ""
        self._salvar()

    def registrar_comando(self, comando: str, saida: str, sucesso: bool) -> None:
        self.ultimo_comando = comando
        self.ultima_saida = saida[:500] if saida else ""
        if sucesso:
            self.ultimo_erro = ""
        self._salvar()

    def registrar_erro(self, erro: str) -> None:
        self.ultimo_erro = erro[:300] if erro else ""
        self._salvar()

    def contexto_para_llm(self) -> str:
        if not self.iniciado_em:
            return ""
        linhas = [f"Sessão anterior ({self.iniciado_em}):"]
        if self.ultimo_comando:
            linhas.append(f"- último comando: `{self.ultimo_comando}`")
        if self.ultimo_erro:
            linhas.append(f"- último erro: {self.ultimo_erro}")
        return "\n".join(linhas)

    def _salvar(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self._template())

    def _template(self) -> str:
        cmd_bloco = f"```bash\n{self.ultimo_comando}\n```" if self.ultimo_comando else "Nenhum"
        saida = self.ultima_saida or ""
        erro = self.ultimo_erro or "Nenhum erro nesta sessão."
        return (
            f"# Sessão Atual\n\n"
            f"## Contexto\n"
            f"- **data**: {self.iniciado_em}\n"
            f"- **cwd**: {self.cwd}\n"
            f"- **shell**: {self.shell}\n"
            f"- **os**: {self.os_info}\n\n"
            f"## Último Comando Executado\n"
            f"{cmd_bloco}\n"
            f"{('Saída: ' + saida) if saida else ''}\n\n"
            f"## Erro Mais Recente\n"
            f"{erro}\n"
        )


_instance: SessionMemory | None = None


def get() -> SessionMemory:
    global _instance
    if _instance is None:
        _instance = SessionMemory()
    return _instance
