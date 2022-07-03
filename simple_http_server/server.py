import json
from os import read
from socket import *
from urllib.parse import urlparse
from urllib.parse import parse_qs

SERVER_HOST = 'localhost'
SERVER_PORT = 80

VERSION = 'HTTP/1.1'


contact_list = [
    {
        'name': 'Kevin Rodrigues Rocha',
        'gender': 'Masculino',
        'email': 'kevin.rocha@geradornv.com.br',
        'nickname': 'kevin2311',
        'phone_number': '(83) 3033-9408',
        'birth_date': '10/11/2001'
    },
    {
        'name': 'Camille Santana Giacomini',
        'gender': 'Feminino',
        'email': 'camille.giacomini@geradornv.com.br',
        'nickname': 'cGiacomini',
        'phone_number': '(87) 2870-4821',
        'birth_date': '11/08/1939'
    },
    {
        'name': 'André Felix Pontes',
        'gender': 'Masculino',
        'email': 'andre.pontes@geradornv.com.br',
        'nickname': 'aFp2020',
        'phone_number': '(44) 2536-6542',
        'birth_date': '12/09/1992'
    }
]


def readFile(fileName):
    file = open(path, 'rb')
    outputBytes = file.read()
    file.close()
    return outputBytes


serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((SERVER_HOST, SERVER_PORT))
serverSocket.listen(1)
print('[+] server is running...')

while True:

    clientConnection, clientAddress = serverSocket.accept()
    request = clientConnection.recv(8192).decode()
    print('[+] request - ' + request.split('\n')[0])
    try:
        reqInfo = request.split('\n')[0].split(' ')
        if len(reqInfo) < 3:
            raise Exception(400, 'Error: Dad Request')
        method = reqInfo[0]
        path = reqInfo[1]
        httpVersion = reqInfo[2]
        if not method in ['GET']:
            raise Exception(405, 'Error: Method Not Allowed')

        if path[:4] == '/api':
            if path[4:14] == '/register?':
                query = parse_qs(path[14:])
                contact_list.append(query)
                res = 'HTTP/1.1 301 Moved Permanent\nAccept: */*\nLocation: http:\\\\localhost\\index.html'
                clientConnection.send(res.encode())
                clientConnection.close()
                continue
            elif path[4:] == '/contacts':
                json_res = json.dumps(contact_list).encode()
                clientConnection.send(json_res)
                clientConnection.close()
                continue
            else:
                raise Exception(404, 'Error: Endpoint Not Found')

        if path[-1] == '/':
            path += 'index.html'
        if path[0] == '/':
            path = path[1:]

        print(path)

        try:
            outputBytes = readFile(path)
        except Exception:
            raise Exception(404, 'Error: Not Found')

        response = f'{VERSION} 200 OK\n\n'
        clientConnection.send(response.encode())
        clientConnection.send(outputBytes)
        clientConnection.close()

    except Exception as error:
        code, message = error.args
        response = f'{VERSION} {code} {message}\n\n'
        clientConnection.send(response.encode())
        clientConnection.close()
