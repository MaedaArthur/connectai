from typing import Dict, List, TypedDict


class DocumentoTabela(TypedDict):
    numero: int
    nome: str
    tipo: str
    papel: str
    estrutura: str
    inconsistencia: str
    docs_relacionados: str


class ClassificacaoDocumento(TypedDict):
    tipo: str
    categoria: str


class ContextoDocumento(TypedDict):
    personagens: List[str]
    eventos_chave: List[str]
    datas_criticas: List[str]
    contexto_do_documento: str
    trecho_inconsistencia: str
    estrutura: str


class EstadoAgente2(TypedDict):
    caminho_md: str
    caso: str
    dificuldade: str
    historia: str
    documentos_tabela: List[DocumentoTabela]
    documentos_json: List[dict]
    indice_atual: int
    classificacoes: Dict[str, ClassificacaoDocumento]
    contextos_documentos: Dict[str, ContextoDocumento]
