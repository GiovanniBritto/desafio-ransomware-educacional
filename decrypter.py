"""Recupera uma cópia do exemplo e verifica sua correspondência com o original."""

import argparse
import sys

from lab_utils import LabError, PROJECT_DIR, decrypt_demo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descriptografa o exemplo do laboratorio em um novo arquivo."
    )
    parser.parse_args()
    try:
        recovered_path, digest = decrypt_demo()
    except (LabError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print("Descriptografia do exemplo concluida.")
    print(f"Copia recuperada: {recovered_path.relative_to(PROJECT_DIR).as_posix()}")
    print(f"SHA-256 do original e da copia recuperada: {digest}")
    print("Verificacao: conteudos identicos; arquivo original preservado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
