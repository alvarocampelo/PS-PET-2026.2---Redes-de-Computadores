#Entidades do chat. Não usa sockets! sockets -> network.py

import json #vamos mandar as mensagens via network.py como json

# tipos de mensagem
ENTRAR = "entrar" #pessoa entrou no chat
SAIR = "sair" #pessoa saiu do chat
TEXTO = "texto" #pessoa mandou algum texto, tipo texto(padrao)
TIPOS = (ENTRAR, SAIR, TEXTO)

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