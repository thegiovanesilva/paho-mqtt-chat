================================================================================
                    PAHO MQTT CHAT - APLICATIVO DE CHAT
================================================================================

IDENTIFICAÇÃO DOS AUTORES:
- Giovane Gonçalves da Silva
- Igor Andrey Ronsoni

================================================================================
REQUISITOS DO SISTEMA:
================================================================================

1. Python 3.7 ou superior instalado
2. Bibliotecas Python necessárias:
   - paho-mqtt

================================================================================
INSTALAÇÃO DAS DEPENDÊNCIAS:
================================================================================

Execute o comando abaixo para instalar a biblioteca necessária:

    pip install paho-mqtt

Ou, se estiver usando Python 3:

    pip3 install paho-mqtt

================================================================================
ESTRUTURA DE ARQUIVOS:
================================================================================

main.py                - Arquivo principal da aplicação
README.md              - Este arquivo de documentação
================================================================================
CONFIGURAÇÃO:
================================================================================

Antes de executar, certifique-se de que:

1. Um servidor MQTT está rodando em 127.0.0.1:1883
   (Padrão: localhost na porta 1883)

2. Se usar um broker diferente, edite as constantes em main.py:
   - BROKER = "127.0.0.1"
   - PORT = 1883

================================================================================
COMO EXECUTAR:
================================================================================

No terminal/prompt de comando, navegue até o diretório do projeto e execute:

    python main.py

Ou, se estiver usando Python 3 explicitamente:

    python3 main.py

Você será solicitado a digitar seu ID de usuário:

    Digite seu ID: <seu_nome_ou_id>

================================================================================
FUNCIONALIDADES PRINCIPAIS:
================================================================================

Menu Interativo:
1. Listar usuários (online/offline)
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
13. Mostrar histórico para debug (rastreia solicitações e aceitações de chat)
0. Sair

================================================================================
FUNCIONALIDADES DE DEPURAÇÃO:
================================================================================

Histórico de Atividades:
- Menu opção 13 lista o histórico completo de:
  ✓ Solicitações de conversa recebidas
  ✓ Solicitações aceitas
  ✓ Tópicos de chat criados
  ✓ Atividades de grupos
  ✓ Timestamps de todas as operações

================================================================================
EXEMPLO DE USO:
================================================================================

1. Abra 2 terminais e execute o aplicativo em cada um
2. Digite IDs diferentes (ex: usuario1, usuario2)
3. No terminal do usuario1, escolha opção 2 para solicitar conversa
4. No terminal do usuario2, escolha opção 7 para responder notificações
5. Aceite a solicitação para iniciar o chat
6. Agora ambos podem trocar mensagens

================================================================================
REQUISITOS FUNCIONAIS IMPLEMENTADOS:
================================================================================

✓ Solicitação de conversa (one-to-one)
✓ Listagem de histórico de solicitações recebidas
✓ Listagem de confirmações de aceite de chat
✓ Exibição do tópico criado para iniciar bate-papo
✓ Criação e gerenciamento de grupos
✓ Mensagens privadas e em grupo
✓ Controle de membros e liderança de grupos

================================================================================
RESOLUÇÃO DE PROBLEMAS:
================================================================================

Erro: "ModuleNotFoundError: No module named 'paho'"
Solução: Execute "pip install paho-mqtt"

Erro: "Conexão recusada"
Solução: Verifique se o servidor MQTT está rodando em 127.0.0.1:1883

Erro: "Nenhum usuário encontrado"
Solução: Aguarde alguns segundos para as mensagens retained do broker
         ou verifique se outros usuários estão conectados

================================================================================
NOTAS:
================================================================================

- O aplicativo usa MQTT com QoS 2 para garantir entrega de mensagens
- As mensagens retained ajudam a manter o estado dos usuários
- O histórico é armazenado em memória durante a execução
- Feche com a opção 0 para desconectar corretamente

================================================================================
