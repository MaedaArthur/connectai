import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..modelo import llm
from .estado import ClassificacaoDocumento, ContextoDocumento, DocumentoTabela, EstadoAgente2

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
    "O conteúdo deve ser coerente com a narrativa completa fornecida, o papel do documento "
    "e os campos críticos do índice.\n"
    "\n"
    "---\n"
    "\n"
    "# REGRAS CRÍTICAS DE ANCORAGEM\n"
    "\n"
    "Antes de gerar qualquer conteúdo, siga estas regras obrigatórias:\n"
    "\n"
    "1. **Ancoragem na narrativa**: use o contexto extraído da história fornecido no prompt (personagens, "
    "eventos-chave, datas críticas e contexto do documento). "
    "O conteúdo, os personagens, as datas e os valores devem ser consistentes com esse contexto. "
    "Se o contexto menciona que um campo estava vazio, ele deve estar vazio no JSON gerado.\n"
    "\n"
    "2. **Ancoragem nos dados críticos**: o campo 'Inconsistência plantada' do índice contém "
    "localização exata e valores específicos. Esses dados DEVEM aparecer exatamente nas abas, células "
    "e campos descritos. Os demais dados podem ser inventados, mas não podem contradizer "
    "os dados críticos fornecidos.\n"
    "\n"
    "3. **Estrutura de abas para planilhas**: o campo 'Estrutura' do índice define quantas abas "
    "a planilha deve ter e quantas linhas cada aba deve conter. Respeite exatamente essa estrutura. "
    "Nunca gere uma planilha com menos abas do que o especificado.\n"
    "\n"
    "4. **Distribuição de inconsistências por aba**: "
    "a inconsistência VISÍVEL deve estar na primeira aba. "
    "a inconsistência CRUZADA deve exigir comparar dados entre a primeira e a segunda aba. "
    "a inconsistência SISTÊMICA deve exigir comparar uma aba com outro documento do caso — "
    "use o campo 'Causa raiz principal' e os 'Documentos relacionados' para calibrar essa inconsistência.\n"
    "\n"
    "5. **Consistência de datas**: todas as datas geradas devem ser consistentes com o ano e período "
    "citados na história. Nunca use datas de anos diferentes dos documentos da narrativa.\n"
    "\n"
    "6. **Consistência de personagens**: os nomes de pessoas que aparecem nos documentos devem ser "
    "os mesmos citados na história. Nunca invente nomes novos para personagens que já existem na narrativa.\n"
    "\n"
    "7. **Inconsistências variadas**: cada documento deve ter 2 a 4 inconsistências. "
    "Nunca repita o mesmo tipo de erro em múltiplas linhas do mesmo documento. "
    "Cada inconsistência deve revelar um aspecto diferente do problema.\n"
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
    '  "secoes": [\n'
    "    {\n"
    '      "titulo": "<título da seção>",\n'
    '      "conteudo": "<texto da seção>"\n'
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
    "- O conteúdo deve ser coerente com a narrativa completa e os campos críticos fornecidos\n"
    "- Gere entre 2 e 4 inconsistências por documento — cada uma revelando um aspecto diferente do problema\n"
    "- Nunca repita o mesmo tipo de inconsistência em múltiplas linhas do mesmo documento\n"
    "- Para xlsx: respeite exatamente a estrutura de abas definida no campo 'Estrutura' do índice. "
    "Cada aba deve ter entre 8 e 15 linhas de dados preenchidos. "
    "Não gere mais de 3 linhas vazias além dos dados por aba.\n"
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
    "- O contexto extraído da história (personagens, eventos, datas, inconsistência) foi utilizado?\n"
    "- Os valores do campo 'Inconsistência plantada' do índice estão presentes exatamente "
    "nas abas, células, linhas e campos descritos?\n"
    "- Para planilhas: o número de abas e linhas por aba corresponde ao campo 'Estrutura' do índice?\n"
    "- A inconsistência VISÍVEL está na primeira aba?\n"
    "- A inconsistência CRUZADA exige comparar dados entre abas da mesma planilha?\n"
    "- A inconsistência SISTÊMICA exige cruzar com outro documento do caso?\n"
    "- Todas as datas são consistentes com o ano e período da história?\n"
    "- Os nomes dos personagens são os mesmos da narrativa?\n"
    "- As inconsistências são variadas — sem repetição do mesmo tipo de erro?\n"
    "- O JSON está limpo, sem markdown, sem texto adicional?\n"
)



