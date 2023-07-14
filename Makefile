.PHONY: .pdm
.pdm:
	@pdm -V || echo 'Please install PDM: https://pdm.fming.dev/latest/\#installation'

.PHONY: .hatch
.hatch:
	@hatch version || echo 'Please install hatch!'

.PHONY: format
format: .pdm
	pdm run isort $(sources)
	pdm run black $(sources)
	pdm run ruff --fix $(sources)

.PHONY: lint
lint: .pdm
	pdm run ruff $(sources)
	pdm run black $(sources) --check --diff

.PHONY: test
test: .pdm
	pdm run coverage run -m pytest $(source) $(args)

.PHONY: testcov
testcov: .pdm test
	pdm run coverage report -m --omit=tests/*

.PHONY: publish
publish: .hatch
	hatch build
	hatch publish
	rm -rf dist
