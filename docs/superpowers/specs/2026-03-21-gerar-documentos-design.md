# Spec: gerar_documentos — Gerador de Todos os Tipos de Documentos

**Data:** 2026-03-21
**Status:** Aprovado

---

## Contexto

O script `gerar_planilhas.py` atualmente gera apenas arquivos `.xlsx` a partir do JSON produzido pelo agente de documentos (`documentos.json`). O pipeline já suporta cinco tipos de documento no JSON (`xlsx`, `docx`, `pdf`, `pptx`, `eml`) e logs estruturados. O objetivo é generalizar o script para gerar arquivos reais de todos os tipos.

---

## Decisões

| Decisão | Escolha | Motivo |
|---|---|---|
| Nome do arquivo | `gerar_documentos.py` | Reflete escopo ampliado; `gerar_planilhas.py` é removido |
| Padrão de extensão | Dict de handlers | Simples, sem over-engineering, fácil de ampliar |
| PDF | fpdf2 | Leve, sem deps de sistema, suficiente para docs corporativos simples |
| DOCX | python-docx | Biblioteca padrão para .docx em Python |
| PPTX | python-pptx | Biblioteca padrão para .pptx em Python |
| EML | .txt formatado | Solicitação do usuário; sem deps extras |

---

## Dependências novas

```
python-docx
python-pptx
fpdf2
```

Adicionar ao `requirements.txt`.

---

## Estrutura do arquivo `gerar_documentos.py`

### Handlers por tipo

```python
HANDLERS = {
    "xlsx": criar_xlsx,
    "docx": criar_docx,
    "pdf":  criar_pdf,
    "pptx": criar_pptx,
    "eml":  criar_eml,
}
```

### Assinaturas

```python
def criar_xlsx(caminho: str, doc: dict) -> None
def criar_docx(caminho: str, doc: dict) -> None
def criar_pdf(caminho: str, doc: dict) -> None
def criar_pptx(caminho: str, doc: dict) -> None
def criar_eml(caminho: str, doc: dict) -> None
def processar_documentos(caminho_json: str) -> None
```

---

## Schemas JSON de entrada (referência)

Os schemas completos são definidos em `src/agente_documentos/nos.py` (prompts do LLM). Resumo das chaves relevantes para cada handler:

| Tipo | Chaves principais |
|---|---|
| xlsx (padrão) | `arquivo`, `tipo`, `abas[]{nome, colunas[], linhas[][]}` |
| xlsx (log) | `arquivo`, `tipo`, `colunas[]`, `entradas[]{col: val}` |
| docx | `arquivo`, `tipo`, `secoes[]{titulo, conteudo}`, `campos_criticos{chave: valor}` |
| pdf (padrão) | `arquivo`, `tipo`, `paginas[]{numero, secoes[]{titulo, conteudo}}`, `assinatura`, `data_emissao` |
| pdf (log) | `arquivo`, `tipo`, `colunas[]`, `entradas[]{col: val}` |
| pptx | `arquivo`, `tipo`, `slides[]{numero, titulo, conteudo, dados{}}` |
| eml | `arquivo`, `tipo`, `cabecalho{de, para, assunto, data}`, `corpo`, `anexos[]` |

O nome do arquivo de saída é sempre `doc["arquivo"]`.

---

## Comportamento por tipo

### xlsx
- Usa `pandas` + `openpyxl` (lógica atual preservada)
- Os dois modos são **mutuamente exclusivos**: se o campo `entradas` estiver presente no documento, opera em modo log; caso contrário, opera em modo padrão
- **Modo log:** gera uma única aba tabular usando `doc["colunas"]` como cabeçalho e cada item de `doc["entradas"]` como linha
- **Modo padrão:** itera `doc["abas"]`, cada aba vira uma sheet com `colunas` e `linhas`

### docx
- Usa `python-docx`
- Itera `secoes`: cada seção → heading nível 1 com `titulo` + parágrafo com `conteudo`
- `campos_criticos` adicionados como tabela de duas colunas no final do documento (se presentes)

### pdf
- Usa `fpdf2`, encoding UTF-8
- Os dois modos são **mutuamente exclusivos**: se o campo `entradas` estiver presente, opera em modo log; caso contrário, modo padrão
- **Modo padrão:** itera `doc["paginas"]`: cada página → `add_page()`, seções com título em negrito e corpo em texto normal; `assinatura` e `data_emissao` são campos opcionais do topo de `doc` — se presentes, inseridos no rodapé da última página; se ausentes, rodapé omitido
- **Modo log:** gera uma única página com tabela; colunas definidas por `doc["colunas"]`; cada item de `doc["entradas"]` é uma linha

### pptx
- Usa `python-pptx`
- Itera `slides`: cada slide → layout "Title and Content", `titulo` no placeholder de título, `conteudo` no corpo
- `dados` do slide são descartados silenciosamente (presentes no JSON apenas para referência de inconsistências, sem representação visual)

### eml
- Gera arquivo `.txt` com extensão `.eml`, encoding UTF-8
- Campos mapeados de `doc["cabecalho"]["de/para/assunto/data"]`, `doc["corpo"]`, `doc["anexos"]`
- Se `doc["anexos"]` for lista vazia ou ausente, a linha "Anexos:" é omitida
- Formato:
  ```
  De: <cabecalho.de>
  Para: <cabecalho.para>
  Assunto: <cabecalho.assunto>
  Data: <cabecalho.data>

  <corpo>

  Anexos: <anexo1>, <anexo2>   ← omitido se lista vazia/ausente
  ```

---

## processar_documentos

```python
def processar_documentos(caminho_json: str) -> None:
    dados = json.load(...)           # falha com exceção se JSON malformado
    diretorio_saida = <pasta documentos_gerados>
    for doc in dados["documentos"]:
        handler = HANDLERS.get(doc["tipo"])
        if not handler:
            print(f"[AVISO] Tipo não suportado: {doc['tipo']} — pulando '{doc['arquivo']}'")
            continue
        caminho = os.path.join(diretorio_saida, doc["arquivo"])
        try:
            handler(caminho, doc)
            print(f"Criado: {caminho}")
        except Exception as e:
            print(f"[ERRO] Falha ao gerar '{doc['arquivo']}': {e}")
```

---

## Invocação

```bash
python gerar_documentos.py outputs/TechCorp/TechCorp_baixa_001/documentos/documentos.json
```

Saída dos arquivos em `<pasta_do_json>/documentos_gerados/`.

---

## Implementação

Implementação sequencial em arquivo único `gerar_documentos.py`. A ordem de execução espelha a ordem dos documentos no JSON: para cada documento, `processar_documentos` identifica o tipo via `doc["tipo"]` e despacha para o handler correspondente — se o primeiro documento for `.eml`, `criar_eml` é chamado primeiro; se for `.pdf`, `criar_pdf` é chamado primeiro, e assim por diante.

---

## Remoção de gerar_planilhas.py

O arquivo `gerar_planilhas.py` é **deletado do repositório** via `git rm`. Não há stub de compatibilidade; o substituto direto é `gerar_documentos.py` com a mesma interface de invocação.

---

## Tratamento de erros

| Situação | Comportamento |
|---|---|
| JSON malformado | Exceção propagada — execução interrompida |
| Tipo de documento desconhecido | Aviso impresso, documento pulado, execução continua |
| Falha dentro de um handler | Exceção capturada, erro impresso, próximo documento processado |

---

## Fora de escopo

- Geração de imagens dentro dos documentos
- Estilização avançada (fontes customizadas, temas, logos)
- Validação do conteúdo das inconsistências
- Suporte a tipos além dos cinco listados
