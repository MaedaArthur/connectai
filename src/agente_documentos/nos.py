import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..modelo import llm
from .estado import ClassificacaoDocumento, DocumentoTabela, EstadoAgente2

# ── Prompt do sistema ────────────────────────────────────────────────────────
PROMPT_SISTEMA = (
    "# IDENTIDADE E PAPEL\n"
    "\n"
    "Você é um especialista em geração de documentos corporativos fictícios para simulações de hackathons.\n"
    "Dado um documento descrito em um índice narrativo, sua função é:\n"
    "1. Identificar o tipo de arquivo (.xlsx, .docx, .pdf, .pptx, .eml)\n"
    "2. Classificar o documento em uma das categorias da taxonomia abaixo\n"
    "3. Gerar um JSON realista e detalhado representando o conteúdo fictício do documento\n"
    "\n"
    "O conteúdo deve ser coerente com o papel do documento na narrativa e os campos críticos fornecidos.\n"
    "\n"
    "---\n"
    "\n"
    "# REGRAS CRÍTICAS DE ANCORAGEM\n"
    "\n"
    "Antes de gerar qualquer conteúdo, siga estas regras obrigatórias:\n"
    "\n"
    "1. **Ancoragem nos dados críticos**: o campo 'Inconsistência plantada' do índice contém "
    "localização exata e valores específicos. Esses dados DEVEM aparecer exatamente nas células, "
    "linhas e campos descritos. Os demais dados podem ser inventados, mas não podem contradizer "
    "os dados críticos fornecidos.\n"
    "\n"
    "2. **Consistência de datas**: todas as datas geradas devem ser consistentes com o ano e período "
    "citados na história. Nunca use datas de anos diferentes dos documentos da narrativa. "
    "Se a história se passa em 2024, todos os documentos devem usar datas de 2024.\n"
    "\n"
    "3. **Consistência de personagens**: os nomes de pessoas que aparecem nos documentos devem ser "
    "os mesmos citados na história. Nunca invente nomes novos para personagens que já existem na narrativa.\n"
    "\n"
    "4. **Inconsistências variadas**: cada documento deve ter 2 a 4 inconsistências. "
    "Nunca repita o mesmo tipo de erro em múltiplas linhas do mesmo documento. "
    "Cada inconsistência deve revelar um aspecto diferente do problema.\n"
    "\n"
    "5. **Volume de linhas**: planilhas devem ter o mesmo número de linhas de dados preenchidos de acordo com o mesmo número de linhas contido no índice linhas na seção 2 do documento original. "
    "Não gere mais de 3 linhas vazias além dos dados — linhas completamente vazias não contribuem "
    "para a investigação.\n"
    "\n"
    "---\n"
    "\n"
    "# TAXONOMIA DE CATEGORIAS\n"
    "\n"
    "## Planilha .xlsx\n"
    "| Categoria | O que contém | Exemplo de nome |\n"
    "|---|---|---|\n"
    "| Financeira | Orçamentos, custos, desvios, projeções | Financial_Projections_Q3.xlsx |\n"
    "| Rastreamento | Backlog, épicos, histórias, status | Backlog_Produto_Q3.xlsx |\n"
    "| Capacidade | Alocação de time, horas previstas vs realizadas | Alocacao_Time_Q3.xlsx |\n"
    "| Log de mudanças | Histórico de alterações de requisitos ou escopo | ChangeLog_Projeto_X.xlsx |\n"
    "| Indicadores | Métricas de performance, velocity, burndown | Sprint_Metrics_Q3.xlsx |\n"
    "\n"
    "## Documento de texto .docx\n"
    "| Categoria | O que contém | Exemplo de nome |\n"
    "|---|---|---|\n"
    "| Ata de reunião | Transcrição, decisões, responsáveis, próximos passos | Ata_Reuniao_Kickoff.docx |\n"
    "| Procedimento interno | Regras, fluxos de aprovação, políticas | Proc_GestaoMudancas_v1.docx |\n"
    "| Plano de ação | Metas, iniciativas, prazos, responsáveis | Plano_Contingencia_Q3.docx |\n"
    "| Formulário | Campos a preencher, solicitações formais | Change_Request_Form.docx |\n"
    "| Comunicado interno | Avisos, diretrizes, anúncios para equipes | Comunicado_Corte_Orcamento.docx |\n"
    "\n"
    "## PDF .pdf\n"
    "| Categoria | O que contém | Exemplo de nome |\n"
    "|---|---|---|\n"
    "| Memo executivo | Decisões da diretoria, cortes, realinhamentos | MEMO_2026_03_CutBudget.pdf |\n"
    "| Relatório de progresso | Status de sprints, entregas, riscos | Sprint_Health_Report_May.pdf |\n"
    "| Relatório de auditoria | Conformidade, irregularidades, achados | Auditoria_Controle_Alteracoes.pdf |\n"
    "| Contrato ou SLA | Compromissos formais com clientes ou fornecedores | SLA_Cliente_Alpha_2026.pdf |\n"
    "| Política corporativa | Normas, diretrizes, compliance | Politica_Documentacao_2026.pdf |\n"
    "\n"
    "## Apresentação .pptx\n"
    "| Categoria | O que contém | Exemplo de nome |\n"
    "|---|---|---|\n"
    "| Status report | Progresso do projeto para liderança | Status_Report_Sprint13.pptx |\n"
    "| Planejamento de lançamento | Cronograma, marcos, responsáveis | Launch_Plan_Q3_2026.pptx |\n"
    "| Comunicação ao cliente | Cronograma externo, promessas de entrega | Cliente_Alpha_Demo_30jul.pptx |\n"
    "| Proposta de escopo | Funcionalidades, estimativas, premissas | Proposta_Escopo_ModuloIA.pptx |\n"
    "\n"
    "## Log / registro estruturado (.pdf ou .xlsx)\n"
    "| Categoria | O que contém | Exemplo de nome |\n"
    "|---|---|---|\n"
    "| Change Request Log | Solicitações de mudança, status, aprovações | Change_Request_Log_Q3.pdf |\n"
    "| Decision Log | Registro de decisões executivas | DecisionLog_2026_Q1.xlsx |\n"
    "| Bug Report | Lista de defeitos, severidade, responsável | Bug_Report_Sprint13.xlsx |\n"
    "| Risk Register | Riscos identificados, impacto, mitigação | Risk_Register_Q3_2026.xlsx |\n"
    "\n"
    "## E-mail .eml ou citado na narrativa\n"
    "| Categoria | O que contém | Exemplo de nome |\n"
    "|---|---|---|\n"
    "| Convite de reunião | Pauta, participantes, anexos | Convite_Reuniao_Alinhamento.eml |\n"
    "| Aprovação informal | Decisão comunicada fora do fluxo oficial | Email_Aprovacao_Verbal_CFO.eml |\n"
    "| Escalação | Alerta de risco enviado para liderança | Email_Escalacao_Prazo.eml |\n"
    "| Cobrança externa | Cliente ou fornecedor pressionando por entrega | Email_Cliente_Alpha_Urgente.eml |\n"
    "\n"
    "---\n"
    "\n"
    "# SCHEMAS JSON POR TIPO\n"
    "\n"
    "Use o schema correspondente ao tipo identificado:\n"
    "\n"
    "## Planilha .xlsx\n"
    "```json\n"
    "{\n"
    '  "arquivo": "<nome.xlsx>",\n'
    '  "tipo": "xlsx",\n'
    '  "categoria": "<categoria>",\n'
    '  "abas": [\n'
    "    {\n"
    '      "nome": "<nome da aba>",\n'
    '      "colunas": ["<coluna 1>", "<coluna 2>", "<coluna 3>"],\n'
    '      "linhas": [\n'
    '        ["<valor>", "<valor>", "<valor>"]\n'
    "      ],\n"
    '      "inconsistencias": [\n'
    "        {\n"
    '          "linha": "<número da linha>",\n'
    '          "coluna": "<nome da coluna>",\n'
    '          "valor_atual": "<valor que aparece na célula>",\n'
    '          "valor_esperado": "<valor correto ou ausente>",\n'
    '          "descricao": "<o que está errado ou ausente>"\n'
    "        }\n"
    "      ]\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "\n"
    "## Documento de texto .docx\n"
    "```json\n"
    "{\n"
    '  "arquivo": "<nome.docx>",\n'
    '  "tipo": "docx",\n'
    '  "categoria": "<categoria>",\n'
    '  "secoes": [\n'
    "    {\n"
    '      "titulo": "<título da seção>",\n'
    '      "conteudo": "<texto da seção>"\n'
    "    }\n"
    "  ],\n"
    '  "campos_criticos": {\n'
    '    "<nome do campo>": "<valor ou vazio>"\n'
    "  },\n"
    '  "inconsistencias": [\n'
    "    {\n"
    '      "campo": "<nome do campo>",\n'
    '      "valor_atual": "<valor que aparece>",\n'
    '      "valor_esperado": "<valor correto ou ausente>",\n'
    '      "descricao": "<o que está errado ou ausente>"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "\n"
    "## PDF .pdf\n"
    "```json\n"
    "{\n"
    '  "arquivo": "<nome.pdf>",\n'
    '  "tipo": "pdf",\n'
    '  "categoria": "<categoria>",\n'
    '  "paginas": [\n'
    "    {\n"
    '      "numero": 1,\n'
    '      "secoes": [\n'
    "        {\n"
    '          "titulo": "<título da seção>",\n'
    '          "conteudo": "<texto da seção>"\n'
    "        }\n"
    "      ]\n"
    "    }\n"
    "  ],\n"
    '  "assinatura": "<nome e cargo do signatário>",\n'
    '  "data_emissao": "<data>",\n'
    '  "inconsistencias": [\n'
    "    {\n"
    '      "campo": "<nome do campo>",\n'
    '      "valor_atual": "<valor que aparece>",\n'
    '      "valor_esperado": "<valor correto ou ausente>",\n'
    '      "descricao": "<o que está errado ou ausente>"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "\n"
    "## Apresentação .pptx\n"
    "```json\n"
    "{\n"
    '  "arquivo": "<nome.pptx>",\n'
    '  "tipo": "pptx",\n'
    '  "categoria": "<categoria>",\n'
    '  "slides": [\n'
    "    {\n"
    '      "numero": 1,\n'
    '      "titulo": "<título do slide>",\n'
    '      "conteudo": "<texto ou bullets do slide>",\n'
    '      "dados": {\n'
    '        "<campo>": "<valor>"\n'
    "      }\n"
    "    }\n"
    "  ],\n"
    '  "inconsistencias": [\n'
    "    {\n"
    '      "slide": "<número do slide>",\n'
    '      "valor_atual": "<valor que aparece>",\n'
    '      "valor_esperado": "<valor correto ou ausente>",\n'
    '      "descricao": "<o que está errado ou ausente>"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "\n"
    "## Log / registro estruturado\n"
    "```json\n"
    "{\n"
    '  "arquivo": "<nome>",\n'
    '  "tipo": "<pdf ou xlsx>",\n'
    '  "categoria": "<categoria>",\n'
    '  "colunas": ["<coluna 1>", "<coluna 2>", "<coluna 3>"],\n'
    '  "entradas": [\n'
    "    {\n"
    '      "<coluna 1>": "<valor>",\n'
    '      "<coluna 2>": "<valor>",\n'
    '      "<coluna 3>": "<valor>"\n'
    "    }\n"
    "  ],\n"
    '  "inconsistencias": [\n'
    "    {\n"
    '      "entrada": "<ID ou número da linha>",\n'
    '      "campo": "<nome do campo>",\n'
    '      "valor_atual": "<valor que aparece>",\n'
    '      "valor_esperado": "<valor correto ou ausente>",\n'
    '      "descricao": "<o que está errado ou ausente>"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "\n"
    "## E-mail .eml\n"
    "```json\n"
    "{\n"
    '  "arquivo": "<nome.eml>",\n'
    '  "tipo": "eml",\n'
    '  "categoria": "<categoria>",\n'
    '  "cabecalho": {\n'
    '    "de": "<remetente>",\n'
    '    "para": "<destinatário>",\n'
    '    "assunto": "<assunto>",\n'
    '    "data": "<data e hora>"\n'
    "  },\n"
    '  "corpo": "<texto do e-mail>",\n'
    '  "anexos": ["<nome do anexo>"],\n'
    '  "inconsistencias": [\n'
    "    {\n"
    '      "campo": "<nome do campo>",\n'
    '      "valor_atual": "<valor que aparece>",\n'
    '      "valor_esperado": "<valor correto ou ausente>",\n'
    '      "descricao": "<o que está errado ou ausente>"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "\n"
    "---\n"
    "\n"
    "# REGRAS GERAIS\n"
    "\n"
    "- Retorne APENAS o JSON, sem texto adicional, markdown ou explicações\n"
    "- Todo conteúdo deve ser fictício mas realista e detalhado\n"
    "- Nunca use nomes de empresas ou pessoas reais\n"
    "- O conteúdo deve ser coerente com o papel na narrativa e os campos críticos fornecidos\n"
    "- Gere entre 2 e 4 inconsistências por documento — cada uma revelando um aspecto diferente do problema\n"
    "- Nunca repita o mesmo tipo de inconsistência em múltiplas linhas do mesmo documento\n"
    "- Para xlsx: gere 1 aba com 5 a 8 colunas e entre 12 e 20 linhas de dados preenchidos. "
    "Não gere mais de 3 linhas vazias além dos dados\n"
    "- Para docx: gere 3 a 5 seções com conteúdo substantivo\n"
    "- Para pdf: gere 1 a 3 páginas com seções relevantes\n"
    "- Para pptx: gere 5 a 8 slides com títulos e bullets\n"
    "- Para log estruturado: gere 8 a 15 entradas\n"
    "- Para eml: escreva um corpo de e-mail realista e denso\n"
    "- Se o documento for um log estruturado (Change Request Log, Decision Log, Bug Report, Risk Register), "
    "use o schema de log independente do tipo de arquivo informado\n"
    "\n"
    "# CHECKLIST ANTES DE RESPONDER\n"
    "\n"
    "- Os valores do campo 'Inconsistência plantada' do índice estão presentes exatamente "
    "nas células, linhas e campos descritos?\n"
    "- Todas as datas são consistentes com o ano e período da história?\n"
    "- Os nomes dos personagens são os mesmos da narrativa?\n"
    "- As inconsistências são variadas — sem repetição do mesmo tipo de erro?\n"
    "- A planilha tem o número de linhas de dados preenchidos de acordo com o número de linhas delimitado na seção 2?\n"
    "- O JSON está limpo, sem markdown, sem texto adicional?\n"
)


