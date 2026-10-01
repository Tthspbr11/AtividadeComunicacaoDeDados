"""Cliente da sala de chat: menu no terminal + thread que recebe mensagens."""
import json
import os
import socket
import struct
import sys
import threading
import protocolo as p

IP_SERVIDOR = "127.0.0.1"   # TROQUE pelo IP do computador onde roda o servidor
PORTA = p.PORTA_PADRAO
PASTA_RECEBIDOS = "recebidos"

trava_envio = threading.Lock()


def nome_livre(pasta, nome):
    """Evita sobrescrever: arquivo.txt -> arquivo (1).txt"""
    base, ext = os.path.splitext(nome)
    caminho, i = os.path.join(pasta, nome), 1
    while os.path.exists(caminho):
        caminho = os.path.join(pasta, f"{base} ({i}){ext}")
        i += 1
    return caminho


def thread_receber(sock):
    """Roda em paralelo ao menu: imprime tudo o que o servidor mandar."""
    try:
        while True:
            msg = p.receber_msg(sock)
            tipo = msg["tipo"]
            if tipo == "msg":
                marca = " (privada)" if msg["privada"] else ""
                print(f"\n[{msg['de']}{marca}] {msg['texto']}")
            elif tipo == "arquivo":
                dados = p.receber_exato(sock, msg["tam"])
                os.makedirs(PASTA_RECEBIDOS, exist_ok=True)
                # basename: impede que o remetente escolha um caminho como ../../x
                caminho = nome_livre(PASTA_RECEBIDOS, os.path.basename(msg["nome"]))
                with open(caminho, "wb") as f:
                    f.write(dados)
                print(f"\n[arquivo] {msg['de']} enviou '{msg['nome']}' ({msg['tam']} bytes) -> salvo em {caminho}")
            elif tipo == "usuarios":
                print("\nOnline:", ", ".join(msg["lista"]))
            elif tipo == "erro":
                print("\n[erro]", msg["texto"])
            else:
                print("\n[info]", msg.get("texto", ""))
    except (ConnectionError, OSError):
        print("\nConexão com o servidor encerrada. Pressione Enter para sair.")


def escolher_arquivo():
    """Mostra os arquivos da pasta atual e deixa o usuário escolher (ou digitar um caminho)."""
    arquivos = sorted(f for f in os.listdir(".") if os.path.isfile(f))
    print("\nArquivos na pasta atual:")
    for i, f in enumerate(arquivos, 1):
        print(f"  {i}) {f} ({os.path.getsize(f)} bytes)")
    print("  Ou digite o caminho completo de outro arquivo.")
    escolha = input("Escolha (número ou caminho, vazio cancela): ").strip().strip('"')
    if not escolha:
        return None
    if escolha.isdigit() and 1 <= int(escolha) <= len(arquivos):
        return arquivos[int(escolha) - 1]
    return escolha


def enviar_arquivo(sock, para):
    caminho = escolher_arquivo()
    if not caminho:
        return
    if not os.path.isfile(caminho):
        print("Arquivo não encontrado.")
        return
    tamanho = os.path.getsize(caminho)
    if tamanho > p.TAMANHO_MAX_ARQUIVO:
        print("Arquivo maior que 20 MB.")
        return
    with open(caminho, "rb") as f:
        dados = f.read()
    cab = json.dumps({"tipo": "arquivo", "nome": os.path.basename(caminho),
                      "tam": tamanho, "para": para}).encode("utf-8")
    with trava_envio:
        sock.sendall(struct.pack("!I", len(cab)) + cab + dados)
    print(f"Enviando '{os.path.basename(caminho)}'...")


MENU = """
===== MENU =====
1) Mensagem para todos
2) Mensagem privada
3) Enviar arquivo para todos
4) Enviar arquivo para um usuário
5) Listar usuários online
0) Sair
================"""


def main():
    nome = input("Seu nome de usuário: ").strip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((IP_SERVIDOR, PORTA))
    except OSError as e:
        print("Não foi possível conectar ao servidor:", e)
        sys.exit(1)
    p.enviar_msg(sock, trava_envio, {"tipo": "entrar", "nome": nome})
    threading.Thread(target=thread_receber, args=(sock,), daemon=True).start()

    try:
        while True:
            print(MENU)
            op = input("Opção: ").strip()
            if op == "1":
                p.enviar_msg(sock, trava_envio, {"tipo": "msg", "para": "todos", "texto": input("Mensagem: ")})
            elif op == "2":
                para = input("Para quem? ").strip()
                p.enviar_msg(sock, trava_envio, {"tipo": "msg", "para": para, "texto": input("Mensagem: ")})
            elif op == "3":
                enviar_arquivo(sock, "todos")
            elif op == "4":
                enviar_arquivo(sock, input("Para quem? ").strip())
            elif op == "5":
                p.enviar_msg(sock, trava_envio, {"tipo": "listar"})
            elif op == "0":
                p.enviar_msg(sock, trava_envio, {"tipo": "sair"})
                break
            else:
                print("Opção inválida.")
    except (EOFError, KeyboardInterrupt, OSError):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()
