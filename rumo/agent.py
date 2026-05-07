import os
import platform
import re
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rumo import llm, config, discovery
from rumo import memory as mem
from rumo.tools import TOOLS_SCHEMA, executar_tool
from rumo.plugins import contexto_plugins_para_llm

console = Console()

SYSTEM_PROMPT = """Você é um agente de terminal autônomo e eficiente.
Sistema: {os} | Shell: {shell} | Diretório: {cwd}
Backend LLM: {ollama_url} (modelo: {ollama_model})

{ctx_discovery}

{ctx_plugins}

{ctx_memoria}

{ctx_sessao}

## Regras
1. Pense passo a passo antes de agir.
2. Use as tools disponíveis para executar comandos reais no sistema.
3. Prefira `execute_shell` para operações no sistema de arquivos e processos.
4. Use `list_binaries` para descobrir ferramentas disponíveis quando necessário.
5. Use `ask_user` quando precisar de informação que não pode descobrir sozinho.
6. Ao finalizar a tarefa, responda em JSON: {{"tool": null, "response": "<resultado>"}}
7. Se um comando falhar, tente corrigir ou use `diagnose_error`.
8. Não execute comandos destrutivos sem necessidade explícita.
9. Comandos que listam diretórios usam `execute_shell` com ls/find, não `list_binaries`.
10. Seja conciso na resposta final."""


def _format_result(resultado: str, verbose: bool = False) -> str:
    linhas = resultado.splitlines()
    if verbose or len(linhas) <= 15:
        return resultado
    visivel = "\n".join(linhas[:15])
    ocultas = len(linhas) - 15
    return f"{visivel}\n[dim]... ({ocultas} linhas ocultas)[/dim]"


def agente(tarefa: str, auto: bool = False, verbose: bool = False, modelo: str = "", perigo: bool = False, debug: bool = False) -> None:
    cfg = config.carregar()
    config.garantir_config_padrao()

    max_iter = cfg["max_iterations"]
    modelo_final = modelo or os.getenv("RUMO_AGENTE_MODEL", "") or cfg["modelo_agente"]

    # contexto rico montado uma vez
    ctx_discovery = discovery.contexto_para_llm()
    ctx_plugins = contexto_plugins_para_llm(tarefa)
    ctx_memoria = mem.contexto_para_llm()
    ctx_sessao = mem.contexto_sessao_para_llm()

    # iniciar sessão
    mem.iniciar_sessao(
        cwd=os.getcwd(),
        shell=os.getenv("SHELL", "bash").split("/")[-1],
        os_info=platform.system(),
    )

    system = SYSTEM_PROMPT.format(
        os=platform.system(),
        shell=os.getenv("SHELL", "bash").split("/")[-1],
        cwd=os.getcwd(),
        ollama_url=llm.OLLAMA_URL,
        ollama_model=modelo_final,
        ctx_discovery=ctx_discovery,
        ctx_plugins=ctx_plugins,
        ctx_memoria=ctx_memoria,
        ctx_sessao=ctx_sessao,
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": tarefa},
    ]

    if perigo:
        console.print("[bold red]⚠️  MODO PERIGO ativado — nenhuma confirmação será solicitada.[/bold red]\n")

    console.print(f"[bold cyan]Agente iniciado:[/bold cyan] {tarefa}\n")

    for i in range(max_iter):
        if verbose:
            console.print(f"[dim]Iteração {i + 1}/{max_iter}[/dim]")

        resposta = llm.complete_with_tools(messages, TOOLS_SCHEMA, model=modelo_final, debug=debug)

        if resposta["type"] == "text":
            conteudo = resposta["content"]

            # tenta extrair comando de blocos de código
            cmd_match = re.search(r"```(?:bash|sh)?\s*\n(.+?)\n```", conteudo, re.DOTALL)
            if not cmd_match:
                cmd_match = re.search(r"`([^`\n]+)`", conteudo)

            if cmd_match:
                cmd = cmd_match.group(1).strip()
                primeiro_token = cmd.split()[0] if cmd.split() else ""
                keywords = {"ls", "cd", "cat", "echo", "grep", "find", "ps", "top", "df",
                            "du", "mkdir", "rm", "cp", "mv", "chmod", "chown", "curl",
                            "wget", "git", "docker", "kubectl", "python", "python3", "node",
                            "npm", "pip", "brew", "apt", "yum", "systemctl", "sudo"}
                if primeiro_token in keywords:
                    if verbose:
                        console.print(f"[dim]Extraindo comando do texto: {cmd}[/dim]")
                    resultado = executar_tool("execute_shell", {"command": cmd}, auto=auto or perigo)
                    mem.registrar_comando(cmd, resultado, "código de retorno: 0" in resultado)
                    messages.append({"role": "user", "content": f"Resultado do comando `{cmd}`:\n{resultado}"})
                    if verbose:
                        console.print(f"[dim]Resultado:[/dim]\n{_format_result(resultado, verbose)}\n")
                    continue

            # resposta final — extrai "response" se o modelo retornou JSON (Ollama)
            if conteudo.strip().startswith("{"):
                try:
                    import json as _json
                    dados = _json.loads(conteudo)
                    if "response" in dados and dados.get("tool") is None:
                        conteudo = dados["response"]
                except Exception:
                    pass
            console.print(Panel(Markdown(conteudo), title="[bold green]Agente[/bold green]", border_style="green"))
            return

        # tool call
        nome = resposta["name"]
        args = resposta["arguments"]

        if verbose:
            console.print(f"[bold cyan]Tool:[/bold cyan] {nome}({args})")

        # APIs OpenAI-compatible exigem a mensagem do assistant com tool_calls no histórico
        if "assistant_message" in resposta:
            messages.append(resposta["assistant_message"])

        resultado = executar_tool(nome, args, auto=auto or perigo)

        if nome == "execute_shell":
            cmd = args.get("command", "")
            sucesso = "código de retorno: 0" in resultado
            mem.registrar_comando(cmd, resultado, sucesso)
            if not sucesso:
                mem.registrar_erro(resultado[:200])

        if verbose:
            console.print(f"[dim]{_format_result(resultado, verbose)}[/dim]\n")

        if "tool_call_id" in resposta:
            messages.append({"role": "tool", "tool_call_id": resposta["tool_call_id"], "content": resultado})
        else:
            messages.append({"role": "tool", "name": nome, "content": resultado})

    console.print(
        f"\n[bold yellow]⚠️  Limite de {max_iter} iterações atingido.[/bold yellow]\n"
        "Use [bold]--verbose[/bold] para inspecionar o progresso ou aumente [bold]max_iterations[/bold] em ~/.rumo/config.md"
    )
