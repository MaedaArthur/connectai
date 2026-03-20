from typing import Annotated, List, TypedDict
from langgraph.graph.message import add_messages


class EntradaHistoria(TypedDict):
    empresa: str
    setor: str
    cargo: str
    dificuldade: str
    sintomas: List[str]
    causas_raiz: dict  # {"principal": str, "secundarias": List[str]}


class EstadoGrafo(TypedDict):
    entrada: EntradaHistoria
    historia: str
    historico: Annotated[List, add_messages]
    feedback: str
