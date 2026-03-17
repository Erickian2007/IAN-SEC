#!/usr/bin/env python3
"""
 ██████╗██████╗ ██╗   ██╗██████╗ ████████╗██╗ █████╗ ███╗   ██╗
██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██║██╔══██╗████╗  ██║
██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║███████║██╔██╗ ██║
██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║██╔══██║██║╚██╗██║
╚██████╗██║  ██║   ██║   ██║        ██║   ██║██║  ██║██║ ╚████║
 ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝

Cofre de Senhas Pessoal
Criptografia: AES-256-GCM + PBKDF2-HMAC-SHA256
"""

import os
import json
import hashlib
import base64
import getpass
import sys
import time
import threading

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("Instale a dependência: pip install cryptography")
    sys.exit(1)

# ── Arquivos ──────────────────────────────────────────────────
ARQUIVO        = os.path.expanduser("~/.cryptian.json")
ARQUIVO_CONFIG = os.path.expanduser("~/.cryptian_config.json")


# ════════════════════════════════════════════════════════════
#  CORES ANSI
# ════════════════════════════════════════════════════════════
class Cor:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    CIANO  = "\033[36m"
    BRANCO = "\033[97m"
    CINZA  = "\033[90m"

    @staticmethod
    def rgb(r, g, b, texto=""):
        return f"\033[38;2;{r};{g};{b}m{texto}\033[0m"


def _limpar():
    os.system("clear")


def _esconder_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def _mostrar_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ════════════════════════════════════════════════════════════
#  ANIMAÇÃO 1 — ABERTURA
# ════════════════════════════════════════════════════════════
_LOGO = [
    " ██████╗██████╗ ██╗   ██╗██████╗ ████████╗██╗ █████╗ ███╗   ██╗",
    "██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██║██╔══██╗████╗  ██║",
    "██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║███████║██╔██╗ ██║",
    "██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║██╔══██║██║╚██╗██║",
    "╚██████╗██║  ██║   ██║   ██║        ██║   ██║██║  ██║██║ ╚████║",
    " ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝",
]

_SUBTITULO = "Cofre de Senhas Pessoal  •  AES-256-GCM  •  PBKDF2"

_GRADIENTE = [
    (180,  80, 255),
    (150, 110, 255),
    ( 90, 160, 255),
    ( 40, 210, 255),
    (  0, 240, 220),
    ( 20, 255, 190),
]


def animacao_abertura():
    _limpar()
    _esconder_cursor()

    # logo linha a linha
    for i, linha in enumerate(_LOGO):
        r, g, b = _GRADIENTE[i % len(_GRADIENTE)]
        print(Cor.rgb(r, g, b, linha))
        time.sleep(0.07)

    # subtítulo letra a letra
    print()
    sys.stdout.write("  ")
    for ch in _SUBTITULO:
        sys.stdout.write(Cor.rgb(100, 180, 255, ch))
        sys.stdout.flush()
        time.sleep(0.022)
    print()

    # barra que se desenha da esquerda para direita
    print()
    sys.stdout.write("  ")
    for ch in "─" * 66:
        sys.stdout.write(Cor.rgb(60, 180, 255, ch))
        sys.stdout.flush()
        time.sleep(0.008)
    print("\n")

    time.sleep(0.3)
    _mostrar_cursor()


