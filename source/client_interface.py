#interface do chat aqui! conecta no servidor, manda o que for digitado e mostra o que os outros mandam.

import network #usado pra criar o socket e mandar/receber mensagens
import protocol
from protocol import Mensagem #montar/ler as mensagens em json
import threading
import os

HOST = "127.0.0.1" #ip do servidor (troque pelo ip do pc do servidor para conversar pela rede)
PORTA = 5000 #mesma porta do servidor

LOGO = r"""
 ______    ______      ______              ______      __  __      ______      ______
/\  == \  /\  ___\    /\__  _\    ______  /\  ___\    /\ \_\ \    /\  __ \    /\__  _\
\ \  _-/  \ \  __\    \/_/\ \/   /\_____\ \ \ \____   \ \  __ \   \ \  __ \   \/_/\ \/
 \ \_\     \ \_____\     \ \_\   \/_____/  \ \_____\   \ \_\ \_\   \ \_\ \_\     \ \_\
  \/_/      \/_____/      \/_/              \/_____/    \/_/\/_/    \/_/\/_/      \/_/

                    chat pelo terminal  |  PET Eng. Comp. UFC
""" #o r antes faz o python não tratar as barras \ como comando tipo \n

def ouvir(conexao, apelido): #fica ouvindo(recebendo, procurando) as mensagens do servidor e mostrando na tela
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

        print(f"\n{msg}") #\n pula a linha que o usuario ta escrevendo. screvendo embaixo
        #aqui foi decisao minha mesmo, ou era isso, ou msg apagava no meio quando alguem enviasse! codigo pra substituir(testar):  print(f"\r{str(msg).ljust(len(apelido) + 2)}")
        #terceira opcao é nao ter nada, mas achei muito feio, não fica evidente que está sendo esperado um texto
         
        print(f"{apelido}: ", end="", flush=True) #mostra o "apelido: " de novo embaixo, esperando novamente a mensagem

    print("* conexão encerrada")

def main():
    print(LOGO)
    apelido = input("Seu apelido: ").strip() or "anonimo" #nome que aparece pros outros

    conexao = network.criarsocket() #cria o socket
    conexao.connect((HOST, PORTA)) #conecta no servidor
    print(f"Conectado em {HOST}:{PORTA}. Digite /sair para sair.")

    network.mandarmensagem(conexao, Mensagem(protocol.ENTRAR, apelido).para_texto()) #avisa que entrou

    thread = threading.Thread( #executa a função ouvir paralelamente. deixa receber mensagens enquanto o usuario dtambem igita
        target=ouvir,
        args=(conexao,apelido),
        daemon=True #a thread fecha junto com o programa
    )
    thread.start()

    while True: #loop pra mandar mensagem
        try:
            texto = input(f"{apelido}: ") #mostra o apelido antes do que o usuario digita, pra deixar mais facil visualização
        except (KeyboardInterrupt, EOFError): #ctrl+c tambem sai
            break

        if texto == "/sair":
            break

        if texto == "/limpar": #limpa só a tela de quem digitou, 100% estetico
            os.system("cls" if os.name == "nt" else "clear") #cls no windows, clear em linux
            print(LOGO) #pra ficar bunitin dnv
            continue

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