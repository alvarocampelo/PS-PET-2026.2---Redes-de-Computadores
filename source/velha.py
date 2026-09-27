#modulo do jogo da velha assincrono para o chat terminal (PET Eng. Comp. UFC)

import json
import protocol
from protocol import Mensagem

VITORIAS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8), # linhas
    (0, 3, 6), (1, 4, 7), (2, 5, 8), # colunas
    (0, 4, 8), (2, 4, 6)             # diagonais
]

def formatar_tabuleiro(tab):
    """Retorna uma string compacta de 5 linhas com o tabuleiro 3x3 formatado em cores."""
    def cor_casa(val):
        if val == "X":
            return "\033[91mX\033[0m" # Vermelho
        if val == "O":
            return "\033[96mO\033[0m" # Ciano
        return f"\033[90m{val}\033[0m" # Cinza escuro para número da casa disponível

    return (
        f"   {cor_casa(tab[0])} | {cor_casa(tab[1])} | {cor_casa(tab[2])}\n"
        f"  ---+---+---\n"
        f"   {cor_casa(tab[3])} | {cor_casa(tab[4])} | {cor_casa(tab[5])}\n"
        f"  ---+---+---\n"
        f"   {cor_casa(tab[6])} | {cor_casa(tab[7])} | {cor_casa(tab[8])}"
    )

def checar_vencedor(tab):
    """Retorna 'X', 'O', 'EMPATE' ou None se o jogo ainda está em andamento."""
    for a, b, c in VITORIAS:
        if tab[a] == tab[b] == tab[c] and tab[a] in ("X", "O"):
            return tab[a]
    if all(casa in ("X", "O") for casa in tab):
        return "EMPATE"
    return None

class JogoDaVelha:
    def __init__(self, meu_apelido):
        self.meu_apelido = meu_apelido
        self.resetar()

    def resetar(self):
        self.oponente = ""
        self.meu_simbolo = ""
        self.simbolo_oponente = ""
        self.minha_vez = False
        self.em_andamento = False
        self.desafio_pendente_de = ""
        self.tabuleiro = [str(i + 1) for i in range(9)]

    def iniciar(self, oponente, sou_desafiante):
        self.oponente = oponente
        self.em_andamento = True
        self.desafio_pendente_de = ""
        self.tabuleiro = [str(i + 1) for i in range(9)]
        if sou_desafiante:
            self.meu_simbolo = "X"
            self.simbolo_oponente = "O"
            self.minha_vez = True
        else:
            self.meu_simbolo = "O"
            self.simbolo_oponente = "X"
            self.minha_vez = False
