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
chats: set[str] = set()
groups: Dict[str, Dict[str, any]] = {}
group_invites: Queue = Queue()

def on_connect(client: mqtt.Client, userdata, flags, rc, properties):
    print("Conectado ao broker MQTT")
    client.subscribe(f"{USER_ID}_Control", qos=2)
    client.subscribe(f"{USERS_TOPIC}/+", qos=2)
    client.subscribe(f"{USERS_TOPIC}/{USER_ID}/chats", qos=2)
    client.subscribe(f"{GROUPS_TOPIC}/+/info", qos=2)
    client.subscribe(f"{GROUPS_TOPIC}/+/members", qos=2)
    client.subscribe(f"{GROUPS_TOPIC}/+/chat", qos=2)
    client.publish(f"{USERS_TOPIC}/{USER_ID}", "online", qos=2, retain=True)
    print(f"[Status] user '{USER_ID}' is now online")

def on_disconnect(client, userdata, rc):
    print(f"[Status] user '{USER_ID}' is now offline")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()   

    if msg.topic.endswith("/chats"):
        control_message: dict[str, any] = json.loads(payload)
        print("entrou aqui", control_message, payload)
        value: str = control_message.get("value")
        if (len(value) > 0): 
            value = value.split(";")
            for v in value:
                chats.add(v)
    elif msg.topic.startswith(USERS_TOPIC):
        user_id = msg.topic.split('/')[-1]
        status = payload
        connected_users[user_id] = status
    elif msg.topic.startswith(GROUPS_TOPIC):
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 3:
            group_name = topic_parts[1]
            message_type = topic_parts[2]
            
            if message_type == "info":
                try:
                    group_info = json.loads(payload)
                    if group_name not in groups:
                        groups[group_name] = {"leader": group_info.get("leader"), "members": []}
                    else:
                        groups[group_name]["leader"] = group_info.get("leader")
                except json.JSONDecodeError:
                    pass
            elif message_type == "members":
                try:
                    members_data = json.loads(payload)
                    if group_name not in groups:
                        groups[group_name] = {"leader": "", "members": members_data.get("members", [])}
                    else:
                        groups[group_name]["members"] = members_data.get("members", [])
                except json.JSONDecodeError:
                    pass
            elif message_type == "chat":
                print("SAI CAPIROTO")
                try:
                    chat_message = json.loads(payload)
                    action = chat_message.get("action")
                    from_user = chat_message.get("from")
                    value = chat_message.get("value")
                    
                    if action == "message" and from_user != USER_ID:
                        if USER_ID in groups.get(group_name, {}).get("members", []):
                            print(f"\n[{group_name}] {from_user}: {value}")
                            #input("Pressione Enter para continuar...")
                except json.JSONDecodeError:
                    pass
    elif msg.topic == f"{USER_ID}_Control":
        try:
            control_message: dict[str, any] = json.loads(payload)
            action = control_message.get("action")
            from_user = control_message.get("from")
            value: str = control_message.get("value")
            if action == "chat_request" and from_user:
                pending_notifications.put(("chat_request", from_user))
                notification_event.set()
                print(f"\nNova solicitação de chat de '{from_user}'! Digite '7' no menu para responder.")
            elif action == "chat_accepted" and from_user:
                # pending_notifications.put(("chat_accepted", (from_user, value)))
                # notification_event.set()
                
                print(f"\nSua solicitação de chat foi aceita por '{from_user}'!")
                handle_chat_accepted(from_user, value)
            elif action == "group_invite" and from_user:
                group_name = control_message.get("group_name")
                group_invites.put((from_user, group_name))
                print(f"\n🎉 Convite para o grupo '{group_name}' de '{from_user}'! Digite '7' no menu para responder.")
            elif action == "group_join_request" and from_user:
                group_name = control_message.get("group_name")
                
                if from_user == USER_ID:
                    return
                
                if group_name in groups and groups[group_name].get("leader") == USER_ID:
                    pending_notifications.put(("group_join_request", from_user, group_name))
                    print(f"\n🚪 Solicitação de entrada no grupo '{group_name}' de '{from_user}'! Digite '7' no menu para responder.")
            elif action == "group_join" and from_user:
                group_name = control_message.get("group_name")
                print(f"\n{from_user} entrou no grupo '{group_name}'!")
            elif action == "group_join_accepted" and from_user:
                group_name = control_message.get("group_name")
                print(f"\nSolicitação de entrada aceita por '{from_user}' no grupo '{group_name}'!")
                chats.add(f"GROUP_{group_name}")
            elif action == "group_leadership_transferred" and from_user:
                group_name = control_message.get("group_name")
                print(f"\n👑 Você agora é o líder do grupo '{group_name}' (transferido por '{from_user}')!")
            elif action == "group_member_left" and from_user:
                group_name = control_message.get("group_name")
                new_leader = control_message.get("new_leader")
                if new_leader:
                    print(f"\n🚪 {from_user} saiu do grupo '{group_name}'. Novo líder: {new_leader}")
                else:
                    print(f"\n🚪 {from_user} saiu do grupo '{group_name}'")
            elif action == "group_removed" and from_user:
                group_name = control_message.get("group_name")
                print(f"\n🗑️  O grupo '{group_name}' foi removido pelo líder '{from_user}'")
                chats.discard(f"GROUP_{group_name}")
            elif action == "chats" and value:
                [chats.add(v) for v in value.split(";")]

        except json.JSONDecodeError:
            print("Mensagem de controle inválida recebida.")
    else: 
        control_message: dict[str, any] = json.loads(payload)
        action = control_message.get("action")
        from_user = control_message.get("from")
        value: str = control_message.get("value")
        if action == "message" and value:
            
            user_from = control_message.get("from") 
            if (user_from != USER_ID):
                print(f"[{user_from}] > {value}")
            
            # input("...")    


