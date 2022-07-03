import json
import socket
import os
from typing import List, Tuple


class FileServerClient:
    def __init__(self, server_addr=''):
        self.server_addr = server_addr
        self.current_dir, _ = self.directory_details('.')

    def change_directory(self, path: str) -> None:
        if path.startswith('/'):
            path = path.split('/')
        else:
            if len(self.current_dir) > 1 and self.current_dir[1] == '':
                path = ['', path]
            else:
                path = self.current_dir + [path]
        self.current_dir, _ = self.directory_details(path)

    def download_file(self, file_name: str, on_progress=None) -> None:
        sock, res = self.send_request(
            'download_file', self.current_dir + [file_name])
        file_size = int(res['file_size'])
        bytes_left = file_size
        if not os.path.isdir(os.path.join('.', 'downloads')):
            os.mkdir(os.path.join('.', 'downloads'))
        file_stream = open(os.path.join('.', 'downloads', file_name), 'wb')
        while bytes_left > 0:
            buffer = sock.recv(
                bytes_left if bytes_left < 2048 else 2048)
            file_stream.write(buffer)
            bytes_left = bytes_left - len(buffer)
            if on_progress != None:
                on_progress(file_size - bytes_left, file_size)
        file_stream.close()
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def upload_file(self, file_name: str, on_progress=None) -> None:
        file_path = os.path.join('.', file_name)
        if not os.path.isfile(file_path):
            raise Exception("[!] File not found")
        sock, _ = self.send_request(
            'upload_file', self.current_dir + [file_name])
        file_size = os.path.getsize(file_path)
        bytes_left = file_size
        sock.send(bytes(str(file_size)+(" "*(2048-len(str(file_size)))), "utf-8"))
        file_stream = open(file_path, "rb")
        while bytes_left > 0:
            buffer = file_stream.read(
                bytes_left if bytes_left < 2048 else 2048)
            sock.sendall(buffer)
            bytes_left = bytes_left - len(buffer)
            if on_progress != None:
                on_progress(file_size - bytes_left, file_size)
        file_stream.close()
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def directory_details(self, dir_path: str) -> Tuple[List[str], list]:
        sock, res = self.send_request('directory_details', dir_path)
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        return res['full_path'], res['items']

    def mkdir(self, dir_name: str) -> None:
        sock, _ = self.send_request('mkdir', self.current_dir + [dir_name])
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def delete(self, path: str) -> None:
        sock, _ = self.send_request('delete', self.current_dir + [path])
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def send_request(self, method: str, path: List[str] = ['.']) -> Tuple[socket.socket, str]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.server_addr, 1411))
        req_text = json.dumps({
            'method': method,
            'path': '/'.join(path),
        })
        sock.send(bytes(req_text+(' '*(8192-len(req_text))), "utf-8"))
        response = sock.recv(8192).decode("utf-8")
        response = json.loads(response)
        if response['status'] == 'ERROR':
            raise Exception(response['message'])
        return sock, response
