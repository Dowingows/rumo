import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer(
    name="rumo",
    help="CLI inteligente para terminal: sugira, execute e diagnostique comandos.",
    no_args_is_help=True,
)
console = Console()


@app.command("sugerir")
def cmd_sugerir(
    descricao: str = typer.Argument(..., help="O que você quer fazer em linguagem natural"),
):
    """Sugere um comando de terminal para o que você quer fazer."""
    from rumo.suggest import sugerir

    console.print("\n[bold cyan]Pensando...[/bold cyan]")
    try:
        comando, explicacao = sugerir(descricao)
    except Exception as e:
        console.print(f"[bold red]Erro ao consultar LLM:[/bold red] {e}")
        raise typer.Exit(1)

    conteudo = f"```\n{comando}\n```"
    if explicacao:
        conteudo += f"\n\n{explicacao}"
    console.print(Panel(Markdown(conteudo), title="[bold green]Sugestão[/bold green]", border_style="green"))


@app.command("executar")
def cmd_executar(
    descricao: str = typer.Argument(..., help="O que você quer executar em linguagem natural"),
    sim: bool = typer.Option(False, "--sim", "-s", help="Executa sem pedir confirmação"),
):
    """Gera e executa um comando a partir de linguagem natural."""
    from rumo.runner import executar

    try:
        executar(descricao, sim=sim)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("diagnosticar")
def cmd_diagnosticar(
    erro: Optional[str] = typer.Argument(None, help="Mensagem de erro (ou use pipe)"),
):
    """Diagnostica um erro de terminal e explica como corrigir.

    Uso com pipe: comando 2>&1 | rumo diagnosticar
    """
    from rumo.diagnose import diagnosticar

    try:
        diagnosticar(erro)
    except Exception as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("memoria")
def cmd_memoria(
    limpar: Optional[str] = typer.Option(None, "--remover", "-r", help="Remove uma entrada pela descrição"),
):
    """Lista os comandos aprendidos e salvos na memória."""
    from rumo import memory

    if limpar:
        if memory.remover(limpar):
            console.print(f"[bold green]Removido:[/bold green] {limpar}")
        else:
            console.print(f"[bold red]Não encontrado:[/bold red] {limpar}")
        return

    entradas = memory.listar()
    if not entradas:
        console.print("[dim]Nenhum comando na memória ainda.[/dim]")
        console.print("Quando um comando falhar, o rumo vai te perguntar o correto e salvar aqui.")
        return

    console.print(f"\n[bold]Memória do rumo[/bold] — {len(entradas)} entrada(s)\n")
    for e in entradas:
        data = e.get("atualizado_em") or e.get("criado_em", "")
        console.print(f"[bold cyan]{e['descricao']}[/bold cyan]")
        console.print(f"  [yellow]{e['comando']}[/yellow]")
        if data:
            console.print(f"  [dim]{data}[/dim]")
        console.print()


if __name__ == "__main__":
    app()