def get_online_users():
    return [user_id for user_id, status in connected_users.items() if status == "online"]

def get_offline_users():
    return [user_id for user_id, status in connected_users.items() if status == "offline"]

def save_chats():
    client.publish(f"{USERS_TOPIC}/{USER_ID}/chats", json.dumps({
        "action": "chats",
        "value": ";".join(chats)
    }), qos=1, retain=True)

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
    total_notifications = pending_notifications.qsize() + group_invites.qsize()
    
    if total_notifications == 0:
        print("Nenhuma notificação pendente.")
        return
    
    print("\n=== Notificações Pendentes ===")
    
    all_notifications = []
    chat_notifications = []
    
    while not pending_notifications.empty():
        notification = pending_notifications.get()
        chat_notifications.append(notification)
    
    for notification in chat_notifications:
        if len(notification) == 2:
            action, from_user = notification
            all_notifications.append(("chat", action, from_user, None))
        elif len(notification) == 3:
            action, from_user, group_name = notification
            all_notifications.append(("group_request", action, from_user, group_name))
    
    group_notifications = []
    while not group_invites.empty():
        group_notifications.append(group_invites.get())
    
    for from_user, group_name in group_notifications:
        all_notifications.append(("group", "invite", from_user, group_name))
    
    for i, (notif_type, action, from_user, extra) in enumerate(all_notifications, 1):
        if notif_type == "chat":
            if action == "chat_request":
                print(f"{i}. Solicitação de chat de '{from_user}'")
            elif action == "chat_accepted":
                print(f"{i}. Chat aceito por '{from_user}'")
        elif notif_type == "group":
            if action == "invite":
                print(f"{i}. Convite para o grupo '{extra}' de '{from_user}'")
        elif notif_type == "group_request":
            if action == "group_join_request":
                print(f"{i}. Solicitação de entrada no grupo '{extra}' de '{from_user}'")
    
    if not all_notifications:
        return
    
    choice = input("\nDigite o número da notificação para processar (ou Enter para sair): ")
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(all_notifications):
            notif_type, action, from_user, extra = all_notifications[choice_idx]
            
            if notif_type == "chat":
                if action == "chat_request":
                    handle_chat_request(from_user)
                elif action == "chat_accepted":
                    print("teste", from_user)
                    # handle_chat_accepted(from_user[0], from_user[1])
            elif notif_type == "group" and action == "invite":
                handle_group_invite(from_user, extra)
            elif notif_type == "group_request" and action == "group_join_request":
                handle_group_join_request(from_user, extra)
            
            for i, (n_type, n_action, n_from, n_extra) in enumerate(all_notifications):
                if i != choice_idx:
                    if n_type == "chat":
                        pending_notifications.put((n_action, n_from))
                    elif n_type == "group":
                        group_invites.put((n_from, n_extra))
                    elif n_type == "group_request":
                        pending_notifications.put((n_action, n_from, n_extra))
        else:
            for n_type, n_action, n_from, n_extra in all_notifications:
                if n_type == "chat":
                    pending_notifications.put((n_action, n_from))
                elif n_type == "group":
                    group_invites.put((n_from, n_extra))
                elif n_type == "group_request":
                    pending_notifications.put((n_action, n_from, n_extra))
            print("Número inválido.")
    except ValueError:
        for n_type, n_action, n_from, n_extra in all_notifications:
            if n_type == "chat":
                pending_notifications.put((n_action, n_from))
            elif n_type == "group":
                group_invites.put((n_from, n_extra))
            elif n_type == "group_request":
                pending_notifications.put((n_action, n_from, n_extra))

