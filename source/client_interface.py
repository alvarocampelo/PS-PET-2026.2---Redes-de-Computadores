#interface do chat aqui! conecta no servidor, manda o que for digitado e mostra o que os outros mandam.

import network #usado pra criar o socket e mandar/receber mensagens
import protocol
from protocol import Mensagem #montar/ler as mensagens em json
import threading
import os
import sys
import subprocess
import shutil
import re
import json
import velha

HOST = "127.0.0.1" #ip do servidor (troque pelo ip do pc do servidor para conversar pela rede)
PORTA = 5000 #mesma porta do servidor

LOGO_ARTE = r"""
 ______    ______      ______              ______      __  __      ______      ______
/\  == \  /\  ___\    /\__  _\    ______  /\  ___\    /\ \_\ \    /\  __ \    /\__  _\
\ \  _-/  \ \  __\    \/_/\ \/   /\_____\ \ \ \____   \ \  __ \   \ \  __ \   \/_/\ \/
 \ \_\     \ \_____\     \ \_\   \/_____/  \ \_____\   \ \_\ \_\   \ \_\ \_\     \ \_\
  \/_/      \/_____/      \/_/              \/_____/    \/_/\/_/    \/_/\/_/      \/_/
""" #o r antes faz o python não tratar as barras \ como comando tipo \n
LOGO_SUBTITULO = "                    chat pelo terminal  |  PET Eng. Comp. UFC\n"
LOGO = f"{protocol.ROXO}{LOGO_ARTE}{protocol.RESET}{LOGO_SUBTITULO}"

def ouvir(conexao, apelido, sessao, historico, jogo): #fica ouvindo as mensagens do servidor e mostrando na tela
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

        chave_atual = sessao.get("chave", "")
        msg.decifrar(chave_atual) #decifra a mensagem caso tenha chave

        # mensagens de jogo da velha são tratadas na extensão abaixo
        if msg.tipo == protocol.JOGO:
            if msg.destinatario == apelido:
                _tratar_mensagem_jogo(msg, apelido, conexao, chave_atual, jogo)
            continue

        # se for mensagem privada, só exibe se for para mim ou enviada por mim
        if msg.tipo == protocol.PRIVADO:
            if msg.destinatario != apelido and msg.remetente != apelido:
                continue

        historico.append(_limpar_ansi(msg)) #guarda no historico para o /salvar
        cor_minha = protocol.cor_do_usuario(apelido)
        # solucao limpa: volta pro inicio da linha (\r), limpa a linha inteira (\033[2K) e imprime a mensagem recebida
        print(f"\r\033[2K{msg}")
        print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True) #redesenha o prompt colorido de digitação embaixo

    print("* conexão encerrada")

def main():
    os.system("") #ativa interpretacao de caracteres ANSI no terminal do Windows (cmd/powershell)
    print(LOGO)
    apelido = input("Seu apelido: ").strip() or "anonimo" #nome que aparece pros outros
    cor_minha = protocol.cor_do_usuario(apelido) #cor exclusiva para o apelido
    chave = input("Chave da sala: ").strip() #chave para cifrar/decifrar mensagens
    sessao = {"chave": chave} #dicionario mutavel para permitir troca de chave em tempo real
    historico = [] #lista em memoria com o historico decifrado da sessao
    jogo = velha.JogoDaVelha(apelido) #instancia do jogo da velha assincrono

    conexao = network.criarsocket() #cria o socket
    try:
        conexao.connect((HOST, PORTA)) #conecta no servidor
    except OSError: #tratamento de erro caso nao consiga conectar no servidor
        print(f"Não foi possível conectar em {HOST}:{PORTA}") #msg de falha
        return
    print(f"Conectado em {HOST}:{PORTA}.")
    print("Comandos: /sair | /limpar | /privado <nome> <msg> | /velha <nome> | /chave <nova_chave> | /salvar")

    network.mandarmensagem(conexao, Mensagem(protocol.ENTRAR, apelido).para_texto()) #avisa que entrou

    thread = threading.Thread( #executa a função ouvir paralelamente. deixa receber mensagens enquanto o usuario dtambem igita
        target=ouvir,
        args=(conexao, apelido, sessao, historico, jogo),
        daemon=True #a thread fecha junto com o programa
    )
    thread.start()

    while True: #loop pra mandar mensagem
        try:
            texto = input(f"{cor_minha}{apelido}{protocol.RESET}: ") #mostra o apelido com a cor do usuario
        except (KeyboardInterrupt, EOFError): #ctrl+c tambem sai
            break

        if texto == "/sair":
            break

        if texto == "/limpar": #limpa só a tela de quem digitou, 100% estetico
            os.system("cls" if os.name == "nt" else "clear") #cls no windows, clear em linux
            print(LOGO) #pra ficar bunitin dnv
            continue

        # executa comandos adicionais (/chave, /salvar, /privado, /velha, /casa, /desistir)
        if processar_comando(texto, apelido, conexao, sessao, historico, jogo):
            continue

        if texto == "":
            continue

        try:
            historico.append(f"{apelido}: {texto}")
            network.mandarmensagem(conexao, Mensagem(protocol.TEXTO, apelido, texto).cifrar(sessao.get("chave", "")).para_texto())
        except OSError: #servidor caiu
            break

    try:
        network.mandarmensagem(conexao, Mensagem(protocol.SAIR, apelido).para_texto()) #avisa que saiu
    except OSError:
        pass
    conexao.close() #encerra a conexão

