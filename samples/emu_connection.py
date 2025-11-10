from src.modules.emu import Emu

def onConnect():
    print("connected!")

emu = Emu("127.0.0.1", 14555)
emu.set_on_connect(onConnect)

emu.start_comms()

emu.send_log("normal log message", "normal")
emu.send_log("warning log message", "warning")
emu.send_log("error log message", "error")