def handle_group_invite(from_user, group_name):
    """Processa convite para grupo"""
    response = input(f"Convite para o grupo '{group_name}' de '{from_user}'. Aceitar? (S/n): ")
    
    if response.lower() != 'n':
        if group_name in groups:
            if USER_ID not in groups[group_name]["members"]:
                groups[group_name]["members"].append(USER_ID)
            
            members_info = {
                "members": groups[group_name]["members"]
            }
            client.publish(f"{GROUPS_TOPIC}/{group_name}/members", json.dumps(members_info), qos=2, retain=True)
            
            for member in groups[group_name]["members"]:
                if member != USER_ID:
                    client.publish(f"{member}_Control", json.dumps({
                        "action": "group_join",
                        "from": USER_ID,
                        "group_name": group_name
                    }), qos=2)
            
            print(f"Você entrou no grupo '{group_name}'!")
            chats.add(f"GROUP_{group_name}")
        else:
            print("Erro: Grupo não encontrado.")
    else:
        print("Convite recusado.")

def handle_group_join_request(from_user, group_name):
    """Processa solicitação de entrada no grupo (apenas para líderes)"""
    response = input(f"'{from_user}' quer entrar no grupo '{group_name}'. Aceitar? (S/n): ")

    if response.lower() != 'n':
        if group_name in groups and groups[group_name].get("leader") == USER_ID:
            if from_user not in groups[group_name]["members"]:
                groups[group_name]["members"].append(from_user)
            
            members_info = {
                "members": groups[group_name]["members"]
            }
            client.publish(f"{GROUPS_TOPIC}/{group_name}/members", json.dumps(members_info), qos=2, retain=True)
            
            client.publish(f"{from_user}_Control", json.dumps({
                "action": "group_join_accepted",
                "from": USER_ID,
                "group_name": group_name
            }), qos=2)
            
            for member in groups[group_name]["members"]:
                if member != USER_ID and member != from_user:
                    client.publish(f"{member}_Control", json.dumps({
                        "action": "group_join",
                        "from": from_user,
                        "group_name": group_name
                    }), qos=2)

            print(f"'{from_user}' foi aceito no grupo '{group_name}'!")
        else:
            print("Erro: Você não é líder deste grupo ou grupo não encontrado.")
    else:
        print("Solicitação recusada.")

def handle_chat_request(from_user_id):
    response = input(f"Você tem uma solicitação de chat de '{from_user_id}'. Aceitar? (S/n): ")
    if response.lower() == 'n':
        print("Solicitação de chat recusada.")
    else:
        one_to_one_topic = f"{USER_ID}_{from_user_id}"
        client.publish(f"{from_user_id}_Control", json.dumps({
            "action": "chat_accepted",
            "from": USER_ID,
            "value": one_to_one_topic
        }), qos=2)
        print(f"Chat iniciado no tópico '{one_to_one_topic}'")
        client.subscribe(one_to_one_topic, qos=2)
        chats.add(one_to_one_topic)
        save_chats()
  
def handle_chat_accepted(from_user_id, topic_name):
    print(f"Sua solicitação de chat foi aceita por '{from_user_id}' blblabla.")
    # one_to_one_topic = f"{USER_ID}_{from_user_id}"
    print(f"Chat iniciado no tópico '{topic_name}'")
    client.subscribe(topic_name, qos=2)
    chats.add(topic_name)
    save_chats()

