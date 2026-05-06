import re
import subprocess

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_binaries",
            "description": "Lista ferramentas instaladas no sistema, opcionalmente filtradas por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": "Categoria opcional: containers, linguagens, gerenciadores, git, editores, rede, busca, dados, monitoramento, ollama",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell",
            "description": "Executa um comando shell e retorna stdout, stderr e código de retorno.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Comando shell a executar",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_command",
            "description": "Gera um comando shell a partir de uma descrição em linguagem natural.",
            "parameters": {
                "type": "object",
                "properties": {
                    "descricao": {
                        "type": "string",
                        "description": "O que você quer fazer em linguagem natural",
                    }
                },
                "required": ["descricao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_error",
            "description": "Analisa uma mensagem de erro e sugere como corrigir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "erro": {
                        "type": "string",
                        "description": "Mensagem de erro a analisar",
                    }
                },
                "required": ["erro"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Faz uma pergunta ao usuário e retorna a resposta. Use quando precisar de informação adicional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {
                        "type": "string",
                        "description": "Pergunta a fazer ao usuário",
                    }
                },
                "required": ["pergunta"],
            },
        },
    },
]

CRITICAL_PATTERNS = [
    r"\brm\s+-[rf]",
    r"\bdd\s+",
    r"\bmkfs\b",
    r"\bfdisk\b",
    r"\bformat\b",
    r">\s*/",
    r"git\s+push\s+--force",
    r"\bsudo\s+rm\b",
    r"\bchmod\s+777\b",
    r"\bshred\b",
    r"\bwipe\b",
]


def _e_critico(comando: str) -> bool:
    return any(re.search(p, comando) for p in CRITICAL_PATTERNS)


def _list_binaries(categoria: str = "") -> str:
    from rumo import discovery
    ferramentas = discovery.descobrir_ferramentas()
    if categoria:
        encontradas = ferramentas.get(categoria, [])
        if not encontradas:
            return f"Nenhuma ferramenta instalada na categoria '{categoria}'."
        return f"Ferramentas em '{categoria}': {', '.join(encontradas)}"
    return discovery.contexto_para_llm() or "Nenhuma ferramenta categorizada encontrada."


def _execute_shell(command: str) -> str:
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        saida = r.stdout.strip()
        erro = r.stderr.strip()
        rc = r.returncode
        partes = []
        if saida:
            partes.append(f"stdout:\n{saida}")
        if erro:
            partes.append(f"stderr:\n{erro}")
        partes.append(f"código de retorno: {rc}")
        return "\n".join(partes)
    except subprocess.TimeoutExpired:
        return "Erro: timeout (30s)"
    except Exception as e:
        return f"Erro ao executar: {e}"


def _suggest_command(descricao: str) -> str:
    from rumo.suggest import sugerir
    comando, explicacao = sugerir(descricao)
    if comando.startswith("PERGUNTA:"):
        return f"Preciso de mais detalhes: {comando[len('PERGUNTA:'):].strip()}"
    return f"{comando}\n{explicacao}".strip()


def _diagnose_error(erro: str) -> str:
    from rumo import llm
    from rumo.diagnose import SYSTEM as SYSTEM_DIAGNOSE
    return llm.complete(erro, system=SYSTEM_DIAGNOSE)


def _ask_user(pergunta: str) -> str:
    print(f"\n🤖 {pergunta}")
    return input("→ ").strip()


def executar_tool(nome: str, args: dict, auto: bool = False) -> str:
    from rich.console import Console
    from rich.prompt import Confirm
    console = Console()

    if nome == "execute_shell":
        comando = args.get("command", "")
        if _e_critico(comando) and not auto:
            console.print(f"\n[bold red]⚠️  Comando crítico detectado:[/bold red] [yellow]{comando}[/yellow]")
            if not Confirm.ask("[bold]Executar mesmo assim?[/bold]", default=False):
                return "Execução cancelada pelo usuário."
        return _execute_shell(comando)

    if nome == "list_binaries":
        return _list_binaries(args.get("categoria", ""))
    if nome == "suggest_command":
        return _suggest_command(args.get("descricao", ""))
    if nome == "diagnose_error":
        return _diagnose_error(args.get("erro", ""))
    if nome == "ask_user":
        return _ask_user(args.get("pergunta", ""))

    return f"Tool desconhecida: {nome}"
