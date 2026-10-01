"""Servidor da sala de chat: uma thread por cliente conectado."""
import json
import socket
import struct
import threading
import protocolo as p

HOST = "0.0.0.0"
PORTA = p.PORTA_PADRAO

clientes = {}                      # nome -> (socket, trava_de_envio)
trava_clientes = threading.Lock()  # protege o dicionário 'clientes'


def enviar_para(nome, msg, dados_arquivo=None):
    """Envia mensagem (e opcionalmente os bytes de um arquivo) a um usuário."""
    with trava_clientes:
        destino = clientes.get(nome)
    if destino is None:
        return False
    sock, trava = destino
    try:
        if dados_arquivo is None:
            p.enviar_msg(sock, trava, msg)
        else:
            with trava:  # cabeçalho + bytes sem ninguém "furar a fila"
                cab = json.dumps(msg).encode("utf-8")
                sock.sendall(struct.pack("!I", len(cab)) + cab + dados_arquivo)
        return True
    except OSError:
        return False


def todos_menos(nome):
    with trava_clientes:
        return [n for n in clientes if n != nome]


def tratar_cliente(conn, addr):
    nome = None
    trava_envio = threading.Lock()
    try:
        # 1) primeiro pacote deve ser "entrar" com o nome escolhido
        msg = p.receber_msg(conn)
        nome = str(msg.get("nome", "")).strip()
        with trava_clientes:
            if not nome or nome.lower() == "todos" or nome in clientes:
                p.enviar_msg(conn, trava_envio, {"tipo": "erro", "texto": "Nome inválido ou já em uso."})
                nome = None
                return
            clientes[nome] = (conn, trava_envio)
        p.enviar_msg(conn, trava_envio, {"tipo": "info", "texto": f"Bem-vindo, {nome}!"})
        print(f"[+] {nome} entrou ({addr[0]}:{addr[1]}). Online: {len(clientes)}")
        for outro in todos_menos(nome):
            enviar_para(outro, {"tipo": "info", "texto": f"{nome} entrou na sala."})

        # 2) laço principal: trata os pedidos deste cliente
        while True:
            msg = p.receber_msg(conn)
            tipo = msg.get("tipo")

            if tipo == "msg":
                texto, para = msg["texto"], msg.get("para", "todos")
                if para == "todos":
                    for outro in todos_menos(nome):
                        enviar_para(outro, {"tipo": "msg", "de": nome, "texto": texto, "privada": False})
                elif not enviar_para(para, {"tipo": "msg", "de": nome, "texto": texto, "privada": True}):
                    enviar_para(nome, {"tipo": "erro", "texto": f"Usuário '{para}' não está online."})

            elif tipo == "arquivo":
                tamanho, arquivo, para = msg["tam"], msg["nome"], msg.get("para", "todos")
                dados = p.receber_exato(conn, tamanho)   # SEMPRE consome os bytes do fluxo
                if tamanho > p.TAMANHO_MAX_ARQUIVO:
                    enviar_para(nome, {"tipo": "erro", "texto": "Arquivo acima do limite de 20 MB."})
                    continue
                destinos = todos_menos(nome) if para == "todos" else [para]
                entregues = [d for d in destinos
                             if enviar_para(d, {"tipo": "arquivo", "de": nome, "nome": arquivo, "tam": tamanho}, dados)]
                if entregues:
                    enviar_para(nome, {"tipo": "info", "texto": f"'{arquivo}' entregue a: {', '.join(entregues)}"})
                else:
                    enviar_para(nome, {"tipo": "erro", "texto": "Nenhum destinatário disponível."})
                print(f"[arquivo] {nome} -> {entregues}: {arquivo} ({tamanho} bytes)")

            elif tipo == "listar":
                enviar_para(nome, {"tipo": "usuarios", "lista": sorted(clientes)})

            elif tipo == "sair":
                break
    except (ConnectionError, OSError, ValueError, KeyError):
        pass
    finally:
        if nome:
            with trava_clientes:
                clientes.pop(nome, None)
            print(f"[-] {nome} saiu. Online: {len(clientes)}")
            for outro in todos_menos(nome):
                enviar_para(outro, {"tipo": "info", "texto": f"{nome} saiu da sala."})
        conn.close()


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen()
    print(f"Servidor da sala de chat na porta {PORTA}. Ctrl+C para encerrar.")
    try:
        while True:
            conn, addr = servidor.accept()
            threading.Thread(target=tratar_cliente, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nEncerrando servidor.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