def list_users():
    print('=== Usuários ===')
    if not connected_users:
        print('Nenhum usuário encontrado. Aguarde as mensagens retained do broker...')
    else:
        online_users = get_online_users()
        offline_users = get_offline_users()
        
        if online_users:
            print(f'Online ({len(online_users)}):')
            for user in online_users:
                print(f"  • {user}")
        
        if offline_users:
            print(f'Offline ({len(offline_users)}):')
            for user in offline_users:
                print(f"  • {user}")
    
    # input("\nPressione Enter para continuar...")

def list_chats():
    print('=== Conversas ===')
    if len(chats) == 0:
        print('Nenhum conversa encontrada.')
    else:
        [print(f"({index}). {id_chat}") for index, id_chat in enumerate(chats, 1)]

def create_group():
    group_name = input("Digite o nome do grupo: ")
    if not group_name:
        print("Nome do grupo não pode ser vazio.")
        return

    if group_name in groups:
        print(f"O grupo '{group_name}' já existe!")
        print(f"Líder atual: {groups[group_name]['leader']}")
        print(f"Membros: {', '.join(groups[group_name]['members']) if groups[group_name]['members'] else 'Nenhum membro'}")
        return

    groups[group_name] = {
        "leader": USER_ID,
        "members": [USER_ID]
    }
    
    group_info = {
        "leader": USER_ID,
        "created_by": USER_ID,
        "created_at": time.time()
    }
    
    members_info = {
        "members": [USER_ID]
    }
    
    client.publish(f"{GROUPS_TOPIC}/{group_name}/info", json.dumps(group_info), qos=2, retain=True)
    client.publish(f"{GROUPS_TOPIC}/{group_name}/members", json.dumps(members_info), qos=2, retain=True)

    print(f"Grupo '{group_name}' criado com sucesso!")
    print(f"Você é o líder do grupo '{group_name}'")
    
    # input("\nPressione Enter para continuar...")

def join_group():
    """Função para entrar em um grupo existente ou solicitar entrada"""
    if not groups:
        print("Nenhum grupo disponível no momento.")
        # input("\nPressione Enter para continuar...")
        return
    
    available_groups = []
    for group_name, group_info in groups.items():
        members = group_info.get("members", [])
        is_member = USER_ID in members
        if not is_member:
            available_groups.append((group_name, group_info))
    
    if not available_groups:
        print("Você já participa de todos os grupos disponíveis.")
        # input("\nPressione Enter para continuar...")
        return
    
    print("=== Grupos Disponíveis para Entrada ===")
    
    for i, (group_name, group_info) in enumerate(available_groups, 1):
        leader = group_info.get("leader", "Desconhecido")
        members = group_info.get("members", [])
        
        print(f"{i}. {group_name}")
        print(f"    Líder: {leader}")
        print(f"    Membros: {len(members)}")
        print("     Disponível para entrada")
        print()
    
    choice = input("Digite o número do grupo para entrar (ou Enter para cancelar): ")
    
    try:
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(available_groups):
            group_name, group_info = available_groups[choice_idx]
            
            if USER_ID in group_info.get("members", []):
                print(f"Você já é membro do grupo '{group_name}'.")
                # input("\nPressione Enter para continuar...")
                return
            
            leader = group_info.get("leader")
            if leader and leader != USER_ID:
                request_group_join(group_name, leader)
            else:
                print("Erro: Líder do grupo não encontrado ou você é o líder.")
        else:
            print("Número inválido.")
    except ValueError:
        print("Cancelado.")
    
    # input("\nPressione Enter para continuar...")

def request_group_join(group_name, leader):
    """Solicita entrada em um grupo"""
    message = json.dumps({
        "action": "group_join_request",
        "from": USER_ID,
        "group_name": group_name
    })
    
    client.publish(f"{leader}_Control", message, qos=2)
    print(f"Solicitação de entrada enviada para o líder '{leader}' do grupo '{group_name}'")

