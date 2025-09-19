import paho.mqtt.client as mqtt
import json
import time
from typing import Dict, List
from queue import Queue
import threading

BROKER = "127.0.0.1"
PORT = 1883

USER_ID = input("Digite seu ID: ")

USERS_TOPIC = "USERS"
GROUPS_TOPIC = "GROUPS"

connected_users: Dict[str, str] = {}
pending_notifications: Queue = Queue()
notification_event = threading.Event()

def on_connect(client, userdata, flags, rc, properties):
    print("Conectado ao broker MQTT")
    client.subscribe(f"{USER_ID}_Control", qos=2)
    client.subscribe(f"{USERS_TOPIC}/+", qos=2)
    client.publish(f"{USERS_TOPIC}/{USER_ID}", "online", qos=2, retain=True)
    print(f"[Status] user '{USER_ID}' is now online")

def on_disconnect(client, userdata, rc):
    print(f"[Status] user '{USER_ID}' is now offline")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()    
    if msg.topic.startswith(USERS_TOPIC):
        user_id = msg.topic.split('/')[-1]
        status = payload
        connected_users[user_id] = status
    elif msg.topic == f"{USER_ID}_Control":
        try:
            control_message = json.loads(payload)
            action = control_message.get("action")
            from_user = control_message.get("from")
            if action == "chat_request" and from_user:
                pending_notifications.put(("chat_request", from_user))
                notification_event.set()
                print(f"\nNova solicitação de chat de '{from_user}'! Digite '7' no menu para responder.")
            elif action == "chat_accepted" and from_user:
                pending_notifications.put(("chat_accepted", from_user))
                notification_event.set()
                print(f"\nSua solicitação de chat foi aceita por '{from_user}'!")
        except json.JSONDecodeError:
            print("Mensagem de controle inválida recebida.")


def get_online_users():
    return [user_id for user_id, status in connected_users.items() if status == "online"]

def request_chat():
    target_user_id = input("Digite o ID do usuário com quem deseja conversar: ")
    if target_user_id == USER_ID:
        print("Você não pode iniciar uma conversa consigo mesmo.")
        return
    if target_user_id not in connected_users or connected_users[target_user_id] != "online":
        print(f"Usuário '{target_user_id}' não está online.")
        return

    target_user_topic = f"{target_user_id}_Control"
    message = json.dumps({
        "action": "chat_request",
        "from": USER_ID
    })
    client.publish(target_user_topic, message, qos=2)
    print(f"Solicitação de chat enviada para '{target_user_id}'")

def process_pending_notifications():
    if pending_notifications.empty():
        print("Nenhuma notificação pendente.")
        return
    
    print("\n=== Notificações Pendentes ===")
    notifications_to_process = []
    
    while not pending_notifications.empty():
        notifications_to_process.append(pending_notifications.get())
    
    for i, (action, from_user) in enumerate(notifications_to_process, 1):
        if action == "chat_request":
            print(f"{i}. Solicitação de chat de '{from_user}'")
        elif action == "chat_accepted":
            print(f"{i}. Chat aceito por '{from_user}'")
    
    if not notifications_to_process:
        return
    
    choice = input("\nDigite o número da notificação para processar (ou Enter para sair): ")
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(notifications_to_process):
            action, from_user = notifications_to_process[choice_idx]
            
            if action == "chat_request":
                handle_chat_request(from_user)
            elif action == "chat_accepted":
                handle_chat_accepted(from_user)
            
            for i, notification in enumerate(notifications_to_process):
                if i != choice_idx:
                    pending_notifications.put(notification)
        else:
            for notification in notifications_to_process:
                pending_notifications.put(notification)
            print("Número inválido.")
    except ValueError:
        for notification in notifications_to_process:
            pending_notifications.put(notification)

def handle_chat_request(from_user_id):
    response = input(f"Você tem uma solicitação de chat de '{from_user_id}'. Aceitar? (s/n): ")
    if response.lower() == 's':
        print(f"Iniciando chat com '{from_user_id}'...")
        one_to_one_topic = f"CHATS/{USER_ID}_{from_user_id}"
        client.publish(f"{from_user_id}_Control", json.dumps({
            "action": "chat_accepted",
            "from": USER_ID
        }), qos=2)
        print(f"Chat iniciado no tópico '{one_to_one_topic}'")
        client.subscribe(one_to_one_topic, qos=2)
    else:
        print("Solicitação de chat recusada.")

def handle_chat_accepted(from_user_id):
    print(f"Sua solicitação de chat foi aceita por '{from_user_id}'.")
    one_to_one_topic = f"CHATS/{USER_ID}_{from_user_id}"
    print(f"Chat iniciado no tópico '{one_to_one_topic}'")
    client.subscribe(one_to_one_topic, qos=2)

def list_users():
    print('=== Usuários ===')
    if not connected_users:
        print('Nenhum usuário encontrado. Aguarde as mensagens retained do broker...')
    else:
        online_users = get_online_users()
        offline_users = [user_id for user_id, status in connected_users.items() if status == "offline"]
        
        if online_users:
            print(f'Online ({len(online_users)}):')
            for user in online_users:
                print(f"  • {user}")
        
        if offline_users:
            print(f'Offline ({len(offline_users)}):')
            for user in offline_users:
                print(f"  • {user}")
    
    input("\nPressione Enter para continuar...")

def create_group():
    group_name = input("Digite o nome do grupo: ")
    if not group_name:
        print("Nome do grupo não pode ser vazio.")
        return
    

def list_groups():
    print('=== Grupos ===')
    input("\nPressione Enter para continuar...")

def menu():
    pending_count = pending_notifications.qsize()
    notification_indicator = f" 🔔({pending_count})" if pending_count > 0 else ""
    
    print(f"\n--- MENU{notification_indicator} ---")
    print("1. Listar usuários")
    print("2. Solicitar conversa (one-to-one)")
    print("3. Criar grupo")
    print("4. Listar grupos")
    print("5. Entrar em sessão/grupo")
    print("6. Enviar mensagem")
    print("7. Responder solicitações de chat")
    print("8. Listar grupos que participo")
    print("9. Listar minhas conversas")
    print("0. Sair")
    choice = input("> ")

    if choice == "1":
        list_users()
    elif choice == "2":
        online_users = get_online_users()
        if online_users:
            print("Usuários online disponíveis para chat:")
            for i, user in enumerate(online_users, 1):
                if user != USER_ID:  # Não mostrar o próprio usuário
                    print(f"{i}. {user}")
        else:
            print("Nenhum usuário online no momento.")
        request_chat()
    elif choice == "3":
        create_group()
    elif choice == "4":
        pass
    elif choice == "5":
        pass
    elif choice == "6":
        pass
    elif choice == "7":
        process_pending_notifications()
    elif choice == "8":
        pass
    elif choice == "9":
        pass
    elif choice == "0":
        exit_program()
        return False
    
    else:
        print("Opção inválida!")
    return True



def exit_program():
    client.publish(f"{USERS_TOPIC}/{USER_ID}", "offline", qos=2, retain=True)
    client.loop_stop()
    client.disconnect()
    print(f"{USER_ID} Desconectado!")


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=USER_ID, 
    clean_session=False
)
client.on_connect = on_connect
client.on_message = on_message

client.will_set(f"{USERS_TOPIC}/{USER_ID}", "offline", qos=2, retain=True)

client.connect(BROKER, PORT)
client.loop_start()



while menu():
    print()



    


