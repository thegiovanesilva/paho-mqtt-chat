.PHONY: build clean install test

# Instala dependências
install:
	pip install -e ".[dev]"

# Instala apenas dependências básicas
install-prod:
	pip install -e .

# Builda o binário
build: install
	pyinstaller mqtt-chat.spec

# Testa o binário
test-binary:
	@echo "Testando binário..."
	@if [ -f dist/mqtt-chat ]; then \
		file dist/mqtt-chat; \
		echo "Binário criado com sucesso!"; \
	else \
		echo "Erro: Binário não encontrado!"; \
		exit 1; \
	fi

# Limpa arquivos de build
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf __pycache__/
	rm -f *.spec~

# Build completo (limpa, builda e testa)
all: clean build test-binary

# Executa o binário (para teste local)
run-binary:
	./dist/mqtt-chat

# Mostra informações do binário
info:
	@if [ -f dist/mqtt-chat ]; then \
		echo "=== Informações do Binário ==="; \
		file dist/mqtt-chat; \
		ls -lh dist/mqtt-chat; \
		echo ""; \
		echo "Para executar: ./dist/mqtt-chat"; \
	else \
		echo "Binário não encontrado. Execute 'make build' primeiro."; \
	fi
