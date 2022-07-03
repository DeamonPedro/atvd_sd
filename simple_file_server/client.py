import sys
from lib.file_server_client import FileServerClient
from termcolor import colored
from tabulate import tabulate
import readline
from utils import printProgressBar


client = FileServerClient()


def print_dir_items(path: str = None) -> None:
    if path == None:
        path = client.current_dir
    _, items = client.directory_details(path)
    rows = []
    for item_data in items:
        if item_data['type'] == 'dir':
            rows.append(
                [colored(f'{item_data["name"]}/', color='blue', attrs=['underline']), '',  ''])
        elif item_data['type'] == 'file':
            rows.append([colored(f'{item_data["name"]}', color='cyan'),
                         item_data["size"], 'bytes'])
    print(tabulate(rows, headers=['Name', 'Size', 'Unit']))


def print_help():
    rows = []
    for cmd in commands:
        cmd_data = commands[cmd]
        rows.append([cmd, cmd_data[0], cmd_data[1]])
    print(tabulate(rows, headers=['Command', 'Params', 'Description']))


def start_process(prefix: str, func, path: str) -> None:
    func(path, lambda progress, total: printProgressBar(progress, total, prefix=prefix,
         fill=colored('█', 'green'), void_fill=colored('█', 'white'), length=50, decimals=0))


commands = {
    'ls': ['<DIR?>', 'lista arquivos do diretório atual', print_dir_items],
    'cd': ['<DIR>', 'altera o diretório atual', client.change_directory],
    'mkdir': ['<DIR>', 'cria um diretório', client.mkdir],
    'del': ['<DIR|FILE>', 'deleta um arquivo ou diretório', client.delete],
    'upload': ['<FILE>', 'envia um arquivo para o servidor', lambda path: start_process(' Upload', client.upload_file, path)],
    'download': ['<FILE>', 'solicitar um arquivo pro servidor', lambda path: start_process(' Download', client.download_file, path)],
    'help': [None, 'exibe a lista de comandos', print_help],
    'exit': [None, 'encerra o client', lambda: sys.exit(0)],


}

while True:
    if len(client.current_dir) > 3:
        pwd = '…'+'/'.join(client.current_dir[-3:])
    else:
        pwd = '/'.join(client.current_dir)
    prompt = f'[{colored(pwd,color="blue",attrs=["underline"])}] ➤ '
    command = input(prompt)
    cmd_words = command.strip().split(' ')
    if cmd_words[0] == '':
        continue
    else:
        cmd_name = cmd_words[0]
        if cmd_name in commands:
            param_info, description, command_func = commands[cmd_name]
            try:
                if len(cmd_words) == 1 and (param_info is None or param_info.__contains__('?')):
                    command_func()
                elif len(cmd_words) == 2:
                    command_func(cmd_words[1])
                else:
                    print(colored(f'[!] Invalid command: {command}', 'red'))
                    continue
            except Exception as err:
                print(colored(f'[!] {err.args[0]}', 'red'))
        else:
            print(colored(f'[!] Command not found: {cmd_name}', 'red'))
