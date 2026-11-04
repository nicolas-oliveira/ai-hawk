#!/usr/bin/env python3
"""Le o Turno e o STATUS do topo do NOTAS.md do ULTIMO COMMIT (HEAD).

Uso:  ler_topo.py turno [pasta-do-projeto]   -> imprime claude | agy | nicolas | ... (minusculo)
      ler_topo.py status [pasta-do-projeto]  -> imprime o texto do STATUS
Imprime vazio se nao achar. Usado pelo hook commit-msg e pelo maestro (magc),
para os dois lerem o topo do mesmo jeito.

Tolerante a variacoes de escrita:
  **DE/PARA/TURNO:** Claude -> Agy | Turno: Agy | data
  **TURNO:** Claude (...)      TURNO: CLAUDE      DE: Agy | ... | TURNO: Claude (...)
Regra: dentro do bloco do comunicado, a primeira linha que tem "turno:" (qualquer
caixa, com ou sem **); vale o ULTIMO valor dessa linha.
"""
import re
import subprocess
import sys


def bloco_do_topo(texto):
    linhas = texto.splitlines()
    ini = next((i for i, l in enumerate(linhas) if "COMUNICADO" in l.upper()), -1)
    bloco = []
    for l in linhas[ini + 1:ini + 31]:
        if l.strip() == "---" and any(x.strip() for x in bloco):
            break
        bloco.append(l)
    return bloco


def ler_turno(texto):
    for l in bloco_do_topo(texto):
        achados = re.findall(r"turno:\**\s*([A-Za-z]+)", l, re.I)
        if achados:
            return achados[-1].lower()
    return ""


def ler_status(texto):
    for l in bloco_do_topo(texto):
        m = re.search(r"status:\**\s*(.*)", l, re.I)
        if m:
            return m.group(1).strip()
    return ""


def notas_do_head(pasta="."):
    try:
        return subprocess.check_output(
            ["git", "-C", pasta, "show", "HEAD:NOTAS.md"], text=True, stderr=subprocess.DEVNULL
        )
    except Exception:
        return ""


if __name__ == "__main__":
    campo = sys.argv[1] if len(sys.argv) > 1 else "turno"
    texto = notas_do_head(sys.argv[2] if len(sys.argv) > 2 else ".")
    print(ler_status(texto) if campo == "status" else ler_turno(texto))
