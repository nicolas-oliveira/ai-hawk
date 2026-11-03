from pathlib import Path


def get_project_root() -> Path:
    """
    Retorna o caminho absoluto da raiz do repositorio do AIHawk,
    independente do diretorio corrente de execucao (os.getcwd()).
    """
    return Path(__file__).resolve().parent.parent.parent
