import os
import subprocess
import sys
import tempfile
import pytest

SCRIPTS_HOOKS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "hooks")
)


def test_ler_topo_reading_turno_and_status():
    sys.path.insert(0, SCRIPTS_HOOKS_DIR)
    from ler_topo import ler_turno, ler_status

    sample_notas = """## COMUNICADO DA SQUAD
**DE/PARA/TURNO:** Claude -> Agy | Turno: Agy | 2026-11-04
**STATUS:** Suíte verde, aguardando validação
**ACEITE/RESUMO:** Testes unitários prontos

---
Texto da carta...
"""
    assert ler_turno(sample_notas) == "agy"
    assert ler_status(sample_notas) == "Suíte verde, aguardando validação"


def test_ler_topo_tolerates_variations():
    sys.path.insert(0, SCRIPTS_HOOKS_DIR)
    from ler_topo import ler_turno

    sample_claude = """## COMUNICADO DA SQUAD
**DE/PARA/TURNO:** Agy -> Claude | Turno: Claude
---
"""
    assert ler_turno(sample_claude) == "claude"

    sample_nicolas = """## COMUNICADO DA SQUAD
Turno: Nicolas
---
"""
    assert ler_turno(sample_nicolas) == "nicolas"


def test_commit_msg_enforces_agent_turn(tmp_path):
    commit_msg_script = os.path.join(SCRIPTS_HOOKS_DIR, "commit-msg")

    # Caso 1: Commit de Nicolas (sem prefixo de agente) passa sempre
    msg_file = tmp_path / "msg1.txt"
    msg_file.write_text("Correção manual de infraestrutura\n", encoding="utf-8")
    res = subprocess.run([sys.executable, commit_msg_script, str(msg_file)], capture_output=True, text=True)
    assert res.returncode == 0

    # Cria repo de teste para validar o comportamento real do git com NOTAS.md no HEAD
    test_repo = tmp_path / "test_repo"
    test_repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(test_repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(test_repo), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(test_repo), check=True)

    notas_content = """## COMUNICADO DA SQUAD
**DE/PARA/TURNO:** Claude -> Agy | Turno: Agy | 2026-11-04
**STATUS:** Em andamento
**ACEITE/RESUMO:** Ok
---
"""
    (test_repo / "NOTAS.md").write_text(notas_content, encoding="utf-8")
    subprocess.run(["git", "add", "NOTAS.md"], cwd=str(test_repo), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(test_repo), check=True)

    # Copia os hooks para o test_repo para que ler_topo fique acessivel
    repo_hooks = test_repo / ".git" / "hooks"
    (repo_hooks / "ler_topo.py").write_text((tmp_path / "fake_ler_topo.py").name if False else (open(os.path.join(SCRIPTS_HOOKS_DIR, "ler_topo.py")).read()), encoding="utf-8")
    (repo_hooks / "commit-msg").write_text(open(os.path.join(SCRIPTS_HOOKS_DIR, "commit-msg")).read(), encoding="utf-8")
    test_commit_msg = str(repo_hooks / "commit-msg")

    # Caso 2: [Agy] quando turno e agy -> passa
    msg_agy = test_repo / "msg_agy.txt"
    msg_agy.write_text("[Agy] Implementa trava de seguranca\n", encoding="utf-8")
    res_agy = subprocess.run(
        [sys.executable, test_commit_msg, str(msg_agy)],
        cwd=str(test_repo),
        capture_output=True,
        text=True
    )
    assert res_agy.returncode == 0

    # Caso 3: [Claude] quando turno e agy -> recusa
    msg_claude = test_repo / "msg_claude.txt"
    msg_claude.write_text("[Claude] Atualiza regras de dominio\n", encoding="utf-8")
    res_claude = subprocess.run(
        [sys.executable, test_commit_msg, str(msg_claude)],
        cwd=str(test_repo),
        capture_output=True,
        text=True
    )
    assert res_claude.returncode == 1
    assert "COMMIT RECUSADO" in res_claude.stderr


def test_pre_push_blocks_master_and_main():
    pre_push_script = os.path.join(SCRIPTS_HOOKS_DIR, "pre-push")

    # Push para master deve ser recusado
    proc_master = subprocess.run(
        [sys.executable, pre_push_script],
        input="refs/heads/feat/2.0-portao-a sha1 refs/heads/master sha2\n",
        capture_output=True,
        text=True
    )
    assert proc_master.returncode == 1
    assert "PUSH RECUSADO" in proc_master.stderr
    assert "master" in proc_master.stderr

    # Push para main deve ser recusado
    proc_main = subprocess.run(
        [sys.executable, pre_push_script],
        input="refs/heads/feat/2.0-portao-a sha1 refs/heads/main sha2\n",
        capture_output=True,
        text=True
    )
    assert proc_main.returncode == 1
    assert "PUSH RECUSADO" in proc_main.stderr

    # Push para feat/* deve ser permitido
    proc_feat = subprocess.run(
        [sys.executable, pre_push_script],
        input="refs/heads/feat/2.0-portao-a sha1 refs/heads/feat/2.0-portao-a sha2\n",
        capture_output=True,
        text=True
    )
    assert proc_feat.returncode == 0

    # Push de tag deve ser permitido
    proc_tag = subprocess.run(
        [sys.executable, pre_push_script],
        input="refs/tags/v1.6 sha1 refs/tags/v1.6 sha2\n",
        capture_output=True,
        text=True
    )
    assert proc_tag.returncode == 0


def test_pre_commit_prunes_history_over_ceiling(tmp_path):
    pre_commit_script = os.path.join(SCRIPTS_HOOKS_DIR, "pre-commit")

    header = """## COMUNICADO DA SQUAD
**DE/PARA/TURNO:** Claude -> Agy | Turno: Agy | 2026-11-04
**STATUS:** Em andamento
**ACEITE/RESUMO:** Ok

---
Carta da squad...

## 4. Historico de Entregas e Sessoes

"""
    entries = "\n".join(f"* [2026-11-0{i%9+1}] Entrada {i}: descricao detalhada" for i in range(20))
    full_text = header + entries + "\n"

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir), check=True)

    notas_file = repo_dir / "NOTAS.md"
    notas_file.write_text(full_text, encoding="utf-8")
    subprocess.run(["git", "add", "NOTAS.md"], cwd=str(repo_dir), check=True)

    # Executa o pre-commit
    res = subprocess.run(
        [sys.executable, pre_commit_script],
        cwd=str(repo_dir),
        capture_output=True,
        text=True
    )
    assert res.returncode == 0

    new_content = notas_file.read_text(encoding="utf-8")
    assert new_content.startswith(header)
    remaining_entries = [l for l in new_content.splitlines() if l.startswith("* [")]
    assert len(remaining_entries) == 10
