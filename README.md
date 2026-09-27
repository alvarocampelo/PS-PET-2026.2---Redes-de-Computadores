# PET-CHAT - PS PET Eng. Comp. UFC 2026.2

Projeto do **Grupo Roxo** para o processo seletivo do PET Eng. Comp. UFC (2026.2), **Tema 6: Redes de Computadores**.

Um sistema de troca de mensagens em tempo real pelo terminal, com um servidor central que aceita múltiplos clientes simultâneos via **sockets TCP**, usando um protocolo próprio baseado em JSON e mensagens com criptografia ponta a ponta simples.

## Como funciona

- O **servidor** fica escutando conexões e mantém uma lista de clientes conectados. Cada cliente é atendido em sua própria *thread*, e toda mensagem recebida é retransmitida (broadcast) para os demais.
- Cada **cliente** abre uma conexão com o servidor, informa um apelido e uma chave de sala e passa a enviar/receber mensagens. Uma *thread* separada fica só ouvindo o que chega, enquanto a *thread* principal cuida do que o usuário digita, assim dá pra receber mensagens sem travar a digitação.
- As mensagens trafegam como JSON (`{"tipo": ..., "remetente": ..., "conteudo": ..., "destinatario": ...}`), com cinco tipos possíveis: entrada na sala, saída da sala, texto, privado (whisper entre dois usuários) e jogo (sincronização das jogadas do jogo da velha).
- Se os dois lados combinarem uma **chave de sala**, o conteúdo das mensagens de texto é cifrado antes de sair do cliente e decifrado só por quem tem a mesma chave — uma forma simples de criptografia ponta a ponta (o servidor nunca vê o texto em claro).
- Cada apelido ganha uma cor própria no terminal (gerada a partir de um hash SHA-256, sem precisar de bibliotecas externas), o que facilita identificar quem está falando.
- Além do chat público, dá pra mandar mensagem privada só pra uma pessoa (`/privado`), trocar a chave da sala sem precisar reconectar (`/chave`), salvar o histórico da conversa num arquivo (`/salvar`) e até desafiar alguém pra uma partida de jogo da velha dentro do próprio chat (`/velha`).

## Estrutura dos arquivos

| Arquivo | O que faz |
|---|---|
| `source/network.py` | Camada de transporte. Só sabe criar sockets TCP/IPv4 e enviar/receber bytes brutos (`send`/`recv`). Não conhece o formato das mensagens — é usado tanto pelo cliente quanto pelo servidor. |
| `source/protocol.py` | Camada de aplicação/protocolo. Define a classe `Mensagem` (tipo, remetente, conteúdo, destinatário) e a conversão entre objeto e JSON, os tipos de mensagem (`entrar`, `sair`, `texto`, `privado`, `jogo`), a classe `Cliente`, as funções de criptografia (`cifrar`/`decifrar`, cifra de fluxo com keystream SHA-256) e a geração de uma cor exclusiva por apelido (`cor_do_usuario`). Não depende de sockets. |
| `source/server.py` | O servidor. Aceita conexões, cria uma thread por cliente conectado (`cadacliente`), recebe as mensagens de cada um e retransmite (broadcast) para todos os outros — inclusive as privadas e as do jogo da velha, que cada cliente filtra pelo campo `destinatario`. Mantém a lista de clientes ativos e o apelido de cada um, e avisa a sala quando alguém sai. |
| `source/client_interface.py` | O cliente / interface do usuário no terminal. Conecta no servidor, pede apelido e chave da sala, mostra o logo, e roda em paralelo uma thread que escuta mensagens (`ouvir`) e o loop principal de digitação. Suporta os comandos `/sair`, `/limpar`, `/privado`, `/chave`, `/salvar` e `/velha`. No Windows, se relança sozinho numa janela de terminal própria. |
| `source/velha.py` | Lógica do jogo da velha jogado dentro do chat: desenha o tabuleiro, define as trincas de vitória, verifica vencedor/empate e guarda o estado (tabuleiro, símbolo, de quem é a vez) de uma partida entre dois clientes. |
## Como rodar

Requer apenas Python 3 (usa só bibliotecas padrão — `socket`, `json`, `threading`, `hashlib`, `base64`).

1. Em um terminal, inicie o servidor:
```bash
   python source/server.py
```

2. Em outro(s) terminal(is), inicie um ou mais clientes:
```bash
   python source/client_interface.py
```
   No Windows, isso já abre uma janela/aba de terminal nova pra cada cliente automaticamente, não precisa abrir os terminais na mão. Em outras plataformas, roda no terminal atual.

3. Informe um apelido e, opcionalmente, uma chave de sala (se todos os clientes usarem a mesma chave, as mensagens de texto trafegam cifradas entre eles).

4. Para conectar a um servidor em outra máquina da rede, troque a constante `HOST` em `client_interface.py` pelo IP do computador que está rodando o servidor.

Comandos disponíveis no chat: `/sair` (desconecta), `/limpar` (limpa a tela), `/privado <apelido> <mensagem>` (mensagem privada cifrada, também aceita `/w`), `/chave <nova_chave>` (troca a chave de criptografia da sala sem reconectar) e `/salvar [arquivo]` (exporta o histórico da conversa pra um .txt). Também dá pra jogar: `/velha <apelido>` desafia alguém, e durante a partida usa-se `/aceitar`, `/recusar`, `/casa <1-9>` e `/desistir`.

## Observações

- A criptografia implementada é educacional: cifra o conteúdo das mensagens apenas para outros usuários e servidor, mas não inclui verificação de integridade (não detecta mensagens adulteradas em rede).
- Por padrão o servidor escuta em `0.0.0.0:5000` e o cliente conecta em `127.0.0.1:5000` (mesma máquina); ajuste conforme a rede usada.

---
Desenvolvido para o processo seletivo do PET Eng. Comp. UFC - 2026.2.
Equipe:
- Álvaro Mendonça Vasconcelos Nunes Campelo
- Marília Mascarenhas Ribeiro
- Paulo Ícaro Matias Franco
