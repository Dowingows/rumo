import re
import shutil
import subprocess
import typer
from rich.console import Console
from rich.prompt import Confirm
from rumo.suggest import sugerir, _os_info
from rumo import llm

console = Console()

SYSTEM_ALTERNATIVA = """Você é um especialista em linha de comando no {os}.
O comando '{binario}' não existe neste sistema operacional.

Responda APENAS com:
- Linha 1: o comando nativo equivalente para este OS (sem markdown, sem backticks)
- Linha 2: em branco
- Linha 3: uma frase curta explicando o comando sugerido

Se não houver nativo mas existir via brew, responda com: brew install <pacote>
Não numere as linhas. Não inclua mais nada."""


def _binario(comando: str) -> str:
    token = re.split(r"[\s|;&]", comando.strip())[0]
    return token.lstrip("(").strip()


def _sugerir_alternativa(binario: str, descricao_original: str, sim: bool = False) -> str | None:
    console.print(f"\n[bold yellow]'{binario}' não existe neste sistema.[/bold yellow]")
    console.print("[dim]Buscando alternativa nativa...[/dim]\n")

    prompt = f"Quero: {descricao_original}\nO comando '{binario}' não existe aqui. Qual o equivalente nativo?"
    resposta = llm.complete(
        prompt,
        system=SYSTEM_ALTERNATIVA.format(os=_os_info(), binario=binario),
    )
    partes = resposta.split("\n\n", 1)
    cmd_alt = partes[0].strip().strip("`")
    explicacao = partes[1].strip() if len(partes) > 1 else ""

    alt_binario = _binario(cmd_alt)
    if alt_binario and not shutil.which(alt_binario) and not cmd_alt.startswith("brew"):
        console.print(f"[bold red]Não encontrei um comando nativo para '{binario}' neste sistema.[/bold red]")
        console.print(f"[dim]Sugestão do modelo (pode requerer instalação): [yellow]{cmd_alt}[/yellow][/dim]")
        return None

    console.print(f"[bold green]Alternativa:[/bold green] [yellow]{cmd_alt}[/yellow]")
    if explicacao:
        console.print(f"[dim]{explicacao}[/dim]")

    if cmd_alt.startswith("brew"):
        return None

    if not sim:
        confirmar = Confirm.ask("\n[bold]Executar este comando?[/bold]", default=True)
        if not confirmar:
            console.print("[dim]Cancelado.[/dim]")
            return None

    return cmd_alt


def executar(descricao: str, sim: bool = False) -> None:
    console.print("\n[bold cyan]Gerando comando...[/bold cyan]")
    comando, explicacao = sugerir(descricao)

    console.print(f"\n[bold green]Comando:[/bold green] [yellow]{comando}[/yellow]")
    if explicacao:
        console.print(f"[dim]{explicacao}[/dim]")

    binario = _binario(comando)
    if binario and not shutil.which(binario):
        cmd_alt = _sugerir_alternativa(binario, descricao, sim=sim)
        if cmd_alt:
            console.print()
            resultado = subprocess.run(cmd_alt, shell=True, text=True)
            if resultado.returncode != 0:
                console.print(f"\n[bold red]Saiu com código {resultado.returncode}[/bold red]")
                console.print("[dim]Dica: use [bold]rumo diagnosticar[/bold] para entender o erro.[/dim]")
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
