from ast import Delete
import multiprocessing
import os
import shutil
import socket
import os
import threading
import json


class FileServer:

    class METHODS:
        DOWNLOAD_FILE = "download_file"
        UPLOAD_FILE = "upload_file"
        DIRECTORY_DETAILS = "directory_details"
        MKDIR = 'mkdir'
        DELETE = 'delete'

    def __init__(self, address=''):
        self.address = address

    def start(self):
        print("Starting server...")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.address, 1411))
        self.server.listen()
        self.wait_clients_proc = multiprocessing.Process(
            target=self.wait_clients)
        self.wait_clients_proc.start()

    def stop(self):
        print("Stopping server...")
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()
        self.wait_clients_proc.terminate()

    def wait_clients(self):
        while True:
            connection, (ip, _) = self.server.accept()
            request = FileServer.Request(connection, ip)
            if request.status == 'validated':
                threading.Thread(target=request.response_func).start()

    class Request:

        def __init__(self, connection: socket.socket, ip: str) -> None:
            self.status = 'accepted'
            self.client_id = ip
            self.connection = connection
            methods_config = {
                FileServer.METHODS.DOWNLOAD_FILE:  [
                    lambda path: os.path.isfile(path),
                    self.upload_response_file
                ],
                FileServer.METHODS.UPLOAD_FILE: [
                    lambda path: os.path.isdir(os.path.dirname(path)),
                    self.download_request_file
                ],
                FileServer.METHODS.DIRECTORY_DETAILS: [
                    lambda path: os.path.isdir(path),
                    self.response_directory_details
                ],
                FileServer.METHODS.MKDIR: [
                    lambda path: True,
                    self.mkdir
                ],
                FileServer.METHODS.DELETE: [
                    lambda path: lambda path: os.path.exists(path),
                    self.delete
                ]
            }
            try:
                request_data = connection.recv(8192).decode("utf-8")
                request_params = json.loads(request_data)
                if set(['method', 'path']) <= set(request_params):
                    if request_params['method'] in methods_config:
                        self.method = request_params['method']
                        self.path = os.path.abspath(request_params['path'])
                        path_valid, self.response_func = methods_config[self.method]
                        if not path_valid(self.path):
                            raise Exception("Invalid path")
                    else:
                        raise Exception("Method not found")
                else:
                    raise Exception("Invalid request")
                self.status = 'validated'
            except Exception as err:
                self.send_json({'status': 'ERROR', 'message': err.args[0]})
                self.finish_connection()

        def upload_response_file(self) -> None:
            print(f'Uploading [{self.path}]...')
            file_size = os.path.getsize(self.path)
            bytes_left = file_size
            file_stream = open(self.path, "rb")
            self.send_json({'status': 'OK', 'file_size': file_size})
            while bytes_left > 0:
                buffer = file_stream.read(
                    bytes_left if bytes_left < 2048 else 2048)
                self.connection.sendall(buffer)
                bytes_left = bytes_left - len(buffer)
            file_stream.close()
            self.finish_connection()

        def download_request_file(self) -> None:
            print(f'Downloading [{self.path}]...')
            self.send_json({'status': 'OK'})
            res_header = self.connection.recv(8192).decode("utf-8")
            file_size = int(res_header)
            bytes_left = file_size
            file_write = open(self.path, "wb")
            while bytes_left > 0:
                buffer = self.connection.recv(
                    bytes_left if bytes_left < 2048 else 2048)
                file_write.write(bytes(buffer))
                bytes_left = bytes_left - len(buffer)
            file_write.close()
            self.finish_connection()

        def response_directory_details(self) -> None:
            print(f'Getting [{self.path}] details...')
            files_and_directories = []
            for item_name in os.listdir(self.path):
                item_path = os.path.join(self.path, item_name)
                item_info = {
                    'name': item_name,
                }
                if os.path.isfile(item_path):
                    item_info['type'] = 'file'
                    item_info['size'] = os.path.getsize(item_path)
                else:
                    item_info['type'] = 'dir'
                files_and_directories.append(item_info)
            self.send_json({
                'status': 'OK',
                'full_path': self.path.split('/'),
                'items': files_and_directories
            })
            self.finish_connection()

        def mkdir(self) -> None:
            try:
                os.mkdir(self.path)
                self.send_json({'status': 'OK'})
            except Exception as err:
                self.send_json({'status': 'ERROR', 'message': err.args[0]})
            self.finish_connection()

        def delete(self) -> None:
            try:
                if os.path.isfile(self.path):
                    os.remove(self.path)
                elif os.path.isdir(self.path):
                    shutil.rmtree(self.path)
                else:
                    raise Exception("Invalid path")
                self.send_json({'status': 'OK'})
            except Exception as err:
                self.send_json({'status': 'ERROR', 'message': err.args[0]})
            self.finish_connection()

        def send_json(self, dictionary: dict) -> None:
            json_str = json.dumps(dictionary)
            self.connection.send(
                bytes(json_str+(' ' * (8192-len(json_str))), "utf-8"))

        def finish_connection(self):
            self.status = 'finished'
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
