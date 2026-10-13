"""Criptografa somente o arquivo fictício fixo deste projeto, preservando-o."""

import argparse
import sys

from lab_utils import LabError, PROJECT_DIR, encrypt_demo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cria uma copia criptografada do exemplo ficticio fixo do laboratorio."
    )
    parser.parse_args()
    try:
        key_path, encrypted_path = encrypt_demo()
    except (LabError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print("Criptografia do exemplo concluida.")
    print(f"Copia criptografada: {encrypted_path.relative_to(PROJECT_DIR).as_posix()}")
    print(f"Chave local: {key_path.relative_to(PROJECT_DIR).as_posix()} (conteudo nao exibido)")
    print("Original preservado: laboratorio/original/exemplo.txt")
    print("Proximo passo: python decrypter.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
