import subprocess
import sys


def test_main_cli_execution():
    """Valida que src/main.py executa de ponta a ponta de forma sincrona retornando exit code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        capture_output=True,
        text=True,
        env={"HEADLESS": "true", "BROWSER_CHANNEL": "chromium", "SESSION_ROOT_DIR": "./tests_scratch/cli_sessions"},
    )
    assert result.returncode == 0
    assert "AIHawk v0.1 - Inicializando Infraestrutura Stealth (Sync)" in result.stdout
    assert "Sessao encerrada com sucesso." in result.stdout
