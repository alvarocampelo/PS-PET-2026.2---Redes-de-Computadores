#Entidades do chat. Não usa sockets —> o network.py cuida disso.

import json


# tipos de mensagem
ENTRAR = "entrar"
SAIR = "sair"
TEXTO = "texto"


class Mensagem:
    def __init__(self, tipo, remetente="", conteudo=""):
        self.tipo = tipo
        self.remetente = remetente
        self.conteudo = conteudo

    def para_texto(self):
        #Mensagem -> string (preparação para enviar)
        return json.dumps({
            "tipo": self.tipo,
            "remetente": self.remetente,
            "conteudo": self.conteudo,
        }, ensure_ascii=False)

    @classmethod
    def de_texto(cls, texto):
        """String recebida -> Mensagem."""
        dados = json.loads(texto)
        return cls(
            tipo=dados["tipo"],
            remetente=dados.get("remetente", ""),
            conteudo=dados.get("conteudo", ""),
        )

    def __str__(self):
        if self.tipo == TEXTO:
            return f"{self.remetente}: {self.conteudo}"
        if self.tipo == ENTRAR:
            return f"* {self.remetente} entrou"
        if self.tipo == SAIR:
            return f"* {self.remetente} saiu"
        return f"* {self.conteudo}"


class Cliente:
    def __init__(self, conexao, endereco, apelido=""):
        self.conexao = conexao
        self.endereco = endereco# (ip, porta)
        self.apelido = apelido

    def __str__(self):
        ip, porta = self.endereco
        return self.apelido or f"{ip}:{porta}"