def invite_to_group():
    """Convida um usuário para um grupo (apenas líderes)"""
    my_led_groups = {name: info for name, info in groups.items() 
                     if info.get("leader") == USER_ID}
    
    if not my_led_groups:
        print("Você não é líder de nenhum grupo.")
        # input("\nPressione Enter para continuar...")
        return
    
    print("=== Seus Grupos (Como Líder) ===")
    for i, (group_name, group_info) in enumerate(my_led_groups.items(), 1):
        members = group_info.get("members", [])
        print(f"{i}. 📁 {group_name} ({len(members)} membros)")
    
    group_choice = input("\nDigite o número do grupo para convidar alguém: ")
    
    try:
        group_idx = int(group_choice) - 1
        group_list = list(my_led_groups.items())
        
        if 0 <= group_idx < len(group_list):
            group_name, group_info = group_list[group_idx]
            
            online_users = get_online_users()
            current_members = group_info.get("members", [])
            available_users = [user for user in online_users 
                             if user != USER_ID and user not in current_members]
            
            if not available_users:
                print("Nenhum usuário disponível para convite.")
                # input("\nPressione Enter para continuar...")
                return
            
            print("\n=== Usuários Disponíveis ===")
            for i, user in enumerate(available_users, 1):
                print(f"{i}. {user}")
            
            user_choice = input("\nDigite o número do usuário para convidar: ")
            
            try:
                user_idx = int(user_choice) - 1
                if 0 <= user_idx < len(available_users):
                    target_user = available_users[user_idx]
                    send_group_invite(target_user, group_name)
                else:
                    print("Número inválido.")
            except ValueError:
                print("Número inválido.")
        else:
            print("Número inválido.")
    except ValueError:
        print("Número inválido.")
    
    # input("\nPressione Enter para continuar...")

def send_group_invite(target_user, group_name):
    """Envia convite para um usuário entrar no grupo"""
    message = json.dumps({
        "action": "group_invite",
        "from": USER_ID,
        "group_name": group_name
    })
    
    client.publish(f"{target_user}_Control", message, qos=2)
    print(f"Convite enviado para '{target_user}' entrar no grupo '{group_name}'")

def send_message():
    print("=== Enviar Mensagem ===")
    print("1. Conversas 1-on-1")
    print("2. Grupos")
    
    choice = input("Escolha o tipo (1 ou 2): ")
    
    if choice == "1":
        send_private_message()
    elif choice == "2":
        send_group_message()
    else:
        print("Opção inválida.")

def send_private_message():
    """Envia mensagem em chat 1-on-1"""
    list_chats()
    if not chats:
        return
    
    to = input("Digite o id da conversa: ")
    if to not in chats:
        print("Conversa não encontrada.")
        return
        
    message = input("[você] > ")
    client.publish(to, json.dumps({
        "action": "message",
        "from": USER_ID, 
        "value": message
    }), 2)

def send_group_message():
    """Envia mensagem para um grupo"""
    my_groups = {name: info for name, info in groups.items() if USER_ID in info.get("members", [])}
    
    if not my_groups:
        print("Você não participa de nenhum grupo.")
        # input("\nPressione Enter para continuar...")
        return
    
    print("=== Meus Grupos ===")
    group_list = list(my_groups.items())
    for i, (group_name, group_info) in enumerate(group_list, 1):
        members_count = len(group_info.get("members", []))
        print(f"{i}. 📁 {group_name} ({members_count} membros)")
    
    choice = input("\nDigite o número do grupo: ")
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(group_list):
            group_name, group_info = group_list[choice_idx]
            
            message = input(f"[{group_name}] você > ")
            if message.strip():
                client.publish(f"{GROUPS_TOPIC}/{group_name}/chat", json.dumps({
                    "action": "message",
                    "from": USER_ID,
                    "value": message
                }), qos=2)
                print("Mensagem enviada para o grupo!")
            else:
                print("Mensagem vazia, cancelado.")
        else:
            print("Número inválido.")
    except ValueError:
        print("Número inválido.")
    
    # input("\nPressione Enter para continuar...")

def list_my_groups():
    print('=== Meus Grupos ===')
    my_groups = {name: info for name, info in groups.items() if USER_ID in info.get("members", [])}
    
    if not my_groups:
        print('Você não participa de nenhum grupo.')
    else:
        for i, (group_name, group_info) in enumerate(my_groups.items(), 1):
            leader = group_info.get("leader", "Desconhecido")
            members = group_info.get("members", [])
            is_leader = leader == USER_ID
            
            print(f"\n{i}. 📁 {group_name}")
            if is_leader:
                print(f"   👑 Você é o líder deste grupo")
            else:
                print(f"   👑 Líder: {leader}")
            
            if len(members) > 1:
                other_members = [member for member in members if member != USER_ID]
                if other_members:
                    print(f"   👥 Outros membros: {', '.join(other_members)}")
            else:
                print(f"   👥 Outros membros: Nenhum")
            
            print(f"   📊 Total de membros: {len(members)}")
    
    # input("\nPressione Enter para continuar...")

