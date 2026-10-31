# Atalhos do AIHawk (equivalente ao "npm run"). Uso: make <alvo>
PY := .venv/bin/python

.PHONY: test pre-pr demo

# Rapido, sem navegador: dominio + aplicacao (uso diario)
test:
	$(PY) -m pytest tests/domain tests/application -q

# Antes de abrir/atualizar PR: testes reais (Chromium) + borda + suite completa
pre-pr:
	HEADLESS=true $(PY) -m pytest tests/real/ tests/infrastructure/ -v
	HEADLESS=true $(PY) -m pytest -q

# Demo visual: abre a janela do Chromium e roda o robo no servidor local de armadilhas
demo:
	$(PY) scripts/demo_visual.py
