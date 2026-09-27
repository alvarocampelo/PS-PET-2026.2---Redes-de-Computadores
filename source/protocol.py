#Entidades do chat. Não usa sockets! sockets -> network.py

import json #vamos mandar as mensagens via network.py como json
import hashlib #funções hash criptográficas (sha256) nativas do python
import base64 #codificação para tráfego seguro de bytes no json
import colorsys #conversão de matiz (hls) para rgb para gerar cores vibrantes dinâmicas

# tipos de mensagem
ENTRAR = "entrar" #pessoa entrou no chat
SAIR = "sair" #pessoa saiu do chat
TEXTO = "texto" #pessoa mandou algum texto, tipo texto(padrao)
PRIVADO = "privado" #mensagem privada (whisper) para um usuario especifico
JOGO = "jogo" #pacote de sincronização do jogo da velha ponto a ponto
TIPOS = (ENTRAR, SAIR, TEXTO, PRIVADO, JOGO)

# cores ansi para o terminal
RESET = "\033[0m"
AMARELO = "\033[93m" # avisos do sistema (entrou, saiu, troca de chave)
VERMELHO = "\033[91m" # mensagens com erro de decifragem
ROXO = "\033[1;38;2;138;43;226m" # logo PET-CHAT em roxo real TrueColor (RGB 138, 43, 226)

def cor_do_usuario(nome):
    """
    Gera uma cor ANSI TrueColor (RGB 24-bit) exclusiva e determinística para cada usuário.
    Usa o SHA-256 do nome espalhado pelo círculo cromático HSL (0° a 359°),
    com luminosidade e saturação calibradas para máxima nitidez no fundo escuro.
    """
    if not nome:
        return RESET
    digest = hashlib.sha256(nome.encode("utf-8")).digest()
    h_val = int.from_bytes(digest, "big")
    hue = (h_val % 360) / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.65, 0.85)
    ir, ig, ib = int(r * 255), int(g * 255), int(b * 255)
    return f"\033[38;2;{ir};{ig};{ib}m"

# FUNÇÕES DE CRIPTOGRAFIA (E2EE - Ponta a Ponta)
# Cifra de fluxo simétrica com Keystream SHA-256 e Base64
def _gerar_keystream(chave, tamanho):
    bloco = 0
    stream = bytearray()
    while len(stream) < tamanho:
        bloco_bytes = hashlib.sha256(f"{chave}:{bloco}".encode("utf-8")).digest()
        stream.extend(bloco_bytes)
        bloco += 1
    return stream[:tamanho]

def cifrar(texto, chave):
    if not chave or not texto:
        return texto
    dados = b"PET!" + texto.encode("utf-8")
    keystream = _gerar_keystream(chave, len(dados))
    cifrado = bytes([b ^ k for b, k in zip(dados, keystream)])
    return base64.b64encode(cifrado).decode("utf-8")

def decifrar(texto_cifrado, chave):
    if not chave or not texto_cifrado:
        return texto_cifrado
    try:
        cifrado = base64.b64decode(texto_cifrado.encode("utf-8"), validate=True)
        keystream = _gerar_keystream(chave, len(cifrado))
        original = bytes([b ^ k for b, k in zip(cifrado, keystream)])
        if not original.startswith(b"PET!"):
            return "[Mensagem criptografada - chave incorreta]"
        return original[4:].decode("utf-8")
    except Exception:
        return "[Mensagem criptografada - chave incorreta]"

class MensagemInvalida(ValueError):
    """O texto recebido não é uma mensagem válida do protocolo.""" #tratamento de mensagem invalida -> uso depois

class Mensagem:#classe mensagem
    def __init__(self, tipo, remetente="", conteudo="", destinatario=""): #atributos de mensagem(construtor da classe aqui)
        self.tipo = tipo
        self.remetente = remetente
        self.conteudo = conteudo
        self.destinatario = destinatario

    def para_texto(self):
        #Mensagem -> string (formatação do obj mensagem para enviar)
        #o json é em bytes, aí o sockets conseguem enviar!

        return json.dumps({
            "tipo": self.tipo,
            "remetente": self.remetente,
            "conteudo": self.conteudo,
            "destinatario": self.destinatario,
        }, ensure_ascii=False)

    @classmethod #exclusivo da classe
    def de_texto(cls, texto):
        #json recebido, pra quem foi, precisa voltar a ser uma mensagem, esse metodo transforma de volta de json para o obj mensagem
        try:
            dados = json.loads(texto)
            tipo = dados["tipo"]
        except (json.JSONDecodeError, KeyError, TypeError):
            raise MensagemInvalida(f"mensagem inválida: {texto!r}")
        if tipo not in TIPOS:
            raise MensagemInvalida(f"tipo desconhecido: {tipo!r}")
        return cls(
            tipo=tipo,
            remetente=dados.get("remetente", ""),
            conteudo=dados.get("conteudo", ""),
            destinatario=dados.get("destinatario", ""),
        )

    def cifrar(self, chave):
        if self.tipo in (TEXTO, PRIVADO, JOGO) and chave:
            self.conteudo = cifrar(self.conteudo, chave)
        return self

    def decifrar(self, chave):
        if self.tipo in (TEXTO, PRIVADO, JOGO) and chave:
            self.conteudo = decifrar(self.conteudo, chave)
        return self

    def __str__(self): #formatando print(Mensagem)

        #a formatação depende do tipo de mensagem com cores ANSI

        if self.tipo == TEXTO:
            cor = cor_do_usuario(self.remetente)
            conteudo = f"{VERMELHO}{self.conteudo}{RESET}" if "chave incorreta" in self.conteudo else self.conteudo
            return f"{cor}{self.remetente}{RESET}: {conteudo}"
        if self.tipo == PRIVADO:
            cor = cor_do_usuario(self.remetente)
            conteudo = f"{VERMELHO}{self.conteudo}{RESET}" if "chave incorreta" in self.conteudo else self.conteudo
            return f"[PRIVADO de {cor}{self.remetente}{RESET}]: {conteudo}"
        if self.tipo == ENTRAR:
            return f"{AMARELO}* {self.remetente} entrou{RESET}"
        if self.tipo == SAIR:
            return f"{AMARELO}* {self.remetente} saiu{RESET}"
        return f"* {self.conteudo}"


class Cliente: #classe cliente(usuário)
    def __init__(self, conexao, endereco, apelido=""):
        self.conexao = conexao
        self.endereco = endereco #(ip, porta)
        self.apelido = apelido #tipo oi nick

    def __str__(self): #formata print(CLiente)
        ip, porta = self.endereco
        return self.apelido or f"{ip}:{porta}"
