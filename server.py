import socket
import threading
import json
import os

LOCK = threading.Lock()
DATA_FILE = 'server_data.json'
SERVER_PORT = 1234

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as file:
        return json.load(file)

def save_data(data):
    with LOCK:
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

def handle_client(client_socket, client_address, data):
    client_ip = client_address[0]
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break

            print(f"[LOG] {client_ip} sent: {message}")

            command, *args = message.split()

            if command == 'JOIN':
                if client_ip not in data:
                    data[client_ip] = []
                    save_data(data)
                    client_socket.sendall(b"CONFIRMJOIN")
                else:
                    client_socket.sendall(b"CLIENTALREADYCONNECTED")

            elif command == 'CREATEFILE':
                filename, size = args
                size = int(size)
                if any(f['filename'] == filename for f in data.get(client_ip, [])):
                    client_socket.sendall(b"FILEALREADYEXISTS")
                else:
                    data[client_ip].append({"filename": filename, "size": size})
                    save_data(data)
                    client_socket.sendall(b"CONFIRMCREATEFILE")

            elif command == 'DELETEFILE':
                filename = args[0]
                if any(f['filename'] == filename for f in data.get(client_ip, [])):
                    data[client_ip] = [f for f in data[client_ip] if f['filename'] != filename]
                    save_data(data)
                    client_socket.sendall(b"CONFIRMDELETEFILE")
                else:
                    client_socket.sendall(b"FILENOTFOUND")

            elif command == 'SEARCH':
                filename = args[0]
                results = [
                    f"FILE {f['filename']} {ip} {f['size']}" for ip, files in data.items()
                    for f in files if f['filename'] == filename
                ]
                if results:
                    client_socket.sendall("\n".join(results).encode())
                else:
                    client_socket.sendall(b"FILENOTFOUND")

            elif command == 'LEAVE':
                if client_ip in data:
                    del data[client_ip]
                    save_data(data)
                    client_socket.sendall(b"CONFIRMLEAVE")
                else:
                    client_socket.sendall(b"CLIENTNOTFOUND")

            elif command == 'LISTFILES':
                response = ''
                for client in data:
                    response = response + f'ip: {client}\n'
                    for file in data[client]:
                        response = response + f'   filename: {file["filename"]}\n'
                        response = response + f'   size: {file["size"]}\n'
                
                client_socket.sendall(response.encode())

        except Exception as e:
            print(f"[ERROR] {client_ip}: {e}")
            break

    client_socket.close()

def main():
    data = load_data()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", SERVER_PORT))
    server_socket.listen(5)
    print(f"[SERVER] Listening on port {SERVER_PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"[CONNECTION] {client_address} connected.")
            threading.Thread(target=handle_client, args=(client_socket, client_address, data)).start()
    except KeyboardInterrupt:
        print("[SERVER] Shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()