import json
import re
from datetime import datetime
from pathlib import Path

LONG_TERM_PATH = Path.home() / ".rumo" / "memory" / "long_term.md"

_TEMPLATE = """# Memória de Longo Prazo

## Comandos com Sucesso

## Erros Resolvidos

## Padrões do Usuário
"""


class LongTermMemory:
    def __init__(self, path: Path = LONG_TERM_PATH):
        self.path = path

    def _garantir(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(_TEMPLATE)

    def _ler(self) -> str:
        self._garantir()
        return self.path.read_text()

    def salvar_comando(self, descricao: str, comando: str) -> None:
        texto = self._ler()
        agora = datetime.now().isoformat(timespec="seconds")
        entrada = (
            f"\n### {descricao}\n"
            f"- **comando**: `{comando}`\n"
            f"- **salvo_em**: {agora}\n"
            f"- **usos**: 1\n"
        )
        # atualiza contagem se já existe
        padrao = re.compile(
            rf"(### {re.escape(descricao)}\n- \*\*comando\*\*: `[^`]+`\n- \*\*salvo_em\*\*: [^\n]+\n- \*\*usos\*\*: )(\d+)",
        )
        match = padrao.search(texto)
        if match:
            usos = int(match.group(2)) + 1
            novo_texto = padrao.sub(
                rf"\g<1>{usos}",
                re.sub(
                    rf"(### {re.escape(descricao)}\n- \*\*comando\*\*: )`[^`]+`",
                    rf"\1`{comando}`",
                    texto,
                ),
            )
            self.path.write_text(novo_texto)
            return

        # insere nova entrada na seção "Comandos com Sucesso"
        novo_texto = texto.replace("## Comandos com Sucesso\n", f"## Comandos com Sucesso\n{entrada}")
        self.path.write_text(novo_texto)

    def buscar_exato(self, descricao: str) -> str | None:
        texto = self._ler()
        padrao = re.compile(
            rf"### {re.escape(descricao)}\n- \*\*comando\*\*: `([^`]+)`"
        )
        match = padrao.search(texto)
        return match.group(1) if match else None

    def listar_comandos(self) -> list[dict]:
        texto = self._ler()
        padrao = re.compile(
            r"### (.+?)\n- \*\*comando\*\*: `([^`]+)`\n- \*\*salvo_em\*\*: ([^\n]+)\n- \*\*usos\*\*: (\d+)"
        )
        return [
            {"descricao": m.group(1), "comando": m.group(2),
             "salvo_em": m.group(3), "usos": int(m.group(4))}
            for m in padrao.finditer(texto)
        ]

    def remover_comando(self, descricao: str) -> bool:
        texto = self._ler()
        padrao = re.compile(
            rf"\n### {re.escape(descricao)}\n(?:- [^\n]+\n)*",
            re.MULTILINE,
        )
        novo_texto, n = padrao.subn("", texto)
        if n:
            self.path.write_text(novo_texto)
        return n > 0

    def salvar_erro_resolvido(self, erro: str, causa: str, solucao: str) -> None:
        texto = self._ler()
        agora = datetime.now().isoformat(timespec="seconds")
        entrada = (
            f"\n### {erro}\n"
            f"- **causa**: {causa}\n"
            f"- **solucao**: `{solucao}`\n"
            f"- **resolvido_em**: {agora}\n"
        )
        novo_texto = texto.replace("## Erros Resolvidos\n", f"## Erros Resolvidos\n{entrada}")
        self.path.write_text(novo_texto)

    def contexto_para_llm(self) -> str:
        comandos = self.listar_comandos()
        if not comandos:
            return ""
        linhas = ["Correções salvas pelo usuário (use como prioridade máxima se for relevante):"]
        for c in comandos:
            linhas.append(f'- "{c["descricao"]}" → {c["comando"]}')
        return "\n".join(linhas)

    def migrar_de_json(self, json_path: Path) -> int:
        """Importa entradas de memory.json para long_term.md. Retorna número de entradas migradas."""
        if not json_path.exists():
            return 0
        try:
            entradas = json.loads(json_path.read_text())
        except Exception:
            return 0
        count = 0
        for e in entradas:
            if e.get("descricao") and e.get("comando"):
                self.salvar_comando(e["descricao"], e["comando"])
                count += 1
        return count


_instance: LongTermMemory | None = None


def get() -> LongTermMemory:
    global _instance
    if _instance is None:
        _instance = LongTermMemory()
        # migração automática na primeira vez
        json_path = Path.home() / ".rumo" / "memory.json"
        lt_path = Path.home() / ".rumo" / "memory" / "long_term.md"
        if json_path.exists() and not lt_path.exists():
            _instance.migrar_de_json(json_path)
    return _instance
