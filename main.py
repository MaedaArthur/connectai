import argparse

from src.entrada import coletar_entrada_arquivo, coletar_entrada_interativa
from src.grafo import app
from src.nos import atualizar_historia, salvar_historia


def main():
    parser = argparse.ArgumentParser(description="Gerador de histórias ConnectAI")
    parser.add_argument(
        "--arquivo", "-a",
        metavar="ARQUIVO.json",
        help="JSON com os campos de entrada. Se omitido, os dados são coletados interativamente.",
    )
    args = parser.parse_args()

    entrada = (
        coletar_entrada_arquivo(args.arquivo)
        if args.arquivo
        else coletar_entrada_interativa()
    )

    config = {"configurable": {"thread_id": "sessao_1"}}

    estado = app.invoke(
        {"entrada": entrada, "historia": "", "historico": [], "feedback": ""},
        config=config,
    )
    print(estado["historia"])

    while True:
        print("\n[f] feedback  |  [s] salvar  |  [q] sair")
        comando = input("> ").strip().lower()

        if comando == "q":
            break
        elif comando == "s":
            salvar_historia(estado)
            break
        elif comando == "f":
            feedback = input("Feedback: ").strip()
            estado = atualizar_historia({**estado, "feedback": feedback})
            print("\n" + estado["historia"])
        else:
            print("Comando inválido.")


if __name__ == "__main__":
    main()
