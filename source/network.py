import socket #importando a biblioteca socket

def criarsocket(): # essa função cria o socket; quando for chamada, vai retornar um socket, com protocolo TCP, e com tipo de endereço IPv4
  return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def mandarmensagem(conexao, mensagem): # essa função recebe a conexão e a mensagem do usuário, e envia para o outro usuário conectado. "utf-8" garante que os bytes serão convertidos para texto.
  conexao.send(mensagem.encode("utf-8"))

def recebermensagem(conexao): # essa função recebe apenas a conexão, e retorna a mensagem recebida por ela
  return conexao.recv(1024).decode("utf-8")
