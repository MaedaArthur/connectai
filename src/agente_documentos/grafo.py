from langgraph.graph import END, StateGraph

from .estado import EstadoAgente2
from .nos import classificar_documento, extrair_secao2, gerar_documento, salvar_saida


def _tem_documentos(estado: EstadoAgente2) -> str:
    if estado["indice_atual"] < len(estado["documentos_tabela"]):
        return "classificar_documento"
    return "salvar_saida"


def _apos_gerar(estado: EstadoAgente2) -> str:
    if estado["indice_atual"] < len(estado["documentos_tabela"]):
        return "classificar_documento"
    return "salvar_saida"


grafo2 = StateGraph(EstadoAgente2)
grafo2.add_node("extrair_secao2", extrair_secao2)
grafo2.add_node("classificar_documento", classificar_documento)
grafo2.add_node("gerar_documento", gerar_documento)
grafo2.add_node("salvar_saida", salvar_saida)

grafo2.set_entry_point("extrair_secao2")
grafo2.add_conditional_edges("extrair_secao2", _tem_documentos)
grafo2.add_edge("classificar_documento", "gerar_documento")
grafo2.add_conditional_edges("gerar_documento", _apos_gerar)
grafo2.add_edge("salvar_saida", END)

app2 = grafo2.compile()
