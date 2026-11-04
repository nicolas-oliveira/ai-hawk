"""
Testes automatizados da lógica de validação da Catraca de Mutação do CI (.github/workflows/ci.yml).
Prova que o gate do CI falha estritamente abaixo do piso (score < 99.0%), acima do teto (survived > 3),
ou com total de mutantes insuficiente (< 500), e aprova no patamar homologado (teto 3, score >= 99.0%).
"""
import sqlite3
import subprocess
import sys
from pathlib import Path

CI_SCRIPT = """
import sqlite3, sys
con = sqlite3.connect('{db_path}')
cur = con.cursor()
counts = dict(cur.execute('SELECT status, count(*) FROM mutant GROUP BY status').fetchall())
killed = counts.get('ok_killed', 0)
survived = counts.get('bad_survived', 0)
total = killed + survived
score = (killed / total * 100) if total > 0 else 0
print(f'Catraca Mutation: {{killed}}/{{total}} mortos ({{score:.1f}}%), {{survived}} sobreviventes')
if total < 500:
    print(f'ERRO: Menos mutantes testados do que o esperado ({{total}} < 500)!')
    sys.exit(1)
if survived > 3:
    print(f'ERRO: Catraca violada! {{survived}} sobreviventes > teto de 3.')
    sys.exit(1)
if score < 99.0:
    print(f'ERRO: Score {{score:.1f}}% abaixo do piso homologado de 99.0%!')
    sys.exit(1)
"""


def _create_mock_cache(db_path: Path, killed: int, survived: int) -> None:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("CREATE TABLE mutant (id INTEGER PRIMARY KEY, status TEXT);")
    for _ in range(killed):
        cur.execute("INSERT INTO mutant (status) VALUES ('ok_killed');")
    for _ in range(survived):
        cur.execute("INSERT INTO mutant (status) VALUES ('bad_survived');")
    conn.commit()
    conn.close()


def _run_ci_gate(db_path: Path) -> subprocess.CompletedProcess:
    code = CI_SCRIPT.format(db_path=str(db_path).replace("\\", "/"))
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )


def test_ci_catraca_accepts_homologated_baseline(tmp_path):
    """Cenário homologado pós-C4 ('e54568b'): 737 mortos, 3 sobreviventes (score 99.6%, total 740)."""
    db_path = tmp_path / ".mutmut-cache"
    _create_mock_cache(db_path, killed=737, survived=3)
    res = _run_ci_gate(db_path)
    assert res.returncode == 0
    assert "Catraca Mutation: 737/740 mortos (99.6%), 3 sobreviventes" in res.stdout


def test_ci_catraca_accepts_further_improvement(tmp_path):
    """Cenário de evolução futura: 738 mortos, 2 sobreviventes (score 99.7%)."""
    db_path = tmp_path / ".mutmut-cache"
    _create_mock_cache(db_path, killed=738, survived=2)
    res = _run_ci_gate(db_path)
    assert res.returncode == 0


def test_ci_catraca_fails_when_survivors_exceed_ceiling(tmp_path):
    """Cenário de violação de teto: 4 sobreviventes (> 3). Deve reprovar no CI."""
    db_path = tmp_path / ".mutmut-cache"
    _create_mock_cache(db_path, killed=736, survived=4)
    res = _run_ci_gate(db_path)
    assert res.returncode == 1
    assert "ERRO: Catraca violada! 4 sobreviventes > teto de 3." in res.stdout


def test_ci_catraca_fails_when_score_below_floor_99(tmp_path):
    """Cenário de violação de piso: score 98.8% (< 99.0%), mesmo com total alto."""
    db_path = tmp_path / ".mutmut-cache"
    # 500 mortos, 6 sobreviventes = 98.8%
    _create_mock_cache(db_path, killed=500, survived=6)
    res = _run_ci_gate(db_path)
    assert res.returncode == 1
    assert "Catraca violada" in res.stdout or "abaixo do piso" in res.stdout


def test_ci_catraca_fails_when_total_mutants_insufficient(tmp_path):
    """Cenário de quebra de escopo: menos de 500 mutantes avaliados. Deve reprovar."""
    db_path = tmp_path / ".mutmut-cache"
    _create_mock_cache(db_path, killed=400, survived=2)
    res = _run_ci_gate(db_path)
    assert res.returncode == 1
    assert "ERRO: Menos mutantes testados do que o esperado (402 < 500)!" in res.stdout
