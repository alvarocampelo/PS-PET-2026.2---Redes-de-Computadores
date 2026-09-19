import socket

def criarsocket():
  return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def mandarmensagem(conexao, mensagem):
  conexao.send(mensagem.encode("utf-8"))

def recebermensagem(conexao):
  return conexao.recv(1024).decode("utf-8")
