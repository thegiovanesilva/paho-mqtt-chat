# MQTT Chat

Um chat de texto usando paho-mqtt.

## Executando o programa

### Pré-requisitos
- Python 3.13+
- Poetry
- Broker MQTT rodando em `127.0.0.1:1883`

### Instalação e execução
```bash
poetry install
poetry run python main.py
```

## Build do binário

### Usando GitHub Actions
O projeto possui um workflow do GitHub Actions que automaticamente builda um binário do Linux sempre que há push para a branch `main` ou quando uma tag é criada.

**Para releases:**
1. Crie uma tag: `git tag v1.0.0`
2. Faça push da tag: `git push origin v1.0.0`
3. O GitHub Actions criará automaticamente uma release com o binário

**Para desenvolvimento:**
- Qualquer push para `main` gerará um artefato que pode ser baixado da aba Actions

### Build local

#### Usando Makefile (recomendado)
```bash
# Build completo (instala dependências, builda e testa)
make all

# Apenas build
make build

# Informações do binário
make info

# Executar o binário
make run-binary

# Limpar arquivos de build
make clean
```

#### Usando Poetry diretamente
```bash
# Instalar dependências
poetry install --with dev

# Buildar
poetry run pyinstaller mqtt-chat.spec

# O binário estará em dist/mqtt-chat
```

## Estrutura do projeto

```
├── main.py              # Código principal
├── mqtt-chat.spec       # Configuração do PyInstaller
├── Makefile            # Comandos de build
├── pyproject.toml      # Configuração do projeto Python
├── *.json              # Arquivos de dados (incluídos no binário)
└── .github/
    └── workflows/
        └── build-linux-binary.yml  # Workflow do GitHub Actions
```

## Como funciona o build

1. **GitHub Actions**: Configura Python 3.13, instala dependências e roda PyInstaller
2. **PyInstaller**: Usa o arquivo `mqtt-chat.spec` para configurar o build
3. **Artefatos**: O binário é disponibilizado como artefato/release
4. **Cache**: Dependencies são cacheadas para builds mais rápidos

O binário resultante:
- É um executável standalone para Linux x64
- Inclui todas as dependências Python
- Inclui arquivos JSON necessários
- Pode ser executado sem Python instalado no sistema alvo