# ════════════════════════════════════════════════════════════
#  ANIMAÇÃO 2 — SPINNER (usado no PBKDF2)
# ════════════════════════════════════════════════════════════
_FRAMES_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _com_spinner(func, *args, mensagem="Processando", **kwargs):
    """
    Executa func em background, exibe spinner animado até terminar.
    Retorna o resultado de func.
    """
    resultado = [None]
    erro      = [None]

    def _executar():
        try:
            resultado[0] = func(*args, **kwargs)
        except Exception as e:
            erro[0] = e

    thread = threading.Thread(target=_executar, daemon=True)
    thread.start()

    _esconder_cursor()
    i = 0
    while thread.is_alive():
        frame = _FRAMES_SPINNER[i % len(_FRAMES_SPINNER)]
        barra_len = 24
        cheio = i % (barra_len + 1)
        barra = Cor.rgb(60, 160, 255, "█" * cheio) + Cor.CINZA + "░" * (barra_len - cheio) + Cor.RESET
        sys.stdout.write(
            f"\r  {Cor.rgb(100,200,255,frame)} "
            f"{Cor.BOLD}{mensagem}...{Cor.RESET}  {barra}"
        )
        sys.stdout.flush()
        time.sleep(0.05)
        i += 1

    thread.join()
    _mostrar_cursor()

    if erro[0]:
        sys.stdout.write(f"\r  {Cor.rgb(255,80,80,'✗')} Erro!                                        \n")
        sys.stdout.flush()
        raise erro[0]

    sys.stdout.write(
        f"\r  {Cor.rgb(80,255,160,'✓')} "
        f"{Cor.BOLD}{mensagem}{Cor.RESET} "
        f"{Cor.rgb(80,255,160,'concluído!')}                        \n"
    )
    sys.stdout.flush()
    return resultado[0]


# ════════════════════════════════════════════════════════════
#  ANIMAÇÃO 3 — BARRA DE PROGRESSO (backup)
# ════════════════════════════════════════════════════════════

def _barra_progresso(atual, total, largura=36, label=""):
    pct   = atual / total
    cheio = int(largura * pct)
    vazio = largura - cheio

    if pct < 0.5:
        r, g, b = 40, 140 + int(pct * 220), 255
    else:
        r, g, b = 40, 255, int(255 - pct * 200)

    barra = Cor.rgb(r, g, b, "█" * cheio) + Cor.CINZA + "░" * vazio + Cor.RESET
    pct_s = Cor.BOLD + f"{int(pct*100):>3}%" + Cor.RESET
    nome  = Cor.CINZA + label[-40:] + Cor.RESET if label else ""
    sys.stdout.write(f"\r  [{barra}] {pct_s}  {nome}  ")
    sys.stdout.flush()


# ════════════════════════════════════════════════════════════
#  CRIPTOGRAFIA
# ════════════════════════════════════════════════════════════

def _derivar_chave_raw(mestra: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", mestra.encode(), salt, 600_000, 32)


def derivar_chave(mestra: str, salt: bytes) -> bytes:
    """Deriva chave com spinner visual."""
    return _com_spinner(_derivar_chave_raw, mestra, salt, mensagem="Derivando chave")


def criptografar(valor: str, mestra: str) -> str:
    salt    = os.urandom(16)
    nonce   = os.urandom(12)
    chave   = derivar_chave(mestra, salt)
    cifrado = AESGCM(chave).encrypt(nonce, valor.encode(), None)
    return base64.urlsafe_b64encode(salt + nonce + cifrado).decode()


def descriptografar(pacote_str: str, mestra: str) -> str:
    raw     = base64.urlsafe_b64decode(pacote_str)
    salt    = raw[:16]
    nonce   = raw[16:28]
    cifrado = raw[28:]
    chave   = derivar_chave(mestra, salt)
    return AESGCM(chave).decrypt(nonce, cifrado, None).decode()


# ════════════════════════════════════════════════════════════
#  ARQUIVO
# ════════════════════════════════════════════════════════════

def carregar() -> dict:
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO) as f:
        return json.load(f)


def salvar(dados: dict):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f, indent=2)
    os.chmod(ARQUIVO, 0o600)


# ════════════════════════════════════════════════════════════
#  OPERAÇÕES
# ════════════════════════════════════════════════════════════

