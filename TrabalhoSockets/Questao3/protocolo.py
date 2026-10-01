"""Funções compartilhadas por servidor e cliente.

Cada mensagem trafega como: [4 bytes = tamanho][JSON em UTF-8].
Isso é necessário porque o TCP é um fluxo de bytes (não preserva "fronteiras"
de mensagem): sem o tamanho, não dá para saber onde uma mensagem termina.
Arquivos são enviados logo depois do cabeçalho JSON, como bytes puros.
"""
import json
import struct

PORTA_PADRAO = 10399              # 5 primeiros dígitos da matrícula (10399)
TAMANHO_MAX_ARQUIVO = 20 * 1024 * 1024   # 20 MB


def receber_exato(sock, n):
    """Lê exatamente n bytes (recv pode devolver menos que o pedido)."""
    buffer = b""
    while len(buffer) < n:
        parte = sock.recv(min(4096, n - len(buffer)))
        if not parte:
            raise ConnectionError("conexão encerrada")
        buffer += parte
    return buffer


def enviar_msg(sock, trava, msg):
    """Envia um dicionário como JSON. A trava evita que duas threads
    escrevam no mesmo socket ao mesmo tempo e misturem os bytes."""
    dados = json.dumps(msg).encode("utf-8")
    with trava:
        sock.sendall(struct.pack("!I", len(dados)) + dados)


def receber_msg(sock):
    tamanho = struct.unpack("!I", receber_exato(sock, 4))[0]
    return json.loads(receber_exato(sock, tamanho).decode("utf-8"))