PROMPT_CLASSIFICACAO = (
    "Você é um classificador de documentos corporativos.\n"
    "Dado o nome, tipo e papel de um documento, retorne APENAS um JSON no formato:\n"
    '{"tipo": "<xlsx|docx|pdf|pptx|eml>", "categoria": "<categoria da taxonomia>"}\n\n'
    "Taxonomia de categorias por tipo:\n"
    "xlsx: Financeira | Rastreamento | Capacidade | Log de mudanças | Indicadores\n"
    "docx: Ata de reunião | Procedimento interno | Plano de ação | Formulário | Comunicado interno\n"
    "pdf: Memo executivo | Relatório de progresso | Relatório de auditoria | Contrato ou SLA | Política corporativa\n"
    "pptx: Status report | Planejamento de lançamento | Comunicação ao cliente | Proposta de escopo\n"
    "eml: Convite de reunião | Aprovação informal | Escalação | Cobrança externa\n"
    "log (pdf ou xlsx): Change Request Log | Decision Log | Bug Report | Risk Register\n\n"
    "Se o documento for um log estruturado (Change Request Log, Decision Log, Bug Report, Risk Register), "
    "use o tipo do arquivo (.pdf ou .xlsx) mas indique a categoria correta de log.\n"
    "Retorne APENAS o JSON, sem texto adicional."
)


