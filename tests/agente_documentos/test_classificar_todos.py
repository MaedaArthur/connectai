import json
from unittest.mock import MagicMock, patch

from src.agente_documentos.nos import classificar_todos


def _make_estado(docs, historia="## SEÇÃO 1\nNarrativa de teste.\n\n## SEÇÃO 2\n"):
    return {
        "caminho_md": "/fake/caso.md",
        "caso": "TesteCaso",
        "dificuldade": "baixa",
        "historia": historia,
        "documentos_tabela": docs,
        "documentos_json": [],
        "indice_atual": 0,
        "classificacoes": {},
    }


def _make_doc(nome="relatorio.xlsx", tipo="xlsx"):
    return {
        "numero": 1,
        "nome": nome,
        "tipo": tipo,
        "papel": "Relatório financeiro principal",
        "estrutura": "1 aba: Dados",
        "inconsistencia": "Valor errado na linha 3",
        "docs_relacionados": "-",
    }


def test_classificar_todos_popula_classificacoes():
    """Classificações de todos os documentos são armazenadas no estado."""
    docs = [_make_doc("rel.xlsx", "xlsx"), _make_doc("ata.docx", "docx")]
    estado = _make_estado(docs)

    resposta_llm = json.dumps({
        "rel.xlsx": {"tipo": "xlsx", "categoria": "Financeira"},
        "ata.docx": {"tipo": "docx", "categoria": "Ata de reunião"},
    })
    mock_resposta = MagicMock()
    mock_resposta.content = resposta_llm

    with patch("src.agente_documentos.nos.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_resposta
        resultado = classificar_todos(estado)

    assert resultado["classificacoes"]["rel.xlsx"] == {"tipo": "xlsx", "categoria": "Financeira"}
    assert resultado["classificacoes"]["ata.docx"] == {"tipo": "docx", "categoria": "Ata de reunião"}


def test_classificar_todos_fallback_parse_total():
    """Se o LLM retornar algo que não é JSON, o fallback usa tipo da tabela."""
    docs = [_make_doc("rel.xlsx", "xlsx")]
    estado = _make_estado(docs)

    mock_resposta = MagicMock()
    mock_resposta.content = "isso não é json"

    with patch("src.agente_documentos.nos.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_resposta
        resultado = classificar_todos(estado)

    assert resultado["classificacoes"]["rel.xlsx"]["tipo"] == "xlsx"
    assert resultado["classificacoes"]["rel.xlsx"]["categoria"] == ""


def test_classificar_todos_fallback_parcial():
    """Se o LLM omitir algum documento, o fallback preenche os ausentes."""
    docs = [_make_doc("rel.xlsx", "xlsx"), _make_doc("ata.docx", "docx")]
    estado = _make_estado(docs)

    resposta_parcial = json.dumps({
        "rel.xlsx": {"tipo": "xlsx", "categoria": "Financeira"},
    })
    mock_resposta = MagicMock()
    mock_resposta.content = resposta_parcial

    with patch("src.agente_documentos.nos.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_resposta
        resultado = classificar_todos(estado)

    assert resultado["classificacoes"]["rel.xlsx"]["categoria"] == "Financeira"
    assert resultado["classificacoes"]["ata.docx"]["tipo"] == "docx"
    assert resultado["classificacoes"]["ata.docx"]["categoria"] == ""


def test_classificar_todos_llm_recebe_todos_documentos():
    """O LLM deve receber todos os documentos na mensagem human."""
    docs = [_make_doc("rel.xlsx"), _make_doc("ata.docx")]
    estado = _make_estado(docs)

    mock_resposta = MagicMock()
    mock_resposta.content = json.dumps({
        "rel.xlsx": {"tipo": "xlsx", "categoria": "Financeira"},
        "ata.docx": {"tipo": "docx", "categoria": "Ata de reunião"},
    })

    with patch("src.agente_documentos.nos.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_resposta
        classificar_todos(estado)

    mensagens = mock_llm.invoke.call_args[0][0]
    human_content = mensagens[1].content
    assert "rel.xlsx" in human_content
    assert "ata.docx" in human_content
