"""Testes de integração: cada caso roda em uma cópia temporária do laboratório."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from cryptography.fernet import Fernet


PROJECT = Path(__file__).resolve().parents[1]


class LaboratoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dio_criptografia_")
        self.root = Path(self.temp.name).resolve()
        if self.root.parent != Path(tempfile.gettempdir()).resolve():
            raise RuntimeError("Pasta temporaria fora do destino esperado.")
        self.addCleanup(self.temp.cleanup)
        self.project = self.root / "projeto"
        self.project.mkdir()
        for name in ("encrypter.py", "decrypter.py", "lab_utils.py"):
            shutil.copyfile(PROJECT / name, self.project / name)
        self.original = self.project / "laboratorio" / "original" / "exemplo.txt"
        self.original.parent.mkdir(parents=True)
        shutil.copyfile(PROJECT / "laboratorio" / "original" / "exemplo.txt", self.original)
        self.expected = self.original.read_bytes()
        self.outputs = self.project / "laboratorio" / "gerados"
        self.external = self.root / "externo"
        self.external.mkdir()
        self.sentinel = self.external / "pessoal.txt"
        self.sentinel.write_bytes(b"Arquivo externo que deve permanecer intacto.")

    def run_script(self, name, *arguments):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        return subprocess.run(
            [sys.executable, str(self.project / name), *arguments],
            cwd=self.external, env=environment, capture_output=True,
            text=True, encoding="utf-8", timeout=10, check=False,
        )

    def encrypt(self):
        response = self.run_script("encrypter.py")
        self.assertEqual(response.returncode, 0, response.stderr)
        return response

    def test_round_trip_preserva_original_e_recupera_conteudo(self):
        self.encrypt()
        self.assertNotEqual((self.outputs / "exemplo.txt.fernet").read_bytes(), self.expected)
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 0, response.stderr)
        self.assertEqual((self.outputs / "exemplo.recuperado.txt").read_bytes(), self.expected)
        self.assertEqual(self.original.read_bytes(), self.expected)

    def test_quebras_de_linha_do_windows_sao_preservadas(self):
        windows_content = self.expected.replace(b"\n", b"\r\n")
        self.original.write_bytes(windows_content)
        self.encrypt()
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 0, response.stderr)
        self.assertEqual((self.outputs / "exemplo.recuperado.txt").read_bytes(), windows_content)
        self.assertEqual(self.original.read_bytes(), windows_content)

    def test_repeticao_da_criptografia_nao_sobrescreve(self):
        self.encrypt()
        previous = {path.name: path.read_bytes() for path in self.outputs.iterdir()}
        response = self.run_script("encrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertIn("Nada foi sobrescrito", response.stderr)
        self.assertEqual({path.name: path.read_bytes() for path in self.outputs.iterdir()}, previous)

    def test_chave_incorreta_nao_produz_copia(self):
        self.encrypt()
        (self.outputs / "chave-demo.key").write_bytes(Fernet.generate_key())
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertIn("Chave incorreta", response.stderr)
        self.assertFalse((self.outputs / "exemplo.recuperado.txt").exists())
        self.assertEqual(self.original.read_bytes(), self.expected)

    def test_token_alterado_nao_produz_copia(self):
        self.encrypt()
        encrypted = self.outputs / "exemplo.txt.fernet"
        token = bytearray(encrypted.read_bytes())
        token[len(token) // 2] ^= 1
        encrypted.write_bytes(token)
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertFalse((self.outputs / "exemplo.recuperado.txt").exists())
        self.assertEqual(self.original.read_bytes(), self.expected)

    def test_arquivo_original_editado_e_recusado(self):
        changed = b"Conteudo diferente do exemplo ficticio."
        self.original.write_bytes(changed)
        response = self.run_script("encrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertIn("exemplo foi alterado", response.stderr)
        self.assertFalse(self.outputs.exists())
        self.assertEqual(self.original.read_bytes(), changed)

    def test_arquivo_grande_e_recusado(self):
        self.original.write_bytes(b"x" * 4097)
        response = self.run_script("encrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertIn("maior que o limite", response.stderr)
        self.assertFalse(self.outputs.exists())

    def test_copia_recuperada_existente_nao_e_sobrescrita(self):
        self.encrypt()
        recovered = self.outputs / "exemplo.recuperado.txt"
        recovered.write_bytes(b"Arquivo existente de teste.")
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertEqual(recovered.read_bytes(), b"Arquivo existente de teste.")

    def test_descriptografia_antes_da_criptografia_informa_erro(self):
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 1)
        self.assertIn("Execute primeiro", response.stderr)
        self.assertFalse(self.outputs.exists())

    def test_diretorio_atual_e_arquivos_externos_permanecem_intactos(self):
        sentinel = self.sentinel.read_bytes()
        self.encrypt()
        response = self.run_script("decrypter.py")
        self.assertEqual(response.returncode, 0, response.stderr)
        self.assertEqual(self.sentinel.read_bytes(), sentinel)
        self.assertEqual({path.name for path in self.external.iterdir()}, {"pessoal.txt"})

    def test_cli_recusa_caminho_arbitrario_e_nao_exibe_chave(self):
        response = self.run_script("encrypter.py", str(self.sentinel))
        self.assertEqual(response.returncode, 2)
        self.assertFalse(self.outputs.exists())
        success = self.encrypt()
        key = (self.outputs / "chave-demo.key").read_text()
        self.assertNotIn(key, success.stdout + success.stderr)


if __name__ == "__main__":
    unittest.main()
