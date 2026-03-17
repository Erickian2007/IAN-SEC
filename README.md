# 🔐 Cryptian

> Cofre de senhas pessoal — offline, terminal, sem servidor, sem nuvem.

```
 ██████╗██████╗ ██╗   ██╗██████╗ ████████╗██╗ █████╗ ███╗   ██╗
██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██║██╔══██╗████╗  ██║
██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║███████║██╔██╗ ██║
██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║██╔══██║██║╚██╗██║
╚██████╗██║  ██║   ██║   ██║        ██║   ██║██║  ██║██║ ╚████║
 ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

---

## Por que offline?

Gerenciadores online como LastPass ou Bitwarden são convenientes, mas carregam riscos estruturais:

- Em 2022, o LastPass foi hackeado — dados de milhões de usuários vazaram
- Você depende da empresa continuar existindo
- Você depende da internet para acessar suas próprias senhas
- Você confia cegamente na implementação criptográfica deles

O Cryptian resolve isso de forma diferente: **o cofre vive na sua máquina**. Nenhum servidor. Nenhuma conta. Nenhuma dependência externa. Se alguém roubar o arquivo `.json`, não consegue nada sem a sua senha mestra — matematicamente.

---

## Como funciona

O Cryptian usa uma cadeia de três camadas de segurança:

```
sua senha mestra (humana, memorável)
        │
        ▼
  PBKDF2-HMAC-SHA256
  600.000 iterações + salt aleatório
        │
        ▼
  chave de 256 bits (inquebrável na força bruta)
        │
        ▼
  AES-256-GCM + nonce aleatório
        │
        ▼
  dado cifrado (ilegível sem a chave)
        │
        ▼
  salvo em ~/.cryptian.json
```

### PBKDF2 + Salt

Sua senha humana é fraca por natureza. O PBKDF2 aplica o SHA-256 **600.000 vezes em loop**, tornando cada tentativa de força bruta cara computacionalmente — o que leva milissegundos para você leva anos para um atacante testando bilhões de combinações.

O salt é um número aleatório de 16 bytes gerado na hora, único para cada entrada. Isso garante que duas senhas idênticas produzam resultados completamente diferentes — eliminando ataques por rainbow table.

### AES-256-GCM

O AES-256 é o padrão adotado pelo governo americano para dados classificados. Com 256 bits de chave, existem mais combinações possíveis do que átomos no universo observável. O modo GCM adiciona autenticação — se alguém alterar um único bit do arquivo cifrado, a descriptografia falha imediatamente.

O nonce (number used once) é outro número aleatório de 12 bytes gerado por operação, garantindo que criptografar o mesmo dado duas vezes produza resultados completamente diferentes.

### Princípio de Kerckhoffs

> *"Um sistema criptográfico deve ser seguro mesmo que tudo sobre ele, exceto a chave, seja de conhecimento público."*

O código do Cryptian é aberto. Os algoritmos são públicos. A segurança está **inteiramente na sua senha mestra** — não no sigilo do sistema.

---

## Instalação

**Dependência:**
```bash
pip install cryptography
```

**Arch Linux:**
```bash
pip install cryptography --break-system-packages
```

**Clipboard automático (opcional):**
```bash
# Arch / Manjaro
sudo pacman -S xclip

# Ubuntu / Debian
sudo apt install xclip
```

**Rodar:**
```bash
python cryptian.py
```

---

## Funcionalidades

| # | Função | Descrição |
|---|--------|-----------|
| 1 | **Adicionar senha** | Criptografa e salva uma senha com nome de serviço |
| 2 | **Obter senha** | Descriptografa e copia para o clipboard automaticamente |
| 3 | **Listar entradas** | Mostra os nomes salvos (nunca as senhas) |
| 4 | **Deletar entrada** | Remove uma entrada (exige senha mestra) |
| 5 | **Gerar senha para site** | Cria senha forte e determinística a partir da sua senha humana |
| 6 | **Fazer backup** | Copia o cofre para destinos configurados |
| 7 | **Destinos de backup** | Gerencia caminhos de backup (pen drive, HD externo, nuvem) |

### Gerador de senha determinístico

A opção 5 é única: ela **não salva nada**. Usa sua senha humana + nome do serviço como entrada do PBKDF2 e gera sempre a mesma senha forte de saída.

```
senha humana + "google"  →  Xk#9mP2qL$nR7vBw4jQs
senha humana + "github"  →  3Yw@8tFnZe5hCmK1sDxA
```

Mesma senha mestra, resultados completamente diferentes por serviço. Se um site vazar, os outros continuam seguros. E você nunca precisa guardar essas senhas — pode recriar qualquer uma na hora.

---

## Backup

O arquivo `~/.cryptian.json` **pode ser copiado para qualquer lugar sem risco**. Sem a senha mestra, é lixo criptografado. Você pode jogá-lo no Google Drive, Dropbox, pen drive, e-mail — não importa.

```bash
# backup manual
cp ~/.cryptian.json /media/seu-pendrive/

# ou use a opção 6 do menu para automatizar
```

O backup automático salva com timestamp:
```
cryptian_backup_20260317_143022.json
```

---

## Segurança

**O que está protegido:**
- Cada entrada usa salt e nonce únicos — padrões são impossíveis
- A comparação de chaves usa tempo constante (`hmac.compare_digest`) — sem timing attacks
- O arquivo tem permissão `600` — só você lê e escreve
- A senha mestra nunca é salva em lugar nenhum

**O que você precisa proteger:**
- Sua senha mestra — sem ela não há recuperação
- O arquivo `~/.cryptian.json` — é seu cofre

**O que não importa se vazar:**
- O código fonte (está aqui, é público — princípio de Kerckhoffs)
- O arquivo `.json` isolado (inútil sem a senha mestra)

---

## Estrutura

```
cryptian.py          ← tudo em um arquivo, sem dependências extras além do cryptography
~/.cryptian.json     ← seu cofre (nunca vai para o repositório)
~/.cryptian_config.json  ← destinos de backup (nunca vai para o repositório)
```

---

## Filosofia

O Cryptian nasceu como um exercício de aprender criptografia do zero — entender cada peça antes de usar. Não é só uma ferramenta, é a materialização de conceitos:

- **XOR** como base de toda criptografia simétrica
- **Funções de mão única** que não têm retorno
- **Salt** contra rainbow tables
- **Iterações custosas** contra força bruta
- **Autenticação** além de confidencialidade

Se você quer entender como o Cryptian funciona por dentro, o código é intencionalmente legível e comentado.

---

## Licença

MIT — use, modifique, distribua à vontade.