def adicionar(nome: str, senha: str, mestra: str):
    dados = carregar()
    if nome in dados:
        confirma = input(f"  '{nome}' já existe. Sobrescrever? (s/N): ").strip().lower()
        if confirma != "s":
            print("  Cancelado.")
            return
    dados[nome] = criptografar(senha, mestra)
    salvar(dados)
    print(f"  {Cor.rgb(80,255,160,'✓')} '{nome}' salvo com sucesso.")


def obter(nome: str, mestra: str) -> str | None:
    dados = carregar()
    if nome not in dados:
        print(f"  {Cor.rgb(255,80,80,'✗')} '{nome}' não encontrado.")
        return None
    try:
        return descriptografar(dados[nome], mestra)
    except Exception:
        print(f"  {Cor.rgb(255,80,80,'✗')} Senha mestra incorreta.")
        return None


def listar() -> list:
    """Exibe entradas e retorna lista ordenada de nomes."""
    dados = carregar()
    if not dados:
        print(f"  {Cor.CINZA}Cofre vazio.{Cor.RESET}")
        return []
    nomes = sorted(dados.keys())
    print(f"  {Cor.rgb(100,180,255, str(len(nomes)) + ' entrada(s) salva(s):')}\n")
    for i, nome in enumerate(nomes, 1):
        print(f"  {Cor.CINZA}{i:>2}.{Cor.RESET}  {nome}")
    return nomes


def resolver_nome(entrada: str, nomes: list) -> str:
    """Aceita número ou nome — retorna o nome real."""
    if entrada.isdigit():
        idx = int(entrada) - 1
        if 0 <= idx < len(nomes):
            return nomes[idx]
    return entrada


def deletar(nome: str, mestra: str):
    dados = carregar()
    if nome not in dados:
        print(f"  {Cor.rgb(255,80,80,'✗')} '{nome}' não encontrado.")
        return
    try:
        descriptografar(dados[nome], mestra)
    except Exception:
        print(f"  {Cor.rgb(255,80,80,'✗')} Senha mestra incorreta.")
        return
    confirma = input(f"  Tem certeza que quer deletar '{nome}'? (s/N): ").strip().lower()
    if confirma != "s":
        print("  Cancelado.")
        return
    del dados[nome]
    salvar(dados)
    print(f"  {Cor.rgb(80,255,160,'✓')} '{nome}' deletado.")


# ════════════════════════════════════════════════════════════
#  GERADOR DE SENHA
# ════════════════════════════════════════════════════════════
_ALFABETO = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*"


def gerar_senha_para_site(senha_humana: str, servico: str, tamanho: int = 20) -> str:
    salt  = servico.lower().strip().encode()
    chave = _com_spinner(
        hashlib.pbkdf2_hmac,
        "sha256", senha_humana.encode(), salt, 600_000, 64,
        mensagem="Gerando senha"
    )
    return "".join(_ALFABETO[b % len(_ALFABETO)] for b in chave)[:tamanho]


# ════════════════════════════════════════════════════════════
#  BACKUP
# ════════════════════════════════════════════════════════════

def carregar_config() -> dict:
    if not os.path.exists(ARQUIVO_CONFIG):
        return {"destinos": []}
    with open(ARQUIVO_CONFIG) as f:
        return json.load(f)


def salvar_config(config: dict):
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(ARQUIVO_CONFIG, 0o600)


