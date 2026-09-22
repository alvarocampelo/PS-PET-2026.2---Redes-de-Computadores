#servidor do chat aqui! aceita varios clientes (uma thread por cliente) e repassa as mensagens para todos.

import network #usado pra criar os sockets
import protocol
from protocol import Mensagem #mandar/receber mensagens pelo servidor

HOST = "0.0.0.0"
PORTA = 5000 #porta tcp -> so um numero n, n>1024  pro cliente conectar

def main():
    servidor = network.criarsocket() #cria o socket
    servidor.bind((HOST, PORTA)) #aloca a porta pro socket dado pro server
    servidor.listen() #socket fica esperando algum cliente (escutando)
    print(f"Servidor ouvindo em {HOST}:{PORTA} (Ctrl+C para parar)")

    conexao, endereco = servidor.accept()
    print(f"{endereco} conectou") #confirmação do server criado

    while True: #loop pra receber mensagem aqui
        texto = network.recebermensagem(conexao)
        if texto == "sair":
            break
        try:
            msg = Mensagem.de_texto(texto)
        except protocol.MensagemInvalida:
            continue  #ignora mensagem quebrada e segue esperando a prox
        print(msg)  # usa o __str__ da msg da vez (entrou, saiu, texto padrao)

    print(f"{endereco} desconectou") #saida
    conexao.close() #termina o server
    servidor.close()


if __name__ == "__main__":
    main() # rodar o programa mesmo aqui