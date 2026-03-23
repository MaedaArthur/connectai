from langgraph.graph import END, StateGraph

from .estado import EstadoAgente2
from .nos import enriquecer_documentos, extrair_secao2, gerar_todos_documentos, salvar_saida


def _tem_documentos(estado: EstadoAgente2) -> str:
    if estado["documentos_tabela"]:
        return "enriquecer_documentos"
    return "salvar_saida"


grafo2 = StateGraph(EstadoAgente2)
grafo2.add_node("extrair_secao2", extrair_secao2)
grafo2.add_node("enriquecer_documentos", enriquecer_documentos)
grafo2.add_node("gerar_todos_documentos", gerar_todos_documentos)
grafo2.add_node("salvar_saida", salvar_saida)

grafo2.set_entry_point("extrair_secao2")
grafo2.add_conditional_edges("extrair_secao2", _tem_documentos)
grafo2.add_edge("enriquecer_documentos", "gerar_todos_documentos")
grafo2.add_edge("gerar_todos_documentos", "salvar_saida")
grafo2.add_edge("salvar_saida", END)

app2 = grafo2.compile()