PROMPT_CLASSIFICACAO = (
    "Você é um classificador de documentos corporativos.\n"
    "Dado uma lista de documentos, retorne APENAS um JSON no formato:\n"
    '{"nome_arquivo.ext": {"tipo": "<xlsx|docx|pdf|pptx|eml>", "categoria": "<categoria da taxonomia>"}, ...}\n\n'
    "Taxonomia de categorias por tipo:\n"
    "xlsx: Financeira | Rastreamento | Capacidade | Log de mudanças | Indicadores\n"
    "docx: Ata de reunião | Procedimento interno | Plano de ação | Formulário | Comunicado interno\n"
    "pdf: Memo executivo | Relatório de progresso | Relatório de auditoria | Contrato ou SLA | Política corporativa\n"
    "pptx: Status report | Planejamento de lançamento | Comunicação ao cliente | Proposta de escopo\n"
    "eml: Convite de reunião | Aprovação informal | Escalação | Cobrança externa\n"
    "log (pdf ou xlsx): Change Request Log | Decision Log | Bug Report | Risk Register\n\n"
    "Se o documento for um log estruturado, use o tipo do arquivo (.pdf ou .xlsx) mas indique a categoria correta de log.\n"
    "Retorne APENAS o JSON, sem texto adicional."
)


# ── Prompt de enriquecimento de contexto ─────────────────────────────────────
PROMPT_ENRIQUECIMENTO = (
    "Você é um extrator de contexto narrativo. Dada uma história corporativa e uma lista de documentos, "
    "sua tarefa é extrair as informações relevantes da narrativa para cada documento.\n\n"
    "Para cada documento, retorne um objeto JSON com os seguintes campos:\n"
    "- personagens: lista de strings com nome e papel dos personagens relevantes para este documento "
    "(ex: [\"Marcos Lima (PM)\", \"Carla Souza (Dev Lead)\"])\n"
    "- eventos_chave: lista de strings com eventos da narrativa que este documento evidencia ou registra\n"
    "- datas_criticas: lista de strings com datas e prazos relevantes para este documento "
    "(ex: [\"31/07/2026 - deadline do release\"])\n"
    "- contexto_do_documento: parágrafo curto (2-3 frases) explicando o papel deste documento na narrativa\n"
    "- trecho_inconsistencia: copie LITERALMENTE o texto do campo 'Inconsistência plantada' fornecido "
    "para este documento, sem alterações\n"
    "- estrutura: copie LITERALMENTE o campo 'Estrutura' fornecido para este documento, sem alterações\n\n"
    "Retorne APENAS JSON puro, sem markdown, no formato:\n"
    "{\"nome_arquivo.ext\": {\"personagens\": [...], \"eventos_chave\": [...], "
    "\"datas_criticas\": [...], \"contexto_do_documento\": \"...\", "
    "\"trecho_inconsistencia\": \"...\", \"estrutura\": \"...\"}, ...}"
)


def enriquecer_documentos(estado: EstadoAgente2) -> EstadoAgente2:
    total = len(estado["documentos_tabela"])
    print(f"\n[NÓ 2.5/4] Enriquecendo contexto de {total} documento(s)...")

    linhas_docs = "\n".join(
        f"{i + 1}. Nome: {doc['nome']} | Tipo: {doc['tipo']} "
        f"| Papel: {doc['papel']} | Estrutura: {doc['estrutura']} "
        f"| Inconsistência plantada: {doc['inconsistencia']}"
        for i, doc in enumerate(estado["documentos_tabela"])
    )

    mensagens = [
        SystemMessage(content=PROMPT_ENRIQUECIMENTO),
        HumanMessage(content=(
            f"História completa:\n{estado['historia']}\n\n"
            f"Documentos a enriquecer:\n{linhas_docs}"
        )),
    ]
    resposta = llm.invoke(mensagens)

    try:
        contextos_raw = _extrair_json(resposta.content)
    except Exception:
        contextos_raw = {}

    contextos: dict[str, ContextoDocumento] = {}
    for doc in estado["documentos_tabela"]:
        nome = doc["nome"]
        raw = contextos_raw.get(nome, {})
        contextos[nome] = ContextoDocumento(
            personagens=raw.get("personagens", []),
            eventos_chave=raw.get("eventos_chave", []),
            datas_criticas=raw.get("datas_criticas", []),
            contexto_do_documento=raw.get("contexto_do_documento", doc["papel"]),
            trecho_inconsistencia=raw.get("trecho_inconsistencia", doc["inconsistencia"]),
            estrutura=raw.get("estrutura", doc["estrutura"]),
        )

    return {**estado, "contextos_documentos": contextos}


