import ssl
import socket
import threading

host = '127.0.0.1'
port = 12346

# Crear y configurar el socket seguro
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

secure_server = context.wrap_socket(server, server_side=True)

clients = []
nicknames = []
first_message_flag = {}  # Marcar si es el primer mensaje de cada cliente

def broadcast(message):
    """Envía un mensaje a todos los clientes conectados."""
    for client in clients[:]:
        try:
            client.send(message)
        except (ssl.SSLEOFError, ConnectionResetError):
            # Si ocurre un error, eliminar al cliente
            clients.remove(client)
            client.close()

def handle(client):
    """Maneja los mensajes de cada cliente."""
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if not message:
                raise ConnectionResetError("Cliente desconectado.")
            
            index = clients.index(client)
            nickname = nicknames[index]
            
            # Evitar retransmitir el primer mensaje (nickname)
            if first_message_flag.get(client):
                first_message_flag[client] = False
                continue

            full_message = f"{nickname}: {message}"
            broadcast(full_message.encode('utf-8'))
        except (ssl.SSLEOFError, ConnectionResetError):
            index = clients.index(client)
            clients.remove(client)
            nickname = nicknames.pop(index)
            client.close()
            broadcast(f"{nickname} ha salido del chat.".encode('utf-8'))
            break

def receive():
    """Acepta nuevas conexiones y maneja el registro de apodos."""
    while True:
        client, address = secure_server.accept()
        print(f"Conexión aceptada de {address}")

        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)
        first_message_flag[client] = True

        broadcast(f"{nickname} se ha unido al chat.".encode('utf-8'))
        client.send("Conectado al servidor".encode('utf-8'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Servidor seguro escuchando")
receive()
