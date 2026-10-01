import socket

IP_SERVIDOR = "127.0.0.1"  # TROQUE pelo IP do computador do servidor (se forem máquinas diferentes)
PORTA = 10399              # 5 primeiros dígitos da matrícula (10399)

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((IP_SERVIDOR, PORTA))
print("Conectado ao servidor. Digite QUIT para encerrar o chat.\n")

while True:
    # 1) o cliente fala primeiro
    mensagem = input("Você: ")
    cliente.send(mensagem.encode("utf-8"))
    if mensagem.strip().upper() == "QUIT":
        print("Chat encerrado por você.")
        break

    # 2) espera a resposta do servidor
    dados = cliente.recv(1024)
    if not dados:
        print("Servidor desconectou.")
        break
    resposta = dados.decode("utf-8")
    print("Servidor:", resposta)
    if resposta.strip().upper() == "QUIT":
        print("Servidor encerrou o chat.")
        break

cliente.close()
