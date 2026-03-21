import json
import re


def _coletar_lista(prompt: str) -> list[str]:
    """Lê itens separados por vírgula ou ponto-e-vírgula."""
    raw = input(prompt).strip()
    return [item.strip() for item in re.split(r"[,;]", raw) if item.strip()]


def coletar_entrada_interativa() -> dict:
    print("\n=== Gerador de Histórias ConnectAI ===\n")
    empresa = input("Empresa: ").strip()
    setor = input("Setor: ").strip()
    cargo = input("Cargo do protagonista: ").strip()
    dificuldade = ""
    while dificuldade not in ("baixa", "média", "alta"):
        dificuldade = input("Dificuldade [baixa / média / alta]: ").strip().lower()
    sintomas = _coletar_lista("Sintomas (separe por vírgula): ")
    principal = input("Causa raiz principal: ").strip()
    secundarias = _coletar_lista("Causas secundárias (separe por vírgula): ")
    return {
        "empresa": empresa,
        "setor": setor,
        "cargo": cargo,
        "dificuldade": dificuldade,
        "sintomas": sintomas,
        "causas_raiz": {"principal": principal, "secundarias": secundarias},
    }


def coletar_entrada_arquivo(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)
