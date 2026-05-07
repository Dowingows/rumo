# Rumo

CLI inteligente para terminal: sugira, execute e diagnostique comandos em linguagem natural.

---

## Instalação

```bash
git clone <repositório>
cd rumo
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Configuração inicial

Na primeira vez que você usar qualquer comando, o Rumo detecta que não há configuração e abre o setup automaticamente.

Para configurar manualmente a qualquer momento:

```bash
rumo config setup
```

O wizard vai:
1. Listar os modelos Ollama disponíveis na sua máquina
2. Pedir o modelo para o **agente** (loop ReAct com tool calling)
3. Pedir o modelo para **executar / sugerir** (geração de comandos)
4. Pedir o modelo para **diagnosticar** (análise de erros)

Para ver a configuração atual:

```bash
rumo config
```

A configuração fica salva em `~/.rumo/config.md` e pode ser editada manualmente.

---

## Backend LLM

O Rumo detecta automaticamente qual backend usar pela presença das variáveis de ambiente. A prioridade é:

**OpenCode Go → Groq → Ollama**

### OpenCode Go (prioridade 1 — API paga, modelos de código otimizados)

Serviço pago em https://opencode.ai/go ($5/mês). Oferece modelos como DeepSeek V4, Kimi K2, Qwen 3.5 Coder via API OpenAI-compatible.

**Passo a passo:**

1. Assine em https://opencode.ai/go
2. Copie `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
3. Adicione sua chave no `.env`:
   ```env
   RUMO_OPENCODE_KEY=sua_chave_aqui
   RUMO_OPENCODE_MODEL=opencode-go/kimi-k2.6
   ```
4. Execute o setup de modelos:
   ```bash
   rumo config setup
   ```

Modelos disponíveis:

| Modelo | Características |
|--------|----------------|
| `opencode-go/kimi-k2.6` | Bom equilíbrio velocidade/qualidade (padrão) |
| `opencode-go/deepseek-v4-pro` | Mais capaz, recomendado para o agente |
| `opencode-go/qwen3.5-coder-32b` | Especializado em código |

> No `rumo config setup`, os modelos Ollama locais são listados automaticamente, mas ao usar OpenCode Go basta digitar o ID do modelo desejado.

### Groq (prioridade 2 — API gratuita, sem instalação)

1. Crie sua chave gratuita em https://console.groq.com
2. Adicione ao `.env`:
   ```env
   RUMO_GROQ_KEY=sua_chave_aqui
   RUMO_GROQ_MODEL=llama3-8b-8192
   ```

### Ollama (padrão — local, sem custo)

Requer o Ollama rodando localmente:

```bash
# Instalar o Ollama: https://ollama.com
ollama pull qwen3:4b        # modelo leve (~2.5GB), bom para sugerir/diagnosticar
ollama pull qwen3:8b        # mais capaz (~5GB), recomendado para o agente
```

Configure no `.env` (opcional — os defaults já funcionam):

```env
RUMO_OLLAMA_URL=http://localhost:11434
RUMO_MODEL=qwen3:4b
RUMO_TEMPERATURE=0.1
```

---

## Comandos

### `rumo sugerir`

Sugere um comando para o que você quer fazer, sem executar.

```bash
rumo sugerir "liste arquivos por data de modificação"
rumo sugerir "compactar pasta sem arquivos .git"
```

### `rumo executar`

Gera e executa o comando diretamente, pedindo confirmação antes.

```bash
rumo executar "mostre os 10 processos que mais consomem memória"
rumo executar "apague arquivos .log mais antigos que 30 dias" --sim   # sem confirmação
rumo executar "formate o HD" --perigo                                  # inclui comandos críticos
```

### `rumo diagnosticar`

Analisa um erro e explica como corrigir.

```bash
rumo diagnosticar "permission denied: /etc/hosts"
cat error.log | rumo diagnosticar
comando_que_falhou 2>&1 | rumo diagnosticar
```

### `rumo agente`

Executa uma tarefa de forma autônoma com loop ReAct e tool calling — o agente pensa, executa comandos, observa resultados e itera até concluir.

```bash
rumo agente "organize os arquivos da pasta Downloads por tipo"
rumo agente "encontre qual processo está usando a porta 8080 e mate-o" --auto
rumo agente "crie um script de backup para ~/Documents" --verbose
rumo agente "configure o nginx" --modelo qwen3:8b   # sobrescreve o modelo
```

Opções:
- `--auto` / `-a` — pula confirmações de comandos não-críticos
- `--verbose` / `-v` — mostra todas as tool calls e resultados
- `--modelo` / `-m` — sobrescreve o modelo configurado para essa execução
- `--perigo` — executa sem nenhuma confirmação
- `--debug` / `-d` — mostra o JSON cru enviado/recebido pelo LLM

### `rumo memoria`

Lista os comandos aprendidos (salvos automaticamente quando um comando falha e você fornece a correção).

```bash
rumo memoria
rumo memoria --remover "descrição do comando"
```

### `rumo config`

```bash
rumo config           # mostra a configuração atual
rumo config setup     # wizard interativo para configurar modelos
```

### `rumo learn`

Aprende uma ferramenta via `--help` e salva como plugin para uso no agente.

```bash
rumo learn docker
rumo learn ffmpeg
```

### `rumo plugin`

```bash
rumo plugin add <nome>           # cria um plugin em branco
rumo plugin add <nome> --learn   # aprende automaticamente via --help
rumo plugin list                 # lista plugins instalados
rumo plugin remove <nome>        # remove um plugin
```

---

## Configuração de referência

Arquivo: `~/.rumo/config.md`

| Chave                | Descrição                                      | Padrão     |
|----------------------|------------------------------------------------|------------|
| `modelo_agente`      | Modelo usado pelo `rumo agente`                | `qwen3:4b` |
| `modelo_executar`    | Modelo usado por `rumo executar` e `sugerir`   | `qwen3:4b` |
| `modelo_diagnosticar`| Modelo usado por `rumo diagnosticar`           | `qwen3:4b` |
| `max_iterations`     | Máximo de iterações do loop do agente          | `10`       |
| `confirmar_criticas` | Pede confirmação antes de comandos críticos    | `true`     |
| `verbose`            | Modo verbose por padrão                        | `false`    |

---

## Adicionando um novo subcomando

1. Crie `rumo/novo_modulo.py` com a lógica e um system prompt
2. Adicione o `@app.command("nome")` em `cli.py` importando do novo módulo
