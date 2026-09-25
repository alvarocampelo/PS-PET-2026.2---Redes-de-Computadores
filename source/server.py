#servidor do chat aqui! aceita varios clientes (uma thread por cliente) e repassa as mensagens para todos.

import network #usado pra criar os sockets
import protocol
from protocol import Mensagem #mandar/receber mensagens pelo servidor
import threading 

HOST = "0.0.0.0"
PORTA = 5000 #porta tcp -> so um numero n, n>1024  pro cliente conectar

clientes = []  # cria um vetor para armazenar as conexões recebidas

def cadacliente(conexao, endereco):
    while True:
        try:
            texto = network.recebermensagem(conexao)

        except (ConnectionResetError, ConnectionAbortedError): # no caso do cliente desconectar repentinamente
            break

        if texto == "":
            break

        try:
            msg = Mensagem.de_texto(texto)
        except protocol.MensagemInvalida:
            continue

        if msg.tipo == protocol.SAIR: # se for a mensagem de saída, desconecta
            break

        print(msg)

        for cliente in clientes[:]: #manda a mensagem para todas as conexões guardadas
            if cliente != conexao:
                try:
                    network.mandarmensagem(cliente, msg.para_texto())
                except (ConnectionResetError, ConnectionAbortedError): # caso o cliente desconecte repentinamente, remover ele do vetor
                    clientes.remove(cliente)
                    cliente.close()

    print(f"{endereco} desconectou") #saida
    if conexao in clientes:
        clientes.remove(conexao) #remove a conexão desse cliente
    conexao.close() # encerra a conexão

def main():
    servidor = network.criarsocket() #cria o socket
    servidor.bind((HOST, PORTA)) #aloca a porta pro socket dado pro server
    servidor.listen() #socket fica esperando algum cliente (escutando)
    print(f"Servidor ouvindo em {HOST}:{PORTA} (Ctrl+C para parar)")

    while True: #loop pra receber mensagem aqui
        conexao, endereco = servidor.accept() # aceita o cliente, recebendo a conexão e o endereço correspondentes
        print(f"{endereco} conectou") 
        clientes.append(conexao)
        
        thread = threading.Thread( # executa a função cadacliente em paralelo. isso permite que o servidor realize a troca de mensagens, ao mesmo tempo que fica ouvindo novas conexões
            target=cadacliente, # fala qual função vai ser executada em paralelo pelo thread
            args=(conexao, endereco) # entrga os argumentos para a função cadacliente
        )
        thread.start()

    servidor.close()


if __name__ == "__main__":
    main() # rodar o programa mesmo aqui
