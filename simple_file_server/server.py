
from lib.file_server import FileServer


f_sever = FileServer()
f_sever.start()
while True:
    if str(input("[q=stop]: ")) == "q":
        break
f_sever.stop()