def _abrir_em_nova_janela():
    #retorna True se conseguiu abrir uma aba nova
    if os.environ.get("CHAT_JANELA_PROPRIA") == "1":
        return False #ja estamos rodando dentro da aba-> nao abre de novo

    os.environ["CHAT_JANELA_PROPRIA"] = "1" #marca pro processo saber que nao precisa abrir mais
    comando = [sys.executable, os.path.abspath(__file__)]

    try:
        if shutil.which("wt"): #windows terminal instalado-> abre como aba
            subprocess.Popen(["wt", "-w", "0", "new-tab", "--"] + comando, env=os.environ)
        else: #sem windows terminal-> abre uma aba de cmd
            subprocess.Popen(["cmd", "/c", "start", "", "cmd", "/k"] + comando, env=os.environ)
        return True
    except OSError:
        return False #nao conseguiu abrir janela nova-> roda aqui


# EXTENSÕES E RECURSOS ADICIONAIS
# Criptografia E2EE, Comandos (/privado, /chave, /salvar) e Jogo da Velha

def _limpar_ansi(texto):
    # remove sequências de escape ANSI para gravar texto limpo no arquivo
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(texto))

def _tratar_mensagem_jogo(msg, apelido, conexao, chave_atual, jogo):
    try:
        dados = json.loads(msg.conteudo)
    except (json.JSONDecodeError, ValueError):
        return

    acao = dados.get("acao")
    cor_rem = protocol.cor_do_usuario(msg.remetente)
    cor_minha = protocol.cor_do_usuario(apelido)

    if acao == "desafio":
        if jogo.em_andamento:
            resp = Mensagem(protocol.JOGO, apelido, json.dumps({"acao": "ocupado"}), destinatario=msg.remetente)
            resp.cifrar(chave_atual)
            try:
                network.mandarmensagem(conexao, resp.para_texto())
            except OSError:
                pass
        else:
            jogo.desafio_pendente_de = msg.remetente
            print(f"\r\033[2K{protocol.AMARELO}* [JOGO] {cor_rem}{msg.remetente}{protocol.AMARELO} desafiou você para um Jogo da Velha!{protocol.RESET}")
            print(f"{protocol.AMARELO}* Digite /aceitar para jogar ou /recusar para ignorar.{protocol.RESET}")
            print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True)

    elif acao == "aceitar":
        jogo.iniciar(msg.remetente, sou_desafiante=True)
        print(f"\r\033[2K{protocol.AMARELO}* [JOGO] {cor_rem}{msg.remetente}{protocol.AMARELO} aceitou o desafio! Você joga primeiro como (X).{protocol.RESET}")
        print(velha.formatar_tabuleiro(jogo.tabuleiro))
        print(f"{protocol.AMARELO}* Sua vez! Digite /casa <1-9>{protocol.RESET}")
        print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True)

    elif acao == "recusar":
        print(f"\r\033[2K{protocol.AMARELO}* [JOGO] {cor_rem}{msg.remetente}{protocol.AMARELO} recusou o seu desafio.{protocol.RESET}")
        print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True)

    elif acao == "ocupado":
        print(f"\r\033[2K{protocol.AMARELO}* [JOGO] {cor_rem}{msg.remetente}{protocol.AMARELO} já está em uma partida no momento.{protocol.RESET}")
        print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True)

    elif acao == "jogada":
        casa = dados.get("casa")
        if jogo.em_andamento and isinstance(casa, int) and 0 <= casa < 9:
            jogo.tabuleiro[casa] = jogo.simbolo_oponente
            print(f"\r\033[2K{protocol.AMARELO}* [JOGO] {cor_rem}{msg.remetente}{protocol.AMARELO} jogou na casa {casa + 1}:{protocol.RESET}")
            print(velha.formatar_tabuleiro(jogo.tabuleiro))

            vencedor = velha.checar_vencedor(jogo.tabuleiro)
            if vencedor == jogo.simbolo_oponente:
                print(f"{protocol.AMARELO}* [JOGO] Fim de partida: {cor_rem}{msg.remetente}{protocol.AMARELO} venceu!{protocol.RESET}")
                jogo.resetar()
            elif vencedor == "EMPATE":
                print(f"{protocol.AMARELO}* [JOGO] Fim de partida: Deu velha (empate)!{protocol.RESET}")
                jogo.resetar()
            else:
                jogo.minha_vez = True
                print(f"{protocol.AMARELO}* Sua vez, {cor_minha}{apelido}{protocol.AMARELO} ({jogo.meu_simbolo})! Digite /casa <1-9>{protocol.RESET}")

            print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True)

    elif acao == "desistir":
        if jogo.em_andamento:
            print(f"\r\033[2K{protocol.AMARELO}* [JOGO] {cor_rem}{msg.remetente}{protocol.AMARELO} desistiu da partida. Você venceu por W.O.!{protocol.RESET}")
            jogo.resetar()
            print(f"{cor_minha}{apelido}{protocol.RESET}: ", end="", flush=True)

