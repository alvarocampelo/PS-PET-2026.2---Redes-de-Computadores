#Entidades do chat. Não usa sockets! sockets -> network.py

import json #vamos mandar as mensagens via network.py como json
import hashlib #funções hash criptográficas (sha256) nativas do python
import base64 #codificação para tráfego seguro de bytes no json

# tipos de mensagem
ENTRAR = "entrar" #pessoa entrou no chat
SAIR = "sair" #pessoa saiu do chat
TEXTO = "texto" #pessoa mandou algum texto, tipo texto(padrao)
TIPOS = (ENTRAR, SAIR, TEXTO)

# ========================================================
# FUNÇÕES DE CRIPTOGRAFIA (E2EE - Ponta a Ponta)
# Cifra de fluxo simétrica com Keystream SHA-256 e Base64
# ========================================================

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
    def __init__(self, tipo, remetente="", conteudo=""): #atributos de mensagem(construtor da classe aqui)
        self.tipo = tipo
        self.remetente = remetente
        self.conteudo = conteudo

    def para_texto(self):
        #Mensagem -> string (formatação do obj mensagem para enviar)
        #o json é em bytes, aí o sockets conseguem enviar!

        return json.dumps({
            "tipo": self.tipo,
            "remetente": self.remetente,
            "conteudo": self.conteudo,
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
        )

    def cifrar(self, chave):
        if self.tipo == TEXTO and chave:
            self.conteudo = cifrar(self.conteudo, chave)
        return self

    def decifrar(self, chave):
        if self.tipo == TEXTO and chave:
            self.conteudo = decifrar(self.conteudo, chave)
        return self

    def __str__(self): #formatando print(Mensagem)

        #a formatação depende do tipo de mensagem, ai a gente testa e vê como formatar

        if self.tipo == TEXTO:
            return f"{self.remetente}: {self.conteudo}"
        if self.tipo == ENTRAR:
            return f"* {self.remetente} entrou"
        if self.tipo == SAIR:
            return f"* {self.remetente} saiu"
        return f"* {self.conteudo}"


class Cliente: #classe cliente(usuário)
    def __init__(self, conexao, endereco, apelido=""):
        self.conexao = conexao
        self.endereco = endereco #(ip, porta)
        self.apelido = apelido #tipo oi nick

    def __str__(self): #formata print(CLiente)
        ip, porta = self.endereco
        return self.apelido or f"{ip}:{porta}"