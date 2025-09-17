import paho.mqtt.client as mqtt
import json
import time
import threading
import queue

BROKER = "127.0.0.1"
PORT = 1883

print("=== MQTT CHAT ===")
USER_ID = input("Digite seu ID: ")

control_queue = queue.Queue()
messages_queue = queue.Queue()
ui_lock = threading.Lock()  # Lock para controlar acesso à interface

# Estruturas em memória (mais simples que arquivos JSON)
active_sessions = {}  # sessões ativas do usuário
my_groups = {}  # grupos que participo
online_users = set()  # usuários online
pending_messages = []  # mensagens que chegaram durante input do usuário

def on_connect(client, userdata, flags, rc, properties):
    print("Conectado ao broker MQTT")
    client.subscribe(f"{USER_ID}_Control")
    client.subscribe("USERS")
    client.subscribe("GROUPS")
    
    restore_session_subscriptions()

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = payload


    if msg.topic == "USERS":
        user = data['user']
        status = data['status']
        if status == "online":
            online_users.add(user)
        else:
            online_users.discard(user)
        print(f"[STATUS] Usuário {user} -> {status}")

    elif msg.topic == "GROUPS":
        # Processa informações de grupo
        if isinstance(data, dict) and 'leader' in data:
            print(f"[GRUPO] Novo grupo criado por {data['leader']}")
        else:
            print(f"[GRUPO] {data}")

    elif msg.topic == f"{USER_ID}_Control":
        handle_control_message(data)

    else:
        # Mensagem de chat recebida via MQTT - adiciona à fila para exibir de forma organizada
        message_info = {
            "topic": msg.topic,
            "content": payload,
            "timestamp": time.time()
        }
        pending_messages.append(message_info)
        
        # Se não estamos no meio de um input, mostra imediatamente
        if ui_lock.acquire(blocking=False):
            try:
                display_pending_messages()
            finally:
                ui_lock.release()


# Funções de controle de interface
def display_pending_messages():
    """Exibe mensagens pendentes de forma organizada"""
    if not pending_messages:
        return
    
    print("\n" + "="*50)
    for msg in pending_messages:
        timestamp = time.strftime("%H:%M:%S", time.localtime(msg['timestamp']))
        print(f"[{timestamp}] 💬 {msg['topic']}: {msg['content']}")
    print("="*50)
    
    # Limpa as mensagens após exibir
    pending_messages.clear()

def safe_input(prompt):
    """Input que não é interrompido por mensagens MQTT"""
    with ui_lock:
        # Mostra mensagens pendentes antes do input
        display_pending_messages()
        return input(prompt)

def restore_session_subscriptions():
    """Restaura inscrições em sessões e grupos (dados em memória)"""
    try:
        session_count = len(active_sessions)
        group_count = len(my_groups)
        
        # Reinscreve em sessões ativas
        for session_topic in active_sessions:
            client.subscribe(session_topic, qos=1)
        
        # Reinscreve em grupos
        for group_name in my_groups:
            client.subscribe(group_name, qos=1)
        
        if session_count > 0 or group_count > 0:
            print(f"[INFO] Restauradas {session_count} sessões e {group_count} grupos")
    except Exception as e:
        print(f"Erro ao restaurar inscrições: {e}")

def handle_control_message(data):
    control_queue.put(data)

def process_control_messages():
    while True:
        try:
            data = control_queue.get(timeout=0.1)
            if data.get("type") == "chat_request":
                print(f"\n[CHAT REQUEST] {data['from']} quer iniciar chat")
                print("Digite 'aceitar' ou 'recusar' na próxima opção do menu.")
                pending_requests[data['from']] = data
            elif data.get("type") == "chat_accept":
                session_topic = data['session']
                print(f"\n[INFO] Solicitação aceita! Sessão: {session_topic}")
                
                # Adiciona à lista de sessões ativas
                active_sessions[session_topic] = {"users": [USER_ID]}  # Não sabemos o outro usuário aqui
                
                client.subscribe(session_topic, qos=1)
                print(f"[INFO] Você agora está inscrito para receber mensagens em: {session_topic} (com garantia)")
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Erro ao processar mensagem de controle: {e}")


def join_session():
    session_topic = safe_input("Digite o tópico da sessão: ")
    client.subscribe(session_topic, qos=1)
    print(f"[INFO] Inscrito no tópico: {session_topic}")
    print("Agora você pode receber mensagens desta sessão (com garantia de entrega)!")
    

pending_requests = {}


def menu():
    while True:
        # Mostra mensagens pendentes antes do menu
        with ui_lock:
            display_pending_messages()
        
        if pending_requests:
            print(f"\n[ATENÇÃO] Você tem {len(pending_requests)} solicitação(ões) de chat pendente(s)!")
            for user in pending_requests.keys():
                print(f"  - {user}")
        
        print("\n--- MENU ---")
        print("1. Listar usuários")
        print("2. Solicitar conversa (one-to-one)")
        print("3. Criar grupo")
        print("4. Listar grupos")
        print("5. Entrar em sessão/grupo")
        print("6. Enviar mensagem")
        print("7. Responder solicitações de chat")
        print("8. Listar grupos que participo")
        print("9. Listar minhas conversas")
        print("10. Sair")
        choice = safe_input("> ")

        if choice == "1":
            list_users()
        elif choice == "2":
            request_chat()
        elif choice == "3":
            create_group()
        elif choice == "4":
            list_groups()
        elif choice == "5":
            join_session()
        elif choice == "6":
            send_message()
        elif choice == "7":
            handle_pending_requests()
        elif choice == "8":
            list_my_groups()
        elif choice == "9":
            list_my_conversations()
        elif choice == "10":
            exit_program()
            break
        
        else:
            print("Opção inválida!")