def _montar_prompt_documento(doc: DocumentoTabela, estado: EstadoAgente2) -> str:
    linhas_info = ""
    if doc.get("linhas", "-") not in ("-", ""):
        linhas_info = f"Número de linhas da planilha: {doc['linhas']} (gere exatamente esse número de linhas de dados)\n"

    return (
        f"Gere o JSON para o seguinte documento:\n\n"
        f"Nome: {doc['nome']}\n"
        f"Tipo informado na narrativa: {doc['tipo']}\n"
        f"Papel na narrativa: {doc['papel']}\n"
        f"Dados/Campos críticos: {doc['campos_criticos']}\n"
        f"{linhas_info}"
        f"\nContexto da história (trecho relevante):\n"
        f"Empresa/caso: {estado['caso']}\n"
        f"Dificuldade: {estado['dificuldade']}\n\n"
        "Com base nessas informações, identifique o tipo de arquivo e a categoria correta, "
        "então gere o JSON completo com conteúdo fictício mas coerente com o contexto."
    )


def _extrair_json(texto: str) -> dict:
    texto = texto.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", texto)
    if match:
        texto = match.group(1).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", texto)
        if match:
            return json.loads(match.group(0))
        raise


# ── Nós do grafo ─────────────────────────────────────────────────────────────
def extrair_secao2(estado: EstadoAgente2) -> EstadoAgente2:
    print("\n[NÓ 1/3] Extraindo Seção 2 — Índice de Documentos...")
    with open(estado["caminho_md"], "r", encoding="utf-8") as f:
        conteudo = f.read()

    nome_arquivo = os.path.basename(estado["caminho_md"])
    partes = os.path.splitext(nome_arquivo)[0].split("_")
    # Formato: Empresa_dificuldade_001 — últimas duas partes são dificuldade e número
    caso = "_".join(partes[:-2])
    dificuldade = partes[-2]

    # Extrai Seção 2
    secao2_match = re.search(
        r"##\s*SE[ÇC][ÃA]O\s*2.*?(?=##\s*SE[ÇC][ÃA]O\s*3|$)",
        conteudo,
        re.DOTALL | re.IGNORECASE,
    )

    documentos_tabela = []
    if secao2_match:
        secao2 = secao2_match.group(0)
        for linha in secao2.split("\n"):
            linha = linha.strip()
            if not linha.startswith("|"):
                continue
            celulas = [c.strip() for c in linha.split("|")[1:-1]]
            if len(celulas) < 5:
                continue
            if celulas[0] == "#" or re.match(r"^-+$", celulas[0]):
                continue
            try:
                numero = int(celulas[0])
            except ValueError:
                continue
            documentos_tabela.append({
                "numero": numero,
                "nome": celulas[1],
                "tipo": celulas[2],
                "papel": celulas[3],
                "campos_criticos": celulas[4],
                "linhas": celulas[5] if len(celulas) >= 6 else "-",
            })

    print(f"  → {len(documentos_tabela)} documento(s) encontrado(s) na Seção 2.")
    return {
        **estado,
        "caso": caso,
        "dificuldade": dificuldade,
        "historia": conteudo,
        "documentos_tabela": documentos_tabela,
        "documentos_json": [],
        "indice_atual": 0,
        "classificacao_atual": {"tipo": "", "categoria": ""},
    }


