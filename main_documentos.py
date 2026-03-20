import argparse
import sys

from src.agente_documentos.grafo import app2


def main():
    parser = argparse.ArgumentParser(
        description="Agente Gerador de Documentos ConnectAI"
    )
    parser.add_argument(
        "arquivo_md",
        metavar="ARQUIVO.md",
        help="Caminho para o .md gerado pelo agente de histórias",
    )
    args = parser.parse_args()

    estado_inicial = {
        "caminho_md": args.arquivo_md,
        "caso": "",
        "dificuldade": "",
        "historia": "",
        "documentos_tabela": [],
        "documentos_json": [],
        "indice_atual": 0,
    }

    print(f"Processando: {args.arquivo_md}")
    app2.invoke(estado_inicial)


if __name__ == "__main__":
    main()
