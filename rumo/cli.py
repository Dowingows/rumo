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
plugin_app = typer.Typer(name="plugin", help="Gerencia plugins do rumo.")
app.add_typer(plugin_app, name="plugin")

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
    auto: bool = typer.Option(False, "--auto", "-a", help="Alias de --sim"),
    perigo: bool = typer.Option(False, "--perigo", help="Executa sem confirmação, incluindo comandos críticos"),
):
    """Gera e executa um comando a partir de linguagem natural."""
    from rumo.runner import executar

    try:
        executar(descricao, sim=sim, auto=auto, perigo=perigo)
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


@app.command("agente")
def cmd_agente(
    tarefa: str = typer.Argument(..., help="Tarefa em linguagem natural"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Pula confirmações de comandos críticos"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostra todas as tool calls e resultados"),
    modelo: str = typer.Option("", "--modelo", "-m", help="Sobrescreve o modelo configurado"),
    perigo: bool = typer.Option(False, "--perigo", help="Executa sem nenhuma confirmação (incluindo críticos)"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Mostra JSON cru do LLM e mensagens enviadas"),
):
    """Executa uma tarefa de forma autônoma com loop ReAct e tool calling."""
    from rumo.agent import agente

    try:
        agente(tarefa, auto=auto, verbose=verbose, modelo=modelo, perigo=perigo, debug=debug)
    except Exception as e:
        console.print(f"[bold red]Erro:[/bold red] {e}")
        raise typer.Exit(1)


@app.command("memoria")
def cmd_memoria(
    limpar: Optional[str] = typer.Option(None, "--remover", "-r", help="Remove uma entrada pela descrição"),
):
    """Lista os comandos aprendidos e salvos na memória."""
    from rumo.memory import listar, remover

    if limpar:
        if remover(limpar):
            console.print(f"[bold green]Removido:[/bold green] {limpar}")
        else:
            console.print(f"[bold red]Não encontrado:[/bold red] {limpar}")
        return

    entradas = listar()
    if not entradas:
        console.print("[dim]Nenhum comando na memória ainda.[/dim]")
        console.print("Quando um comando falhar, o rumo vai te perguntar o correto e salvar aqui.")
        return

    console.print(f"\n[bold]Memória do rumo[/bold] — {len(entradas)} entrada(s)\n")
    for e in entradas:
        data = e.get("salvo_em", "")
        console.print(f"[bold cyan]{e['descricao']}[/bold cyan]")
        console.print(f"  [yellow]{e['comando']}[/yellow]")
        if data:
            console.print(f"  [dim]{data}[/dim]")
        console.print()


@app.command("learn")
def cmd_learn(
    ferramenta: str = typer.Argument(..., help="Ferramenta para aprender (ex: docker, ffmpeg, git)"),
):
    """Aprende uma ferramenta via --help e salva como plugin em ~/.rumo/plugins/."""
    from rumo.learn import aprender

    console.print(f"\n[bold cyan]Aprendendo '{ferramenta}'...[/bold cyan]")
    try:
        path = aprender(ferramenta)
        console.print(f"[bold green]✓ Plugin criado:[/bold green] {path}")
        console.print(f"[dim]Use [bold]rumo agente[/bold] com tarefas de {ferramenta} para aproveitá-lo.[/dim]")
    except FileNotFoundError as e:
        console.print(f"[bold red]{e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro ao aprender '{ferramenta}':[/bold red] {e}")
        raise typer.Exit(1)


# --- Subcomandos plugin ---

@plugin_app.command("add")
def cmd_plugin_add(
    nome: str = typer.Argument(..., help="Nome do plugin (ex: docker, git, k8s)"),
    learn: bool = typer.Option(False, "--learn", "-l", help="Auto-gera via --help da ferramenta"),
):
    """Adiciona um plugin. Com --learn, aprende da ferramenta automaticamente."""
    if learn:
        from rumo.learn import aprender
        console.print(f"\n[bold cyan]Aprendendo '{nome}' via --help...[/bold cyan]")
        try:
            path = aprender(nome)
            console.print(f"[bold green]✓ Plugin criado:[/bold green] {path}")
        except FileNotFoundError as e:
            console.print(f"[bold red]{e}[/bold red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Erro:[/bold red] {e}")
            raise typer.Exit(1)
    else:
        from rumo.plugins.manager import adicionar_plugin
        path = adicionar_plugin(nome)
        console.print(f"[bold green]✓ Plugin criado:[/bold green] {path}")
        console.print(f"[dim]Edite o arquivo para adicionar comandos e exemplos.[/dim]")


@plugin_app.command("list")
def cmd_plugin_list():
    """Lista todos os plugins instalados."""
    from rumo.plugins.manager import listar_detalhado

    plugins = listar_detalhado()
    if not plugins:
        console.print("[dim]Nenhum plugin instalado.[/dim]")
        console.print("Instale com: [bold]rumo plugin add <nome>[/bold] ou [bold]rumo learn <ferramenta>[/bold]")
        return

    console.print(f"\n[bold]Plugins instalados[/bold] — {len(plugins)} plugin(s)\n")
    for p in plugins:
        console.print(f"[bold cyan]{p['nome']}[/bold cyan]  [dim]{p['tamanho_kb']}KB[/dim]")
        if p["descricao"]:
            console.print(f"  [dim]{p['descricao']}[/dim]")
        console.print()


@plugin_app.command("remove")
def cmd_plugin_remove(
    nome: str = typer.Argument(..., help="Nome do plugin a remover"),
):
    """Remove um plugin instalado."""
    from rumo.plugins.manager import remover_plugin

    if remover_plugin(nome):
        console.print(f"[bold green]✓ Plugin '{nome}' removido.[/bold green]")
    else:
        console.print(f"[bold red]Plugin '{nome}' não encontrado.[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
