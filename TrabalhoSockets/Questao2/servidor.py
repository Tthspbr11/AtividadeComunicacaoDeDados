import socket

HOST = "0.0.0.0"   # aceita conexões de qualquer interface da máquina
PORTA = 10399      # 5 primeiros dígitos da matrícula (10399)

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # permite reiniciar rápido na mesma porta
servidor.bind((HOST, PORTA))
servidor.listen(1)
print(f"Servidor aguardando cliente na porta {PORTA}...")

conn, addr = servidor.accept()
print("Cliente conectado:", addr)
print("Digite QUIT para encerrar o chat.\n")

while True:
    # 1) espera a mensagem do cliente
    dados = conn.recv(1024)
    if not dados:                       # cliente fechou a conexão sem avisar
        print("Cliente desconectou.")
        break
    mensagem = dados.decode("utf-8")
    print("Cliente:", mensagem)
    if mensagem.strip().upper() == "QUIT":
        print("Cliente encerrou o chat.")
        break

    # 2) responde ao cliente
    resposta = input("Você: ")
    conn.send(resposta.encode("utf-8"))
    if resposta.strip().upper() == "QUIT":
        print("Chat encerrado por você.")
        break

conn.close()
servidor.close()
