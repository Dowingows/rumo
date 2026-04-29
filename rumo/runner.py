import subprocess
import typer
from rich.console import Console
from rich.prompt import Confirm
from rumo.suggest import sugerir

console = Console()


def executar(descricao: str, sim: bool = False) -> None:
    console.print("\n[bold cyan]Gerando comando...[/bold cyan]")
    comando, explicacao = sugerir(descricao)

    console.print(f"\n[bold green]Comando:[/bold green] [yellow]{comando}[/yellow]")
    if explicacao:
        console.print(f"[dim]{explicacao}[/dim]")

    if not sim:
        confirmar = Confirm.ask("\n[bold]Executar?[/bold]", default=True)
        if not confirmar:
            console.print("[dim]Cancelado.[/dim]")
            raise typer.Exit()

    console.print()
    resultado = subprocess.run(comando, shell=True, text=True)
    if resultado.returncode != 0:
        console.print(f"\n[bold red]Saiu com código {resultado.returncode}[/bold red]")
        console.print("[dim]Dica: use [bold]rumo diagnosticar[/bold] para entender o erro.[/dim]")