def _montar_prompt_documento(doc: DocumentoTabela, estado: EstadoAgente2) -> str:
    classificacao = estado.get("classificacoes", {}).get(doc["nome"], {})
    tipo_classificado = classificacao.get("tipo", doc["tipo"])
    categoria_classificada = classificacao.get("categoria", "")

    return (
        f"Gere o JSON para o seguinte documento:\n\n"
        f"Nome: {doc['nome']}\n"
        f"Tipo do arquivo: {tipo_classificado}\n"
        f"Categoria: {categoria_classificada}\n"
        f"Papel na narrativa: {doc['papel']}\n"
        f"Estrutura: {doc['estrutura']}\n"
        f"Inconsistência plantada: {doc['inconsistencia']}\n"
        f"Documentos relacionados para cruzamento: {doc.get('docs_relacionados', '-')}\n"
        f"\nContexto da história (trecho relevante):\n"
        f"Empresa/caso: {estado['caso']}\n"
        f"Dificuldade: {estado['dificuldade']}\n\n"
        f"Use o schema JSON correspondente ao tipo '{tipo_classificado}' e gere o conteúdo "
        "completo, fictício e coerente com o contexto."
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


def classificar_todos(estado: EstadoAgente2) -> EstadoAgente2:
    total = len(estado["documentos_tabela"])
    print(f"\n[NÓ 2/4] Classificando {total} documento(s) em lote...")

    historia = estado["historia"]

    secao1_match = re.search(
        r"##\s*SE[ÇC][ÃA]O\s*1.*?(?=##\s*SE[ÇC][ÃA]O\s*2|$)",
        historia,
        re.DOTALL | re.IGNORECASE,
    )
    secao_1 = secao1_match.group(0).strip() if secao1_match else historia

    causa_match = re.search(
        r"(?:causa\s+raiz\s+principal)[:\s]+(.*?)(?:\n\n|\n#|$)",
        historia,
        re.DOTALL | re.IGNORECASE,
    )
    causa_raiz = causa_match.group(1).strip() if causa_match else ""

    linhas_docs = "\n".join(
        f"{i + 1}. Nome: {doc['nome']} | Tipo: {doc['tipo']} "
        f"| Papel: {doc['papel']} | Estrutura: {doc['estrutura']}"
        for i, doc in enumerate(estado["documentos_tabela"])
    )

    mensagens = [
        SystemMessage(content=PROMPT_CLASSIFICACAO),
        HumanMessage(content=(
            f"NARRATIVA (SEÇÃO 1):\n{secao_1}\n\n"
            f"CAUSA RAIZ PRINCIPAL:\n{causa_raiz}\n\n"
            f"DOCUMENTOS A CLASSIFICAR:\n{linhas_docs}"
        )),
    ]

    resposta = llm.invoke(mensagens)

    try:
        classificacoes = _extrair_json(resposta.content)
    except Exception as e:
        print(f"  [AVISO] Falha ao parsear classificações em lote: {e}. Usando fallback.")
        classificacoes = {}

    for doc in estado["documentos_tabela"]:
        if doc["nome"] not in classificacoes:
            classificacoes[doc["nome"]] = {"tipo": doc["tipo"], "categoria": ""}

    for nome, cl in classificacoes.items():
        print(f"  → {nome}: {cl.get('tipo', '?')} / {cl.get('categoria', '?')}")

    return {**estado, "classificacoes": classificacoes}


# ── Nós do grafo ─────────────────────────────────────────────────────────────
def extrair_secao2(estado: EstadoAgente2) -> EstadoAgente2:
    print("\n[NÓ 1/4] Extraindo Seção 2 — Índice de Documentos...")
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
                "estrutura": celulas[4],
                "inconsistencia": celulas[5] if len(celulas) >= 6 else "-",
                "docs_relacionados": celulas[6] if len(celulas) >= 7 else "-",
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
        "classificacoes": {},
        "contextos_documentos": {},
    }


def gerar_documento(estado: EstadoAgente2) -> EstadoAgente2:
    idx = estado["indice_atual"]
    doc = estado["documentos_tabela"][idx]

    print(f"[NÓ 3/4] Gerando conteúdo: {doc['nome']} ...")

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
    print("\n[NÓ 4/4] Salvando JSON de saída...")
    pasta_caso = os.path.dirname(os.path.abspath(estado["caminho_md"]))

    os.makedirs(os.path.join(pasta_caso, "documentos", "documentos_gerados"), exist_ok=True)

    saida = {
        "caso": estado["caso"],
        "dificuldade": estado["dificuldade"],
        "documentos": estado["documentos_json"],
    }

    caminho_json = os.path.join(pasta_caso, "documentos", "documentos.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"\nJSON salvo em: {caminho_json}")
    return estado