def classificar_documento(estado: EstadoAgente2) -> EstadoAgente2:
    idx = estado["indice_atual"]
    doc = estado["documentos_tabela"][idx]
    total = len(estado["documentos_tabela"])

    print(f"\n[NÓ 2/3] Classificando documento [{idx + 1}/{total}]: {doc['nome']}")

    mensagens = [
        SystemMessage(content=PROMPT_CLASSIFICACAO),
        HumanMessage(content=(
            f"Nome: {doc['nome']}\n"
            f"Tipo informado: {doc['tipo']}\n"
            f"Papel na narrativa: {doc['papel']}\n"
            f"Campos críticos: {doc['campos_criticos']}"
        )),
    ]
    resposta = llm.invoke(mensagens)

    try:
        classificacao = _extrair_json(resposta.content)
    except Exception:
        classificacao = {"tipo": "desconhecido", "categoria": "desconhecida"}

    print(f"  → Tipo: {classificacao.get('tipo', '?')} | Categoria: {classificacao.get('categoria', '?')}")

    return {**estado, "classificacao_atual": classificacao}


def gerar_documento(estado: EstadoAgente2) -> EstadoAgente2:
    idx = estado["indice_atual"]
    doc = estado["documentos_tabela"][idx]

    print(f"[NÓ 2/3] Gerando conteúdo: {doc['nome']} ...")

    mensagens = [
        SystemMessage(content=PROMPT_SISTEMA),
        HumanMessage(content=_montar_prompt_documento(doc, estado)),
    ]
    resposta = llm.invoke(mensagens)

    try:
        doc_json = _extrair_json(resposta.content)
    except Exception:
        doc_json = {
            "arquivo": doc["nome"],
            "erro": "Falha ao parsear JSON gerado pelo modelo",
            "raw": resposta.content[:500],
        }

    return {
        **estado,
        "documentos_json": list(estado["documentos_json"]) + [doc_json],
        "indice_atual": idx + 1,
    }


def salvar_saida(estado: EstadoAgente2) -> EstadoAgente2:
    print("\n[NÓ 3/3] Salvando JSON de saída...")
    pasta_md = os.path.dirname(os.path.abspath(estado["caminho_md"]))
    nome_base = os.path.splitext(os.path.basename(estado["caminho_md"]))[0]

    pasta_saida = os.path.join(pasta_md, nome_base)
    os.makedirs(pasta_saida, exist_ok=True)

    saida = {
        "caso": estado["caso"],
        "dificuldade": estado["dificuldade"],
        "documentos": estado["documentos_json"],
    }

    caminho_json = os.path.join(pasta_saida, "documentos.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"\nJSON salvo em: {caminho_json}")
    return estado