def list_users():
    print(f"\nUsuários online ({len(online_users)}):")
    if online_users:
        for user in sorted(online_users):
            print(f"  • {user}")
    else:
        print("  Nenhum usuário online no momento.")

def request_chat():
    target = safe_input("Digite o ID do usuário: ")
    client.publish(f"{target}_Control", json.dumps({"type":"chat_request","from":USER_ID}))
    
def create_group():
    group_name = safe_input("Nome do grupo: ")
    if group_name in my_groups:
        print("Você já participa deste grupo!")
        return
    
    # Adiciona aos meus grupos
    my_groups[group_name] = {"leader": USER_ID, "members": [USER_ID]}
    
    # Se inscreve automaticamente no grupo
    client.subscribe(group_name, qos=1)
    
    # Notifica outros usuários sobre o novo grupo
    client.publish("GROUPS", json.dumps({"name": group_name, "leader": USER_ID, "members": [USER_ID]}))
    
    print(f"Grupo {group_name} criado!")
    print(f"[INFO] Você está automaticamente inscrito no grupo: {group_name}")

def list_groups():
    print("Funcionalidade simplificada - use 'Listar meus grupos' para ver seus grupos.")

def list_my_groups():
    """Lista grupos dos quais o usuário participa (dados em memória)"""
    if not my_groups:
        print("Você não participa de nenhum grupo.")
        return
    
    print(f"\n👥 Seus grupos ({len(my_groups)}):")
    group_list = list(my_groups.items())
    for i, (group_name, group_info) in enumerate(group_list, 1):
        is_leader = group_info.get("leader") == USER_ID
        leader_status = " [LÍDER]" if is_leader else ""
        
        print(f"{i}. {group_name}{leader_status}")
        print(f"   Líder: {group_info.get('leader', 'N/A')}")
        print(f"   Membros: {', '.join(group_info.get('members', []))}")
        print()
    
    choice = safe_input("Digite o número do grupo para se reinscrever (ou Enter para voltar): ")
    if choice.isdigit() and 1 <= int(choice) <= len(group_list):
        selected_group = group_list[int(choice) - 1][0]
        client.subscribe(selected_group, qos=1)
        print(f"[INFO] Reinscrito no grupo: {selected_group}")
        print("Agora você pode receber mensagens do grupo!")

def send_message():
    topic = safe_input("Digite o tópico da sessão ou grupo: ")
    msg = safe_input("Mensagem: ")
    client.publish(topic, msg, qos=1)
    print("Mensagem enviada com garantia de entrega!")

def list_my_conversations():
    """Lista todas as conversas/sessões ativas do usuário (dados em memória)"""
    if not active_sessions:
        print("Você não tem conversas ativas.")
        return
    
    print(f"\n💬 Suas conversas ativas ({len(active_sessions)}):")
    session_list = list(active_sessions.items())
    for i, (topic, data) in enumerate(session_list, 1):
        other_users = [u for u in data["users"] if u != USER_ID] if "users" in data else []
        print(f"{i}. {topic}")
        if "users" in data:
            print(f"   Participantes: {', '.join(data['users'])}")
            print(f"   Outros usuários: {', '.join(other_users) if other_users else 'Só você'}")
        print()
    
    choice = safe_input("Digite o número da conversa para se reinscrever (ou Enter para voltar): ")
    if choice.isdigit() and 1 <= int(choice) <= len(session_list):
        selected_topic = session_list[int(choice) - 1][0]
        client.subscribe(selected_topic, qos=1)
        print(f"[INFO] Reinscrito em: {selected_topic}")

def handle_pending_requests():
    if not pending_requests:
        print("Nenhuma solicitação pendente.")
        return
    
    print("\nSolicitações pendentes:")
    for user, data in pending_requests.copy().items():
        print(f"\n{user} quer iniciar chat")
        resp = safe_input("Aceitar? (s/n): ").lower()
        if resp == "s":
            timestamp = int(time.time())
            session_topic = f"{USER_ID}_{data['from']}_{timestamp}"
            
            # Adiciona às sessões ativas em memória
            active_sessions[session_topic] = {"users": [USER_ID, data['from']]}
            
            # Informa ao solicitante o tópico da sessão
            client.publish(f"{data['from']}_Control", json.dumps({"type":"chat_accept","session":session_topic}))
            
            # Se inscreve no tópico da sessão para receber mensagens com QoS 1
            client.subscribe(session_topic, qos=1)
            
            print(f"[INFO] Chat iniciado no tópico: {session_topic}")
            print(f"[INFO] Você agora está inscrito para receber mensagens em: {session_topic} (com garantia)")
        else:
            print("Solicitação recusada.")
        
        # Remove da lista de pendentes
        del pending_requests[user]

def exit_program():
    client.publish("USERS", json.dumps({"user": USER_ID, "status": "offline"}))
    client.disconnect()
    print("Desconectado!")

# Inicializa MQTT
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=USER_ID, 
    clean_session=False
)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)
client.loop_start()

# Sinaliza presença online
client.publish("USERS", json.dumps({"user": USER_ID, "status": "online"}))
online_users.add(USER_ID)

# Inicia thread para processar mensagens de controle
control_thread = threading.Thread(target=process_control_messages, daemon=True)
control_thread.start()

# Menu principal (executa na thread principal)
menu()
