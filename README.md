 # PAHO MQTT CHAT

Aplicativo de chat simples usando MQTT (biblioteca paho-mqtt).

Este repositório contém uma implementação de exemplo de chat baseado em tópicos MQTT, com suporte a conversas one-to-one e grupos.

## Autores

- Giovane Gonçalves da Silva
- Igor Andrey Ronsoni

## Requisitos

- Python 3.9 ou superior
- Biblioteca Python: `paho-mqtt`

Instale a dependência com:

```shell
pip install paho-mqtt
```

ou

```shell
pip3 install paho-mqtt
```

## Estrutura do projeto

- `main.py` — arquivo principal da aplicação
- `README.md` — documentação (este arquivo)

## Configuração

Por padrão o cliente tenta conectar ao broker MQTT em `127.0.0.1:1883`.
Se você usar outro broker/host/porta, ajuste as constantes/variáveis em `main.py` (por exemplo `BROKER` e `PORT`).

## Como executar

1. Abra um terminal no diretório do projeto.
2. Execute:

```shell
python main.py
```

ou

```shell
python3 main.py
```

3. Ao iniciar, o programa solicitará um ID de usuário:

```
Digite seu ID: <seu_nome_ou_id>
```

Repita em terminais diferentes para simular múltiplos usuários.

## Funcionalidades principais

- Listar usuários (online/offline)
- Solicitação de conversa (one-to-one)
- Criação e gerenciamento de grupos
- Envio de mensagens privadas e em grupo
- Listagem de histórico de eventos para debug

Menu (exemplos de opções):

1. Listar usuários
2. Solicitar conversa (one-to-one)
3. Criar grupo
4. Listar grupos
5. Entrar em grupo
6. Enviar mensagem
7. Responder notificações
8. Listar grupos que participo
9. Listar minhas conversas
10. Convidar para grupo
11. Sair de grupo
12. Remover grupo
13. Mostrar histórico para debug
0. Sair

## Exemplo rápido

1. Abra dois terminais e execute `python main.py` em cada um.
2. Use IDs diferentes (por exemplo `usuario1` e `usuario2`).
3. Em `usuario1`, solicite uma conversa com a opção correspondente.
4. Em `usuario2`, responda a notificação e aceite a conversa.
5. Ambos poderão trocar mensagens.


## Notas

- O aplicativo usa QoS adequado para garantir a entrega conforme implementado em `main.py`.
- O histórico é mantido em memória durante a execução do programa.