def leave_group():
    """Sair de um grupo"""
    my_groups = {name: info for name, info in groups.items() if USER_ID in info.get("members", [])}
    
    if not my_groups:
        print("Você não participa de nenhum grupo.")
        # input("\nPressione Enter para continuar...")
        return
    
    print("=== Meus Grupos - Sair de Grupo ===")
    group_list = list(my_groups.items())
    
    for i, (group_name, group_info) in enumerate(group_list, 1):
        leader = group_info.get("leader", "Desconhecido")
        members_count = len(group_info.get("members", []))
        is_leader = leader == USER_ID
        
        print(f"{i}. {group_name}")
        print(f"    Líder: {leader}")
        print(f"    Membros: {members_count}")
        
        if is_leader:
            print("    Você é o líder - sair irá transferir liderança ou remover o grupo")
        print()
    
    choice = input("Digite o número do grupo para sair (ou Enter para cancelar): ")
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(group_list):
            group_name, group_info = group_list[choice_idx]
            
            confirmation = input(f"⚠️  Tem certeza que quer sair do grupo '{group_name}'? (S/n): ")
            if confirmation.lower() != 'n':
                leave_group_action(group_name, group_info)
            else:
                print("Operação cancelada.")
        else:
            print("Número inválido.")
    except ValueError:
        print("Cancelado.")
    
    # input("\nPressione Enter para continuar...")

def leave_group_action(group_name, group_info):
    """Executa a ação de sair do grupo"""
    members = group_info.get("members", [])
    leader = group_info.get("leader")
    is_leader = leader == USER_ID
    
    if USER_ID not in members:
        print("Você não é membro deste grupo.")
        return
    
    members.remove(USER_ID)
    
    if len(members) == 0:
        if group_name in groups:
            del groups[group_name]
        
        client.publish(f"{GROUPS_TOPIC}/{group_name}/info", "", qos=2, retain=True)
        client.publish(f"{GROUPS_TOPIC}/{group_name}/members", "", qos=2, retain=True)
        
        print(f"Grupo '{group_name}' foi removido (último membro saindo).")
        
    elif is_leader and len(members) > 0:
        new_leader = members[0]
        groups[group_name]["leader"] = new_leader
        groups[group_name]["members"] = members
        
        group_info_update = {
            "leader": new_leader,
            "updated_at": time.time()
        }
        members_info = {
            "members": members
        }
        
        client.publish(f"{GROUPS_TOPIC}/{group_name}/info", json.dumps(group_info_update), qos=2, retain=True)
        client.publish(f"{GROUPS_TOPIC}/{group_name}/members", json.dumps(members_info), qos=2, retain=True)
        
        client.publish(f"{new_leader}_Control", json.dumps({
            "action": "group_leadership_transferred",
            "from": USER_ID,
            "group_name": group_name
        }), qos=2)
        
        for member in members:
            if member != new_leader:
                client.publish(f"{member}_Control", json.dumps({
                    "action": "group_member_left",
                    "from": USER_ID,
                    "group_name": group_name,
                    "new_leader": new_leader
                }), qos=2)
        
        print(f"🔄 Você saiu do grupo '{group_name}' e a liderança foi transferida para '{new_leader}'.")
        
    else:
        groups[group_name]["members"] = members
        
        members_info = {
            "members": members
        }
        client.publish(f"{GROUPS_TOPIC}/{group_name}/members", json.dumps(members_info), qos=2, retain=True)
        
        for member in members:
            client.publish(f"{member}_Control", json.dumps({
                "action": "group_member_left",
                "from": USER_ID,
                "group_name": group_name
            }), qos=2)
        
        print(f"Você saiu do grupo '{group_name}'.")
    
    chats.discard(f"GROUP_{group_name}")