def processar_comando(texto, apelido, conexao, sessao, historico, jogo):
    """
    Processa comandos especiais do chat.
    Retorna True se o texto foi um comando tratado, ou False para mensagem normal.
    """
    if texto.startswith("/chave"):
        partes = texto.split(" ", 1)
        nova_chave = partes[1].strip() if len(partes) > 1 else ""
        sessao["chave"] = nova_chave
        aviso = "[sem chave]" if not nova_chave else nova_chave
        print(f"{protocol.AMARELO}* Chave da sala alterada para: {aviso}{protocol.RESET}")
        return True

    if texto.startswith("/salvar"):
        partes = texto.split(" ", 1)
        nome_arquivo = partes[1].strip() if len(partes) > 1 and partes[1].strip() else "historico_chat.txt"
        try:
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                f.write(f"=== Histórico PET-CHAT ({apelido}) ===\n\n")
                for linha in historico:
                    f.write(linha + "\n")
            print(f"{protocol.AMARELO}* Histórico salvo com sucesso em '{nome_arquivo}' ({len(historico)} mensagens){protocol.RESET}")
        except OSError as e:
            print(f"{protocol.VERMELHO}* Erro ao salvar histórico: {e}{protocol.RESET}")
        return True

    if texto.startswith("/privado ") or texto.startswith("/w "):
        partes = texto.split(" ", 2)
        if len(partes) >= 3:
            alvo = partes[1].strip()
            conteudo = partes[2].strip()
            msg = Mensagem(protocol.PRIVADO, apelido, conteudo, destinatario=alvo)
            msg.cifrar(sessao.get("chave", ""))
            try:
                network.mandarmensagem(conexao, msg.para_texto())
                cor_alvo = protocol.cor_do_usuario(alvo)
                print(f"[PRIVADO para {cor_alvo}{alvo}{protocol.RESET}]: {conteudo}")
                historico.append(f"[PRIVADO para {alvo}]: {conteudo}")
            except OSError:
                pass
        else:
            print(f"{protocol.AMARELO}* Uso correto: /privado <apelido> <mensagem>{protocol.RESET}")
        return True

    if texto.startswith("/velha "):
        partes = texto.split(" ", 1)
        alvo = partes[1].strip() if len(partes) > 1 else ""
        if not alvo:
            print(f"{protocol.AMARELO}* Uso correto: /velha <apelido>{protocol.RESET}")
            return True
        if alvo == apelido:
            print(f"{protocol.AMARELO}* Você não pode desafiar a si mesmo!{protocol.RESET}")
            return True
        if jogo.em_andamento:
            print(f"{protocol.AMARELO}* Você já está em uma partida contra {jogo.oponente}! Use /desistir para sair.{protocol.RESET}")
            return True
        msg_desafio = Mensagem(protocol.JOGO, apelido, json.dumps({"acao": "desafio"}), destinatario=alvo)
        msg_desafio.cifrar(sessao.get("chave", ""))
        try:
            network.mandarmensagem(conexao, msg_desafio.para_texto())
            print(f"{protocol.AMARELO}* Desafio enviado para {alvo}. Aguardando resposta...{protocol.RESET}")
        except OSError:
            pass
        return True

    if texto == "/aceitar":
        if not jogo.desafio_pendente_de:
            print(f"{protocol.AMARELO}* Você não tem nenhum desafio pendente.{protocol.RESET}")
            return True
        oponente = jogo.desafio_pendente_de
        jogo.iniciar(oponente, sou_desafiante=False)
        msg_aceitar = Mensagem(protocol.JOGO, apelido, json.dumps({"acao": "aceitar"}), destinatario=oponente)
        msg_aceitar.cifrar(sessao.get("chave", ""))
        try:
            network.mandarmensagem(conexao, msg_aceitar.para_texto())
            print(f"{protocol.AMARELO}* Partida iniciada com {oponente}! Você é (O). Aguarde a jogada dele.{protocol.RESET}")
            print(velha.formatar_tabuleiro(jogo.tabuleiro))
        except OSError:
            pass
        return True

    if texto == "/recusar":
        if not jogo.desafio_pendente_de:
            print(f"{protocol.AMARELO}* Você não tem nenhum desafio pendente.{protocol.RESET}")
            return True
        oponente = jogo.desafio_pendente_de
        jogo.desafio_pendente_de = ""
        msg_recusar = Mensagem(protocol.JOGO, apelido, json.dumps({"acao": "recusar"}), destinatario=oponente)
        msg_recusar.cifrar(sessao.get("chave", ""))
        try:
            network.mandarmensagem(conexao, msg_recusar.para_texto())
            print(f"{protocol.AMARELO}* Desafio de {oponente} recusado.{protocol.RESET}")
        except OSError:
            pass
        return True

    if texto.startswith("/casa ") or texto.startswith("/c "):
        if not jogo.em_andamento:
            print(f"{protocol.AMARELO}* Você não está em nenhuma partida. Desafie alguém com /velha <nome>{protocol.RESET}")
            return True
        if not jogo.minha_vez:
            print(f"{protocol.AMARELO}* Não é sua vez! Aguarde a jogada de {jogo.oponente}.{protocol.RESET}")
            return True
        partes = texto.split()
        if len(partes) < 2 or not partes[1].isdigit():
            print(f"{protocol.AMARELO}* Digite um número de 1 a 9 (ex: /casa 5){protocol.RESET}")
            return True
        pos = int(partes[1])
        if pos < 1 or pos > 9:
            print(f"{protocol.AMARELO}* Casa inválida! Escolha entre 1 e 9.{protocol.RESET}")
            return True
        idx = pos - 1
        if jogo.tabuleiro[idx] in ("X", "O"):
            print(f"{protocol.AMARELO}* A casa {pos} já está ocupada! Escolha outra.{protocol.RESET}")
            return True

        jogo.tabuleiro[idx] = jogo.meu_simbolo
        jogo.minha_vez = False
        msg_jogada = Mensagem(protocol.JOGO, apelido, json.dumps({"acao": "jogada", "casa": idx}), destinatario=jogo.oponente)
        msg_jogada.cifrar(sessao.get("chave", ""))
        try:
            network.mandarmensagem(conexao, msg_jogada.para_texto())
            print(f"{protocol.AMARELO}* Você jogou na casa {pos}:{protocol.RESET}")
            print(velha.formatar_tabuleiro(jogo.tabuleiro))

            vencedor = velha.checar_vencedor(jogo.tabuleiro)
            if vencedor == jogo.meu_simbolo:
                print(f"{protocol.AMARELO}* [JOGO] 🎉 Parabéns! Você venceu a partida contra {jogo.oponente}!{protocol.RESET}")
                jogo.resetar()
            elif vencedor == "EMPATE":
                print(f"{protocol.AMARELO}* [JOGO] Fim de partida: Deu velha (empate)!{protocol.RESET}")
                jogo.resetar()
            else:
                print(f"{protocol.AMARELO}* Aguardando a jogada de {jogo.oponente} ({jogo.simbolo_oponente})...{protocol.RESET}")
        except OSError:
            pass
        return True

    if texto == "/desistir":
        if not jogo.em_andamento:
            print(f"{protocol.AMARELO}* Você não está em nenhuma partida.{protocol.RESET}")
            return True
        oponente = jogo.oponente
        msg_desistir = Mensagem(protocol.JOGO, apelido, json.dumps({"acao": "desistir"}), destinatario=oponente)
        msg_desistir.cifrar(sessao.get("chave", ""))
        try:
            network.mandarmensagem(conexao, msg_desistir.para_texto())
            print(f"{protocol.AMARELO}* Você desistiu da partida contra {oponente}.{protocol.RESET}")
        except OSError:
            pass
        jogo.resetar()
        return True

    return False

if __name__ == "__main__":
    if os.name == "nt" and _abrir_em_nova_janela():
        sys.exit() #esse processo fecha, o chat continua rodando na aba nova
    main() #rodar o programa mesmo aqui caso trave