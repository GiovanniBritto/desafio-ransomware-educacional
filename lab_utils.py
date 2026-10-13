"""Operações limitadas ao exemplo fictício que acompanha este laboratório."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

from cryptography.fernet import Fernet, InvalidToken


PROJECT_DIR = Path(__file__).resolve().parent
LAB_DIR = PROJECT_DIR / "laboratorio"
ORIGINAL_DIR = LAB_DIR / "original"
ORIGINAL_FILE = ORIGINAL_DIR / "exemplo.txt"
OUTPUT_DIR = LAB_DIR / "gerados"
KEY_NAME = "chave-demo.key"
ENCRYPTED_NAME = "exemplo.txt.fernet"
RECOVERED_NAME = "exemplo.recuperado.txt"
ALLOWED_OUTPUTS = frozenset({KEY_NAME, ENCRYPTED_NAME, RECOVERED_NAME})
MAX_SAMPLE_BYTES = 4096
MAX_TOKEN_BYTES = 8192
EXPECTED_SAMPLE = (
    "LABORATORIO EDUCACIONAL DIO\n"
    "Este arquivo contem somente dados ficticios para estudar criptografia.\n"
    "O original deve permanecer intacto durante toda a demonstracao.\n"
).encode("utf-8")


class LabError(RuntimeError):
    """Erro esperado do cenário de treinamento."""


def _reject_redirect(path: Path) -> None:
    if path.is_symlink():
        raise LabError("O laboratorio recusa links simbolicos.")
    if path.exists():
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise LabError("O laboratorio recusa diretorios ou arquivos redirecionados.")


def _check_lab() -> None:
    for directory in (LAB_DIR, ORIGINAL_DIR):
        _reject_redirect(directory)
        if not directory.is_dir():
            raise LabError("A pasta laboratorio/original do projeto esta ausente.")
        if not directory.resolve().is_relative_to(PROJECT_DIR):
            raise LabError("Caminho fora da pasta do projeto.")


def _read_limited(path: Path, limit: int) -> bytes:
    _reject_redirect(path)
    if not path.is_file():
        raise LabError(f"Arquivo necessario ausente: {path.name}.")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise LabError("Arquivo maior que o limite deste laboratorio.")
    return data


def read_sample() -> bytes:
    _check_lab()
    content = _read_limited(ORIGINAL_FILE, MAX_SAMPLE_BYTES)
    if content.replace(b"\r\n", b"\n") != EXPECTED_SAMPLE:
        raise LabError("O arquivo de exemplo foi alterado. Use o exemplo ficticio original do pacote.")
    return content


def _output_path(name: str, *, create_directory: bool = False) -> Path:
    if name not in ALLOWED_OUTPUTS:
        raise LabError("Nome de saida fora do cenario permitido.")
    _check_lab()
    _reject_redirect(OUTPUT_DIR)
    if create_directory:
        OUTPUT_DIR.mkdir(exist_ok=True)
    if not OUTPUT_DIR.is_dir():
        raise LabError("Execute primeiro encrypter.py para gerar o exemplo criptografado.")
    _reject_redirect(OUTPUT_DIR)
    if OUTPUT_DIR.resolve() != LAB_DIR.resolve() / "gerados":
        raise LabError("Pasta de saida fora do laboratorio.")
    target = OUTPUT_DIR / name
    _reject_redirect(target)
    return target


def _write_new(name: str, content: bytes) -> Path:
    path = _output_path(name)
    # O_CREAT + O_EXCL recusa um destino existente, inclusive em uma repetição.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(content)
    return path


def encrypt_demo() -> tuple[Path, Path]:
    sample = read_sample()
    key_path = _output_path(KEY_NAME, create_directory=True)
    encrypted_path = _output_path(ENCRYPTED_NAME)
    if key_path.exists() or encrypted_path.exists():
        raise LabError("Ja existem arquivos gerados. Nada foi sobrescrito. Para repetir, use uma nova copia do projeto.")
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(sample)
    # O original e aberto somente para leitura e permanece na pasta original/.
    _write_new(KEY_NAME, key)
    _write_new(ENCRYPTED_NAME, token)
    return key_path, encrypted_path


def decrypt_demo() -> tuple[Path, str]:
    sample = read_sample()
    key_path = _output_path(KEY_NAME)
    encrypted_path = _output_path(ENCRYPTED_NAME)
    recovered_path = _output_path(RECOVERED_NAME)
    if recovered_path.exists():
        raise LabError("A copia recuperada ja existe. Nada foi sobrescrito.")
    key = _read_limited(key_path, 128)
    token = _read_limited(encrypted_path, MAX_TOKEN_BYTES)
    try:
        plaintext = Fernet(key).decrypt(token)
    except (InvalidToken, ValueError) as error:
        raise LabError("Chave incorreta ou arquivo criptografado invalido/alterado. Nenhuma copia foi gravada.") from error
    if plaintext != sample:
        raise LabError("O conteudo recuperado nao corresponde ao exemplo ficticio esperado.")
    recovered_path = _write_new(RECOVERED_NAME, plaintext)
    return recovered_path, hashlib.sha256(plaintext).hexdigest()
