from typing import List, TypedDict


class DocumentoTabela(TypedDict):
    numero: int
    nome: str
    tipo: str
    papel: str
    campos_criticos: str
    linhas: str  # número de linhas se planilha, "-" caso contrário


class ClassificacaoDocumento(TypedDict):
    tipo: str
    categoria: str


class EstadoAgente2(TypedDict):
    caminho_md: str
    caso: str
    dificuldade: str
    historia: str
    documentos_tabela: List[DocumentoTabela]
    documentos_json: List[dict]
    indice_atual: int
    classificacao_atual: ClassificacaoDocumento