def fazer_backup():
    if not os.path.exists(ARQUIVO):
        print("  Cofre vazio, nada para fazer backup.")
        return

    config   = carregar_config()
    destinos = config.get("destinos", [])

    if not destinos:
        print("  Nenhum destino configurado.")
        print("  Adicione um destino primeiro (opção 7).")
        return

    from datetime import datetime
    import shutil

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"cryptian_backup_{timestamp}.json"
    erros       = 0

    print(f"\n  Fazendo backup para {len(destinos)} destino(s)...\n")
    _esconder_cursor()

    for destino_raw in destinos:
        destino = os.path.expanduser(destino_raw)
        passos  = 30
        for p in range(passos + 1):
            _barra_progresso(p, passos, label=destino_raw)
            time.sleep(0.02)
        try:
            os.makedirs(destino, exist_ok=True)
            shutil.copy2(ARQUIVO, os.path.join(destino, nome_backup))
            os.chmod(os.path.join(destino, nome_backup), 0o600)
            print(f"  {Cor.rgb(80,255,160,'✓')} {destino_raw}")
        except Exception as e:
            print(f"  {Cor.rgb(255,80,80,'✗')} {destino_raw} — {e}")
            erros += 1

    _mostrar_cursor()

    if erros == 0:
        print(f"\n  {Cor.rgb(80,255,160,'✓ Backup concluído:')} {nome_backup}")
    else:
        print(f"\n  Backup com {erros} erro(s).")


def gerenciar_destinos():
    config   = carregar_config()
    destinos = config.get("destinos", [])

    while True:
        print(f"\n{Cor.BOLD}── Destinos de backup ──{Cor.RESET}")
        if not destinos:
            print(f"  {Cor.CINZA}Nenhum destino configurado.{Cor.RESET}")
        else:
            for i, d in enumerate(destinos, 1):
                print(f"  {Cor.CINZA}{i}.{Cor.RESET}  {d}")

        print("\n  a. Adicionar    r. Remover    v. Voltar")
        op = input("\n  Opção: ").strip().lower()

        if op == "a":
            print(f"\n  {Cor.CINZA}Exemplos:{Cor.RESET}")
            print("    /media/pendrive/backup")
            print("    ~/Dropbox/cryptian")
            print("    /mnt/hd-externo/senhas")
            novo = input("\n  Caminho: ").strip()
            if novo and novo not in destinos:
                destinos.append(novo)
                config["destinos"] = destinos
                salvar_config(config)
                print(f"  {Cor.rgb(80,255,160,'✓')} '{novo}' adicionado.")
            elif novo in destinos:
                print("  Destino já existe.")

        elif op == "r":
            if not destinos:
                print("  Nenhum destino para remover.")
                continue
            idx = input("  Número a remover: ").strip()
            try:
                removido = destinos.pop(int(idx) - 1)
                config["destinos"] = destinos
                salvar_config(config)
                print(f"  {Cor.rgb(80,255,160,'✓')} '{removido}' removido.")
            except (ValueError, IndexError):
                print("  Número inválido.")

        elif op == "v":
            break


# ════════════════════════════════════════════════════════════
#  CLIPBOARD
# ════════════════════════════════════════════════════════════

def copiar_clipboard(valor: str) -> bool:
    try:
        import subprocess
        if sys.platform.startswith("linux"):
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    proc.communicate(valor.encode())
                    return True
                except FileNotFoundError:
                    continue
        elif sys.platform == "darwin":
            subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE).communicate(valor.encode())
            return True
        elif sys.platform == "win32":
            subprocess.Popen(["clip"], stdin=subprocess.PIPE).communicate(valor.encode())
            return True
    except Exception:
        pass
    return False


# ════════════════════════════════════════════════════════════
#  INTERFACE
# ════════════════════════════════════════════════════════════

def _titulo_secao(titulo: str):
    print(f"\n{Cor.rgb(60,180,255,'─' * 4)} {Cor.BOLD}{titulo}{Cor.RESET} {Cor.rgb(60,180,255,'─' * (40 - len(titulo)))}")


