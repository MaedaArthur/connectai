# Agente ConnectAI — Gerador de Histórias

Gerador de narrativas ficcionais imersivas para simulações corporativas de hackathons.
Usa a metodologia **mirror-problem-first**: o problema é vivido e documentado antes de qualquer movimento em direção à solução.

---

## Estrutura do projeto

```
Agente ConnectAI/
├── main.py             # Ponto de entrada
├── entrada.json        # JSON de entrada editável (use como template)
├── .env                # Variáveis de ambiente (não versionar)
├── .env.example        # Modelo do .env
├── outputs/            # Histórias salvas (uma pasta por empresa)
└── src/
    ├── estado.py       # TypedDicts do grafo (EntradaHistoria, EstadoGrafo)
    ├── modelo.py       # Configuração do LLM (Groq)
    ├── nos.py          # Nós do grafo: gerar, atualizar e salvar história
    ├── grafo.py        # Construção e compilação do grafo LangGraph
    └── entrada.py      # Coleta de entrada: arquivo JSON ou prompts interativos
```

---

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install langgraph langchain-core langchain-groq python-dotenv
```

Crie o arquivo `.env` com base em `.env.example`:

```bash
cp .env.example .env
```

---

## Configuração

Edite o `.env`:

```env
GROQ_API_KEY=sua_chave_aqui
```

---

## Como usar

### 1. Via arquivo JSON (recomendado)

Edite o [entrada.json](entrada.json) com os dados do cenário e execute:

```bash
python main.py --arquivo entrada.json
# ou
python main.py -a entrada.json
```

### 2. Via prompts interativos

```bash
python main.py
```

O terminal vai pedir cada campo um por um.

---

## Campos do JSON de entrada

| Campo | Tipo | Valores aceitos |
|---|---|---|
| `empresa` | string | Nome ou tipo da empresa |
| `setor` | string | Setor de atuação |
| `cargo` | string | Cargo do protagonista |
| `dificuldade` | string | `"baixa"`, `"média"` ou `"alta"` |
| `sintomas` | lista de strings | Manifestações visíveis do problema |
| `causas_raiz.principal` | string | Causa sistêmica central (nunca aparece diretamente na história) |
| `causas_raiz.secundarias` | lista de strings | Causas intermediárias |

### Efeito do campo `dificuldade`

| Nível | Documentos gerados | Evidências da causa principal |
|---|---|---|
| `baixa` | 3 a 5 | 1 |
| `média` | 6 a 8 | 2 |
| `alta` | 9 a 12 | 3 a 4 |

---

## Loop de feedback

Após a geração, o terminal oferece três comandos:

```
[f] feedback  |  [s] salvar  |  [q] sair
```

- **f** — envia um feedback textual; o agente revisa a história mantendo a metodologia
- **s** — salva o arquivo `.md` em `historias/<Empresa>/` e encerra
- **q** — sai sem salvar

---

## Saída gerada

A história é salva em Markdown com nome automático:

```
outputs/<Empresa>/<Empresa>_<dificuldade>_001.md
```

O arquivo contém três seções:
1. **A história** — narrativa em terceira pessoa (mín. 2.500 palavras)
2. **Índice de documentos** — tabela com todos os artefatos citados
3. **Mapa de investigação** — uso interno do mentor (sinais + gabarito RPU)
# connectai
