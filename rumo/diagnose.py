import sys
from rumo import llm, config
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

SYSTEM = """Você é um especialista em linha de comando e sistemas Unix/Linux.
Analise a saída de erro abaixo e responda em português:
1. O que causou o erro (em 1 linha)
2. Como corrigir (passos objetivos, máximo 4)

Seja direto e prático. Use markdown simples."""


def diagnosticar(erro: str | None = None) -> None:
    if erro is None:
        if not sys.stdin.isatty():
            erro = sys.stdin.read().strip()
        else:
            console.print("[bold red]Forneça o erro via argumento ou pipe.[/bold red]")
            console.print("  Exemplo: [dim]command 2>&1 | rumo diagnosticar[/dim]")
            console.print("  Exemplo: [dim]rumo diagnosticar 'No such file or directory'[/dim]")
            return

    if not erro:
        console.print("[dim]Nenhum erro fornecido.[/dim]")
        return

    cfg = config.carregar()
    modelo = cfg.get("modelo_diagnosticar", "")
    console.print("\n[bold cyan]Analisando erro...[/bold cyan]\n")
    resposta = llm.complete(erro, system=SYSTEM, model=modelo)
    console.print(Panel(Markdown(resposta), title="[bold red]Diagnóstico[/bold red]", border_style="red"))
