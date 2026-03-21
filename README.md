# ConnectAI — Gerador de Casos para Hackathons

Gerador de narrativas ficcionais imersivas e documentos corporativos para simulações de hackathons.
Usa a metodologia **mirror-problem-first**: o problema é vivido e documentado antes de qualquer movimento em direção à solução.

---

## Estrutura do projeto

```
connectai/
├── main.py                      # Etapa 1 — gera a narrativa (.md)
├── main_documentos.py           # Etapa 2 — gera o conteúdo dos documentos (.json)
├── gerar_documentos.py          # Etapa 3 — gera os arquivos reais (.xlsx, .docx, .pdf, .pptx, .eml)
├── entrada.example.json         # Template do JSON de entrada
├── .env.example                 # Modelo de variáveis de ambiente
├── requirements.txt
├── outputs/                     # Saídas geradas
│   └── <Empresa>/
│       └── <Empresa>_<dificuldade>_001/
│           ├── <Empresa>_<dificuldade>_001.md   # narrativa gerada (Etapa 1)
│           └── documentos/
│               ├── documentos.json              # dados dos documentos (Etapa 2)
│               └── documentos_gerados/          # arquivos reais (Etapa 3)
│                   ├── Roadmap_Release_Q3.xlsx
│                   ├── Memo_Interno.docx
│                   ├── Relatorio_Auditoria.pdf
│                   ├── Apresentacao_Status.pptx
│                   └── Email_Aprovacao_CFO.eml
└── src/
    ├── modelo.py                # Configuração compartilhada do LLM (Groq)
    ├── agente_narrativa/        # Etapa 1 — agente gerador de histórias
    │   ├── estado.py            # TypedDict EstadoGrafo
    │   ├── nos.py               # Nós: gerar_historia, atualizar_historia, salvar_historia
    │   ├── grafo.py             # Grafo LangGraph do agente de narrativa
    │   └── entrada.py           # Coleta de entrada: arquivo JSON ou interativo
    └── agente_documentos/       # Etapa 2 — agente gerador de documentos
        ├── estado.py            # TypedDicts: DocumentoTabela, EstadoAgente2
        ├── nos.py               # Nós: extrair_secao2, classificar_documento, gerar_documento, salvar_saida
        └── grafo.py             # Grafo LangGraph do agente de documentos
```

---

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crie os arquivos locais a partir dos templates:

```bash
cp .env.example .env
cp entrada.example.json entrada.json
```

---

## Configuração

Edite o `.env`:

```env
GROQ_API_KEY=sua_chave_aqui
```

---

## Etapa 1 — Gerador de Narrativa (`main.py`)

Gera uma narrativa ficcional corporativa a partir de um JSON de entrada.

### Como usar

```bash
# Via arquivo JSON (recomendado)
python main.py --arquivo entrada.json

# Via prompts interativos
python main.py
```

### Campos do JSON de entrada

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

| Nível | Documentos na história | Evidências da causa principal |
|---|---|---|
| `baixa` | 3 a 5 | 1 |
| `média` | 6 a 8 | 2 |
| `alta` | 9 a 12 | 3 a 4 |

### Loop de feedback

Após a geração, o terminal oferece três comandos:

```
[f] feedback  |  [s] salvar  |  [q] sair
```

- **f** — envia feedback; o agente revisa mantendo a metodologia
- **s** — salva o `.md` em `outputs/<Empresa>/<Empresa>_<dificuldade>_001/` e encerra
- **q** — sai sem salvar

### Saída gerada

O `.md` contém três seções:

1. **Seção 1 — A história** — narrativa em terceira pessoa (mín. 2.500 palavras)
2. **Seção 2 — Índice de documentos** — tabela com todos os artefatos citados (nome, tipo, papel, estrutura, inconsistência plantada)
3. **Seção 3 — Mapa de investigação** — uso interno do mentor (sinais por camada + gabarito RPU)

---

## Etapa 2 — Gerador de Conteúdo dos Documentos (`main_documentos.py`)

Lê o `.md` da Etapa 1, extrai o índice de documentos (Seção 2) e gera o conteúdo fictício de cada artefato como JSON estruturado.

### Como usar

```bash
python main_documentos.py outputs/<Empresa>/<Empresa>_<dificuldade>_001/<Empresa>_<dificuldade>_001.md
```

### Fluxo interno (grafo LangGraph)

```
extrair_secao2 → [loop por documento] → classificar_documento → gerar_documento → salvar_saida
```

1. **extrair_secao2** — parseia a tabela da Seção 2 do `.md`
2. **classificar_documento** — determina o tipo exato (`.xlsx`, `.docx`, `.pdf`, `.pptx`, `.eml`) e a categoria da taxonomia
3. **gerar_documento** — gera o JSON do documento com conteúdo ancorado na narrativa, dados críticos e inconsistências plantadas
4. **salvar_saida** — salva `documentos/documentos.json`

### Tipos de documento suportados

| Tipo | Schema JSON gerado |
|---|---|
| `xlsx` | `abas[]{nome, colunas, linhas}` ou `colunas + entradas[]` (log) |
| `docx` | `secoes[]{titulo, conteudo}`, `campos_criticos{}` |
| `pdf` | `paginas[]{secoes[]}`, `assinatura`, `data_emissao` |
| `pptx` | `slides[]{numero, titulo, conteudo, dados{}}` |
| `eml` | `cabecalho{de, para, assunto, data}`, `corpo`, `anexos[]` |

### Saída gerada

```
documentos/documentos.json
```

---

## Etapa 3 — Gerador de Arquivos Reais (`gerar_documentos.py`)

Lê o `documentos.json` da Etapa 2 e gera os arquivos reais na ordem em que aparecem no JSON.

### Como usar

```bash
python gerar_documentos.py outputs/<Empresa>/<Empresa>_<dificuldade>_001/documentos/documentos.json
```

### Bibliotecas utilizadas por tipo

| Tipo | Biblioteca |
|---|---|
| `.xlsx` | `pandas` + `openpyxl` |
| `.docx` | `python-docx` |
| `.pdf` | `fpdf2` |
| `.pptx` | `python-pptx` |
| `.eml` | texto formatado (sem dependências extras) |

### Saída gerada

```
documentos/documentos_gerados/
    <arquivo>.xlsx
    <arquivo>.docx
    <arquivo>.pdf
    <arquivo>.pptx
    <arquivo>.eml
```
