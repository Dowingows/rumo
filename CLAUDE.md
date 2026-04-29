# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup e instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copie `.env.example` para `.env` e configure o backend LLM desejado.

## Comandos disponíveis

```bash
rumo sugerir "liste arquivos por data"
rumo executar "mostre os 10 processos que mais consomem memória"
rumo diagnosticar "permission denied: /etc/hosts"
cat error.log | rumo diagnosticar   # via pipe
rumo executar "apague logs antigos" --sim   # sem confirmação
```

## Arquitetura

O projeto tem três camadas:

**`rumo/llm.py`** — abstração do cliente LLM. Detecta automaticamente o backend: se `GROQ_API_KEY` estiver definida usa Groq API, caso contrário usa Ollama local. Todas as outras camadas chamam apenas `llm.complete(prompt, system)`.

**`rumo/suggest.py`, `runner.py`, `diagnose.py`** — lógica de cada ferramenta. Cada módulo tem um system prompt específico e uma função principal que recebe linguagem natural e retorna o resultado processado.

**`rumo/cli.py`** — entry point Typer. Mapeia os subcomandos `sugerir`, `executar`, `diagnosticar` para as funções dos módulos acima. Toda formatação visual (Rich panels, cores) fica aqui.

## Backends LLM

- **Ollama** (padrão): requer `ollama` rodando localmente. Modelo padrão: `qwen2.5:0.5b` (leve, ~500MB). Instalar modelo: `ollama pull qwen2.5:0.5b`
- **Groq** (alternativa): API gratuita, sem instalação. Basta definir `GROQ_API_KEY` no `.env`.

## Adicionando um novo subcomando

1. Crie `rumo/novo_modulo.py` com a lógica e um system prompt
2. Adicione o `@app.command("nome")` em `cli.py` importando do novo módulo
