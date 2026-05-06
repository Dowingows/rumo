import shutil
import subprocess
from pathlib import Path
from rumo import llm
from rumo.plugins.manager import adicionar_plugin

SYSTEM_LEARN = """Você é um especialista em CLI.
Dado o output de `{ferramenta} --help`, gere documentação estruturada em markdown.

Formato EXATO a seguir:

# Plugin: {ferramenta_cap}

## Descrição
<1-2 linhas descrevendo o que a ferramenta faz>

## Comandos Essenciais
<lista de 8-15 comandos mais úteis com descrição curta>

## Exemplos
<2-4 exemplos práticos com blocos de código bash>

## Notas de Segurança
<avisos importantes se aplicável, ou "Nenhuma nota especial.">

Responda APENAS com o markdown acima. Sem texto adicional."""


def aprender(ferramenta: str) -> Path:
    """
    Aprende uma ferramenta via --help e salva como plugin em ~/.rumo/plugins/<ferramenta>.md.
    Retorna o path do arquivo criado.
    """
    if not shutil.which(ferramenta):
        raise FileNotFoundError(f"Ferramenta '{ferramenta}' não encontrada no PATH.")

    help_text = _obter_help(ferramenta)
    markdown = _resumir_com_llm(ferramenta, help_text)
    path = adicionar_plugin(ferramenta, markdown)
    return path


def _obter_help(ferramenta: str) -> str:
    for variante in [[ferramenta, "--help"], [ferramenta, "help"], [ferramenta, "-h"]]:
        try:
            r = subprocess.run(variante, capture_output=True, text=True, timeout=10)
            saida = (r.stdout or r.stderr or "").strip()
            if saida:
                linhas = saida.splitlines()[:200]
                return "\n".join(linhas)
        except Exception:
            continue
    raise RuntimeError(f"Não foi possível obter ajuda de '{ferramenta}'.")


def _resumir_com_llm(ferramenta: str, help_text: str) -> str:
    system = SYSTEM_LEARN.format(
        ferramenta=ferramenta,
        ferramenta_cap=ferramenta.capitalize(),
    )
    return llm.complete(help_text, system=system)
