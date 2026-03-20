from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .estado import EstadoGrafo
from .nos import atualizar_historia, gerar_historia, salvar_historia

memoria = MemorySaver()

grafo = StateGraph(EstadoGrafo)
grafo.add_node("gerar_historia", gerar_historia)
grafo.add_node("atualizar_historia", atualizar_historia)
grafo.add_node("salvar_historia", salvar_historia)

grafo.set_entry_point("gerar_historia")
grafo.add_edge("gerar_historia", END)
grafo.add_edge("atualizar_historia", END)
grafo.add_edge("salvar_historia", END)

app = grafo.compile(checkpointer=memoria)