def remove_group():
    my_led_groups = {name: info for name, info in groups.items() 
                     if info.get("leader") == USER_ID}
    
    if not my_led_groups:
        print("Você não é líder de nenhum grupo.")
        # input("\nPressione Enter para continuar...")
        return
    
    print("=== Meus Grupos (Como Líder) - Remover Grupo ===")
    group_list = list(my_led_groups.items())
    
    for i, (group_name, group_info) in enumerate(group_list, 1):
        members_count = len(group_info.get("members", []))
        print(f"{i}. {group_name}")
        print(f"   Membros: {members_count}")
        print()
    
    choice = input("Digite o número do grupo para remover (ou Enter para cancelar): ")
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(group_list):
            group_name, group_info = group_list[choice_idx]
            
            members_count = len(group_info.get("members", []))

            confirmation = input(f"ATENÇÃO: Remover o grupo '{group_name}' irá expulsar todos os {members_count} membros. Confirma? (digite 'REMOVER' para confirmar): ")

            if confirmation == "REMOVER":
                remove_group_action(group_name, group_info)
            else:
                print("Operação cancelada.")
        else:
            print("Número inválido.")
    except ValueError:
        print("Cancelado.")
    
    # input("\nPressione Enter para continuar...")

def remove_group_action(group_name, group_info):
    """Executa a ação de remover o grupo"""
    members = group_info.get("members", [])
    
    for member in members:
        if member != USER_ID:
            client.publish(f"{member}_Control", json.dumps({
                "action": "group_removed",
                "from": USER_ID,
                "group_name": group_name
            }), qos=2)
    
    if group_name in groups:
        del groups[group_name]
    
    client.publish(f"{GROUPS_TOPIC}/{group_name}/info", "", qos=2, retain=True)
    client.publish(f"{GROUPS_TOPIC}/{group_name}/members", "", qos=2, retain=True)
    
    chats.discard(f"GROUP_{group_name}")

    print(f"Grupo '{group_name}' foi removido permanentemente.")

def list_groups():
    print('=== Grupos Cadastrados ===')
    if not groups:
        print('Nenhum grupo encontrado.')
    else:
        for i, (group_name, group_info) in enumerate(groups.items(), 1):
            leader = group_info.get("leader", "Desconhecido")
            members = group_info.get("members", [])
            
            print(f"\n{i}. 📁 {group_name}")
            print(f"   👑 Líder: {leader}")
            
            if len(members) > 1:
                other_members = [member for member in members if member != leader]
                print(f"   👥 Membros: {', '.join(other_members)}")
            else:
                print(f"   👥 Membros: Apenas o líder")
            
            print(f"   📊 Total de membros: {len(members)}")
    
    # input("\nPressione Enter para continuar...")

def menu():
    pending_count = pending_notifications.qsize() + group_invites.qsize()
    notification_indicator = f" ({pending_count}) Notificações pendentes" if pending_count > 0 else ""
    
    print(f"\n--- MENU{notification_indicator} ---")
    print("1. Listar usuários")
    print("2. Solicitar conversa (one-to-one)")
    print("3. Criar grupo")
    print("4. Listar grupos")
    print("5. Entrar em grupo")
    print("6. Enviar mensagem")
    print("7. Responder notificações")
    print("8. Listar grupos que participo")
    print("9. Listar minhas conversas")
    print("10. Convidar para grupo")
    print("11. Sair de grupo")
    print("12. Remover grupo")
    print("0. Sair")
    choice = input("> ")

    if choice == "1":
        list_users()
    elif choice == "2":
        online_users = get_online_users()
        
        if online_users and len(online_users) > 1:
            print("Usuários online disponíveis para chat:")
            for i, user in enumerate(online_users, 1):
                if user != USER_ID:
                    print(f"{i}. {user}")

        offline_users = get_offline_users()
        if len(offline_users) > 0:
            print("Usuários offline:")
            for i, user in enumerate(offline_users, 1):
                if user != USER_ID:
                    print(f"{i}. {user}")

        request_chat()
    elif choice == "3":
        create_group()
    elif choice == "4":
        list_groups()
    elif choice == "5":
        join_group()
    elif choice == "6":
        send_message()
    elif choice == "7":
        process_pending_notifications()
    elif choice == "8":
        list_my_groups()
    elif choice == "9":
        list_chats()
        # input("\nPressione Enter para continuar...")
    elif choice == "10":
        invite_to_group()
    elif choice == "11":
        leave_group()
    elif choice == "12":
        remove_group()
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
    clean_session=False,
)
client.on_connect = on_connect
client.on_message = on_message

client.will_set(f"{USERS_TOPIC}/{USER_ID}", "offline", qos=2, retain=True)

client.connect(BROKER, PORT)
client.loop_start()

while menu():
    print()



    


