import socket
import os
import threading

SERVER_PORT = 1234
CLIENT_PORT = 1235
PUBLIC_FOLDER = "./public"

if not os.path.exists(PUBLIC_FOLDER):
    os.makedirs(PUBLIC_FOLDER)

def handle_file_request(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        parts = request.split()
        if parts[0] == "GET" and len(parts) >= 3:
            filename = parts[1]
            offset_start = int(parts[2])
            offset_end = int(parts[3]) if len(parts) == 4 else None

            file_path = os.path.join(PUBLIC_FOLDER, filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    file.seek(offset_start)
                    data = file.read(offset_end - offset_start if offset_end else None)
                    client_socket.sendall(data)
            else:
                client_socket.sendall(b"FILENOTFOUND")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client_socket.close()

def start_file_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", CLIENT_PORT))
        server_socket.listen(5)
        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=handle_file_request, args=(client_socket,)).start()

def join_server(server_ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, SERVER_PORT))
            client_socket.sendall(f"JOIN {server_ip}".encode())
            response = client_socket.recv(1024).decode()
            print(response)
    except Exception as e:
        print(f"[ERROR] {e}")

def refresh_list(server_ip):
    files_local = {f for f in os.listdir(PUBLIC_FOLDER) if os.path.isfile(os.path.join(PUBLIC_FOLDER, f))}

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, SERVER_PORT))

            client_socket.sendall(b"LISTMYFILES")
            response = client_socket.recv(4096).decode()

            files_server = set()
            if response.strip():
                for line in response.strip().split("\n"):
                    if "Name: " in line:
                        filename = line.replace("Name: ", "").strip()
                        files_server.add(filename)

            for file in files_local:
                size = os.path.getsize(os.path.join(PUBLIC_FOLDER, file))
                client_socket.sendall(f"CREATEFILE {file} {size}".encode())
                print(client_socket.recv(1024).decode())

            for file in files_server - files_local:
                client_socket.sendall(f"DELETEFILE {file}".encode())
                print(client_socket.recv(1024).decode())

    except Exception as e:
        print(f"[ERROR] {e}")

def search_file(server_ip, filename):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, SERVER_PORT))
            client_socket.sendall(f"SEARCH {filename}".encode())
            response = client_socket.recv(4096).decode()
            print(response)
    except Exception as e:
        print(f"[ERROR] {e}")

def get_file(client_ip, filename, offset_start, offset_end=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((client_ip, CLIENT_PORT))
            message = f"GET {filename} {offset_start} {offset_end}" if offset_end else f"GET {filename} {offset_start}"
            client_socket.sendall(message.encode())
            with open(os.path.join(PUBLIC_FOLDER, filename), 'wb') as file:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file.write(data)
            print(f"[INFO] File {filename} downloaded successfully.")
    except Exception as e:
        print(f"[ERROR] {e}")

def list_files(server_ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, SERVER_PORT))
            client_socket.sendall(f"LISTFILES".encode())
            response = client_socket.recv(4096).decode()
            print(response)
    except Exception as e:
        print(f"[ERROR] {e}")

def leave_server(server_ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, SERVER_PORT))
            client_socket.sendall("LEAVE".encode())
            response = client_socket.recv(1024).decode()
            print(response)
    except Exception as e:
        print(f"[ERROR] {e}")

def delete_file(server_ip, filename):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, SERVER_PORT))
            client_socket.sendall(f"DELETEFILE {filename}".encode())
            response = client_socket.recv(1024).decode()
            print(response)
    except Exception as e:
        print(f"[ERROR] {e}")

def print_options():
    print("\n1- JOIN SERVER")
    print("2- REFRESH LIST")
    print("3- SEARCH FILE")
    print("4- GET FILE")
    print("5- LEAVE SERVER")
    print("6- LIST FILES")
    print("7- DELETE FILE")
    print("0- EXIT\n")

def main():
    try:
        while True:
            print_options()
            choice = input("Select an option: ")
            if choice == "1":
                server_ip = input("Enter server IP: ")
                join_server(server_ip)
            elif choice == "2":
                server_ip = input("Enter server IP: ")
                refresh_list(server_ip)
            elif choice == "3":
                server_ip = input("Enter server IP: ")
                filename = input("Enter filename to search: ")
                search_file(server_ip, filename)
            elif choice == "4":
                client_ip = input("Enter client IP: ")
                filename = input("Enter filename to download: ")
                offset_start = input("Enter offset start: ")
                offset_end = input("Enter offset end (optional): ") or None
                get_file(client_ip, filename, offset_start, offset_end)
            elif choice == "5":
                server_ip = input("Enter server IP: ")
                leave_server(server_ip)
            elif choice == "6":
                server_ip = input("Enter server IP: ")
                list_files(server_ip)
            elif choice == "7":
                server_ip = input("Enter server IP: ")
                filename = input("Enter filename to delete: ")
                delete_file(server_ip, filename)
            elif choice == "0":
                print("[INFO] Exiting program.")
                break
            else:
                input("\nInvalid option, try againg...")
    except KeyboardInterrupt:
        print("\nSEE YOU LATER :)")

if __name__ == "__main__":
    threading.Thread(target=start_file_server, daemon=True).start()
    main()