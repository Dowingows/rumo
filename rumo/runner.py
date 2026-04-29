import re
import shutil
import subprocess
import typer
from rich.console import Console
from rich.prompt import Confirm
from rumo.suggest import sugerir
from rumo import llm

console = Console()

SYSTEM_INSTALAR = """Você é um especialista em macOS.
O nome abaixo é um comando que não está instalado. Responda APENAS com:
- Linha 1: o comando brew para instalar (ex: brew install iproute2mac)
- Linha 2: em branco
- Linha 3: uma frase curta explicando o que o pacote faz

Use SOMENTE brew. Não use apt, yum ou qualquer outro gerenciador. Não numere as linhas."""


def _binario(comando: str) -> str:
    """Extrai o nome do primeiro binário de um comando shell."""
    token = re.split(r"[\s|;&]", comando.strip())[0]
    return token.lstrip("(").strip()


def _sugerir_instalacao(binario: str) -> None:
    console.print(f"\n[bold yellow]'{binario}' não encontrado no sistema.[/bold yellow]")
    console.print("[dim]Buscando como instalar...[/dim]\n")
    resposta = llm.complete(binario, system=SYSTEM_INSTALAR)
    partes = resposta.split("\n\n", 1)
    cmd_install = partes[0].strip().strip("`")
    explicacao = partes[1].strip() if len(partes) > 1 else ""
    console.print(f"[bold green]Para instalar:[/bold green] [yellow]{cmd_install}[/yellow]")
    if explicacao:
        console.print(f"[dim]{explicacao}[/dim]")


def executar(descricao: str, sim: bool = False) -> None:
    console.print("\n[bold cyan]Gerando comando...[/bold cyan]")
    comando, explicacao = sugerir(descricao)

    console.print(f"\n[bold green]Comando:[/bold green] [yellow]{comando}[/yellow]")
    if explicacao:
        console.print(f"[dim]{explicacao}[/dim]")

    binario = _binario(comando)
    if binario and not shutil.which(binario):
        _sugerir_instalacao(binario)
        raise typer.Exit()

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
