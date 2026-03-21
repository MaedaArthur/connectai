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

## Comportamento por tipo

### xlsx
- Usa `pandas` + `openpyxl` (lógica atual preservada)
- Detecta logs estruturados pelo campo `entradas`: gera uma única aba tabular com as colunas de `colunas` e linhas de `entradas`
- Caso padrão: itera `abas`, cada aba vira uma sheet com `colunas` e `linhas`

### docx
- Usa `python-docx`
- Itera `secoes`: cada seção → heading nível 1 com `titulo` + parágrafo com `conteudo`
- `campos_criticos` adicionados como tabela de duas colunas no final do documento (se presentes)

### pdf
- Usa `fpdf2`
- Itera `paginas`: cada página → `add_page()`, seções com título em negrito e corpo em texto normal
- `assinatura` e `data_emissao` inseridos no rodapé da última página
- Detecta logs estruturados pelo campo `entradas`: gera tabela com colunas do campo `colunas`

### pptx
- Usa `python-pptx`
- Itera `slides`: cada slide → layout "Title and Content", `titulo` no placeholder de título, `conteudo` no corpo
- `dados` do slide ignorados na renderização visual (estão no JSON para referência de inconsistências)

### eml
- Gera arquivo `.txt` (extensão `.eml` mantida no nome do arquivo)
- Formato:
  ```
  De: ...
  Para: ...
  Assunto: ...
  Data: ...

  <corpo>

  Anexos: ...
  ```

---

## processar_documentos

```python
def processar_documentos(caminho_json: str) -> None:
    dados = json.load(...)
    diretorio_saida = <pasta documentos_gerados>
    for doc in dados["documentos"]:
        handler = HANDLERS.get(doc["tipo"])
        if not handler:
            print(f"Tipo não suportado: {doc['tipo']}")
            continue
        caminho = os.path.join(diretorio_saida, doc["arquivo"])
        handler(caminho, doc)
        print(f"Criado: {caminho}")
```

---

## Invocação

```bash
python gerar_documentos.py outputs/TechCorp/TechCorp_baixa_001/documentos/documentos.json
```

Saída dos arquivos em `<pasta_do_json>/documentos_gerados/`.

---

## Paralelização da implementação

Cada handler será implementado por um agente independente:

| Agente | Responsabilidade |
|---|---|
| Agente 1 | `criar_xlsx` (adaptar lógica atual + suporte a logs) |
| Agente 2 | `criar_docx` |
| Agente 3 | `criar_pdf` |
| Agente 4 | `criar_pptx` |
| Agente 5 | `criar_eml` |
| Agente 6 | `processar_documentos` + `HANDLERS` + `main` + deps |

Os agentes trabalham de forma independente; o resultado é consolidado em `gerar_documentos.py`.

---

## Fora de escopo

- Geração de imagens dentro dos documentos
- Estilização avançada (fontes customizadas, temas, logos)
- Validação do conteúdo das inconsistências
- Suporte a tipos além dos cinco listados
