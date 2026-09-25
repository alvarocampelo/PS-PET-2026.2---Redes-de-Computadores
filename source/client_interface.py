#interface do chat aqui! conecta no servidor, manda o que for digitado e mostra o que os outros mandam.

import network #usado pra criar o socket e mandar/receber mensagens
import protocol
from protocol import Mensagem #montar/ler as mensagens em json
import threading

HOST = "127.0.0.1" #ip do servidor (troque pelo ip do pc do servidor para conversar pela rede)
PORTA = 5000 #mesma porta do servidor

def ouvir(conexao): #fica ouvindo(recebendo, procurando) as mensagens do servidor e mostrando na tela
    while True:
        try:
            texto = network.recebermensagem(conexao)
        except OSError: #no caso da conexão cair ou ser fechada (OSError já inclui ambos ConnectionResetError e ConnectionAbortedError)
            break

        if texto == "": #vazio = o servidor fechou a conexão
            break

        try:
            msg = Mensagem.de_texto(texto)
        except protocol.MensagemInvalida:
            continue

        print(msg)

    print("* conexão encerrada")

def main():
    apelido = input("Seu apelido: ").strip() or "anonimo" #nome que aparece pros outros

    conexao = network.criarsocket() #cria o socket
    conexao.connect((HOST, PORTA)) #conecta no servidor
    print(f"Conectado em {HOST}:{PORTA}. Digite /sair para sair.")

    network.mandarmensagem(conexao, Mensagem(protocol.ENTRAR, apelido).para_texto()) #avisa que entrou

    thread = threading.Thread( #executa a função ouvir paralelamente. deixa receber mensagens enquanto o usuario dtambem igita
        target=ouvir,
        args=(conexao,),
        daemon=True #a thread fecha junto com o programa
    )
    thread.start()

    while True: #loop pra mandar mensagem
        try:
            texto = input()
        except (KeyboardInterrupt, EOFError): #ctrl+c também sai
            break

        if texto == "/sair":
            break

        if texto == "":
            continue

        try:
            network.mandarmensagem(conexao, Mensagem(protocol.TEXTO, apelido, texto).para_texto())
        except OSError: #servidor caiu
            break

    try:
        network.mandarmensagem(conexao, Mensagem(protocol.SAIR, apelido).para_texto()) #avisa que saiu
    except OSError:
        pass
    conexao.close() #encerra a conexão


if __name__ == "__main__":
    main() #rodar o programa mesmo aqui