def menu():
    print(f"\n{Cor.rgb(60,140,255,'╔══════════════════════════════╗')}")
    print(f"{Cor.rgb(60,140,255,'║')}  {Cor.rgb(180,80,255,'🔐')} {Cor.BOLD}{Cor.rgb(180,80,255,'C R Y P T I A N')}{Cor.RESET}           {Cor.rgb(60,140,255,'║')}")
    print(f"{Cor.rgb(60,140,255,'╠══════════════════════════════╣')}")
    opcoes = [
        ("1", "Adicionar senha"),
        ("2", "Obter senha"),
        ("3", "Listar entradas"),
        ("4", "Deletar entrada"),
        ("5", "Gerar senha p/ site"),
        ("6", "Fazer backup"),
        ("7", "Destinos de backup"),
        ("8", "Sair"),
    ]
    for num, texto in opcoes:
        n = Cor.rgb(100, 200, 255, num)
        print(f"{Cor.rgb(60,140,255,'║')}  {n}{Cor.CINZA}.{Cor.RESET} {texto:<26}{Cor.rgb(60,140,255,'║')}")
    print(f"{Cor.rgb(60,140,255,'╚══════════════════════════════╝')}")


def pedir_mestra(acao: str = "continuar") -> str:
    return getpass.getpass(f"  Senha mestra para {acao}: ")


def run():
    animacao_abertura()

    while True:
        menu()
        op = input(f"\n  {Cor.rgb(100,200,255,'›')} Opção: ").strip()

        if op == "1":
            _titulo_secao("Adicionar")
            nome = input("  Nome (ex: github, email): ").strip()
            if not nome:
                print("  Nome não pode ser vazio.")
                input("\n  [Enter para continuar]")
                continue
            senha  = getpass.getpass("  Senha a guardar: ")
            mestra = pedir_mestra("salvar")
            adicionar(nome, senha, mestra)

        elif op == "2":
            _titulo_secao("Obter")
            nomes  = listar()
            entrada = input("\n  Nome ou número: ").strip()
            nome   = resolver_nome(entrada, nomes)
            mestra = pedir_mestra("obter")
            valor  = obter(nome, mestra)
            if valor:
                if copiar_clipboard(valor):
                    print(f"  {Cor.rgb(80,255,160,'✓')} Senha copiada para o clipboard!")
                else:
                    print(f"  🔑 {nome}: {Cor.BOLD}{valor}{Cor.RESET}")
                    print(f"  {Cor.CINZA}(instale xclip: sudo pacman -S xclip){Cor.RESET}")

        elif op == "3":
            _titulo_secao("Entradas salvas")
            listar()

        elif op == "4":
            _titulo_secao("Deletar")
            nomes   = listar()
            entrada = input("\n  Nome ou número a deletar: ").strip()
            nome    = resolver_nome(entrada, nomes)
            mestra  = pedir_mestra("deletar")
            deletar(nome, mestra)

        elif op == "5":
            _titulo_secao("Gerar senha para site")
            print(f"  {Cor.CINZA}Mesma entrada → sempre mesma saída. Nada é salvo.{Cor.RESET}\n")
            servico      = input("  Serviço (ex: google, github): ").strip().lower()
            senha_humana = getpass.getpass("  Sua senha humana: ")
            tam_str      = input("  Tamanho [20]: ").strip()
            tamanho      = int(tam_str) if tam_str.isdigit() else 20
            gerada       = gerar_senha_para_site(senha_humana, servico, tamanho)
            if copiar_clipboard(gerada):
                print(f"  {Cor.rgb(80,255,160,'✓')} Senha para '{servico}' copiada para o clipboard!")
            else:
                print(f"  🔑 {servico}: {Cor.BOLD}{gerada}{Cor.RESET}")
            print(f"  {Cor.CINZA}({tamanho} caracteres){Cor.RESET}")

        elif op == "6":
            _titulo_secao("Backup")
            fazer_backup()

        elif op == "7":
            gerenciar_destinos()

        elif op == "8":
            print(f"\n  {Cor.rgb(180,80,255,'Cryptian encerrado.')} {Cor.rgb(60,140,255,'🔒')}\n")
            break

        else:
            print(f"  {Cor.CINZA}Opção inválida.{Cor.RESET}")

        input(f"\n  {Cor.CINZA}[Enter para continuar]{Cor.RESET}")


if __name__ == "__main__":
    run()