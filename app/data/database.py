# app/data/database.py
# Banco local com espelho automático por comprador na rede.
# Modelo:
# - Iury usa banco local e espelha para:      Z:\0 OBRAS\brasul_pedidos\Iury\cotacao_iury.db
# - Thamyres usa banco local e espelha para:  Z:\0 OBRAS\brasul_pedidos\Thamyres\cotacao_thamyres.db
# - Funciona offline: se a rede cair, o sistema continua funcionando localmente.

import os
import shutil
import sqlite3
import time
from datetime import datetime
from config import DATABASE_PATH, BACKUP_DIR, BASE_REDE_DIR


try:
    from config import COMPRADOR_PADRAO
except Exception:
    COMPRADOR_PADRAO = "IURY"


# ============================================================
# CONFIGURAÇÃO DE REDE
# ============================================================
REDE_BASE_DIR = BASE_REDE_DIR


def _normalizar_nome_comprador(nome: str) -> str:
    nome = (nome or "").strip().upper()
    if not nome:
        return "IURY"
    if nome == "YURI":
        return "IURY"
    return nome


def _nome_pasta_comprador(nome: str) -> str:
    nome = _normalizar_nome_comprador(nome)
    return nome.title()


def _nome_arquivo_db_rede(nome: str) -> str:
    nome = _normalizar_nome_comprador(nome)
    slug = "".join(ch.lower() for ch in nome if ch.isalnum()) or "usuario"
    return f"cotacao_{slug}.db"


def obter_rede_db_path() -> str:
    comprador = _normalizar_nome_comprador(COMPRADOR_PADRAO)
    pasta = _nome_pasta_comprador(comprador)
    arquivo = _nome_arquivo_db_rede(comprador)
    return os.path.join(REDE_BASE_DIR, pasta, arquivo)


REDE_DB_PATH = obter_rede_db_path()
REDE_LOCACOES_DB_PATH = os.path.join(REDE_BASE_DIR, "_shared", "locacoes.db")


# ============================================================
# CONEXÃO
# ============================================================
def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_locacoes_connection():
    """
    Banco compartilhado de locações (único para todos os usuários).
    Usa WAL + busy_timeout para reduzir conflito de escrita concorrente.
    """
    os.makedirs(os.path.dirname(REDE_LOCACOES_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(REDE_LOCACOES_DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 20000")
    return conn


def list_obras_nomes_para_locacao() -> list[str]:
    """
    Nomes de obra para o formulário de locação: cadastro de obras, pedidos, locações já salvas.
    Ordem alfabética (sem importar diferenças só de maiúsculas).
    """
    nomes: set[str] = set()
    try:
        with get_connection() as conn:
            try:
                for row in conn.execute(
                    "SELECT nome FROM obras WHERE IFNULL(ativo, 1) != 0"
                ):
                    n = (row[0] or "").strip()
                    if n:
                        nomes.add(n)
            except sqlite3.Error:
                pass
            try:
                for row in conn.execute(
                    """
                    SELECT DISTINCT TRIM(obra_nome) AS o FROM pedidos
                    WHERE obra_nome IS NOT NULL AND TRIM(obra_nome) != ''
                    """
                ):
                    n = (row[0] or "").strip()
                    if n:
                        nomes.add(n)
            except sqlite3.Error:
                pass
    except OSError:
        pass
    try:
        with get_locacoes_connection() as conn:
            for row in conn.execute(
                """
                SELECT DISTINCT TRIM(obra) AS o FROM locacoes_registros
                WHERE obra IS NOT NULL AND TRIM(obra) != ''
                """
            ):
                n = (row[0] or "").strip()
                if n:
                    nomes.add(n)
    except OSError:
        pass
    except sqlite3.Error:
        pass
    return sorted(nomes, key=lambda x: (x.upper(), x))


def list_fornecedores_nomes_para_locacao() -> list[str]:
    """
    Fornecedores para o formulário de locação: cadastro, pedidos e locações já salvas.
    """
    nomes: set[str] = set()
    try:
        with get_connection() as conn:
            try:
                for row in conn.execute(
                    "SELECT nome FROM fornecedores WHERE IFNULL(ativo, 1) != 0"
                ):
                    n = (row[0] or "").strip()
                    if n:
                        nomes.add(n)
            except sqlite3.Error:
                pass
            try:
                for row in conn.execute(
                    """
                    SELECT DISTINCT TRIM(fornecedor_nome) AS f FROM pedidos
                    WHERE fornecedor_nome IS NOT NULL AND TRIM(fornecedor_nome) != ''
                    """
                ):
                    n = (row[0] or "").strip()
                    if n:
                        nomes.add(n)
            except sqlite3.Error:
                pass
    except OSError:
        pass
    try:
        with get_locacoes_connection() as conn:
            for row in conn.execute(
                """
                SELECT DISTINCT TRIM(fornecedor) AS f FROM locacoes_registros
                WHERE fornecedor IS NOT NULL AND TRIM(fornecedor) != ''
                """
            ):
                n = (row[0] or "").strip()
                if n:
                    nomes.add(n)
    except OSError:
        pass
    except sqlite3.Error:
        pass
    return sorted(nomes, key=lambda x: (x.upper(), x))


def init_locacoes_shared_db():
    with get_locacoes_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS locacoes_registros (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                obra              TEXT,
                comprador         TEXT,
                numero_pedido     TEXT,
                fornecedor        TEXT,
                item_locado       TEXT,
                tipo              TEXT DEFAULT '',
                pedido_compra_numero TEXT DEFAULT '',
                data_pedido       TEXT,
                periodo_dias      INTEGER,
                data_vencimento   TEXT,
                dias_a_vencer     TEXT,
                situacao          TEXT,
                pedido_ok         TEXT,
                origem_planilha   TEXT,
                editando_por      TEXT,
                editando_desde    TEXT,
                versao            INTEGER DEFAULT 0,
                atualizado_em     TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_locacoes_numero
                ON locacoes_registros(numero_pedido);
            CREATE INDEX IF NOT EXISTS idx_locacoes_obra
                ON locacoes_registros(obra);
            CREATE INDEX IF NOT EXISTS idx_locacoes_comprador
                ON locacoes_registros(comprador);
            CREATE INDEX IF NOT EXISTS idx_locacoes_situacao
                ON locacoes_registros(situacao);
            CREATE INDEX IF NOT EXISTS idx_locacoes_vencimento
                ON locacoes_registros(data_vencimento);
            CREATE INDEX IF NOT EXISTS idx_locacoes_editando_por
                ON locacoes_registros(editando_por);

            CREATE TABLE IF NOT EXISTS locacoes_meta (
                chave   TEXT PRIMARY KEY,
                valor   TEXT
            );
        """)
        # Migração leve para bases compartilhadas antigas
        existentes = {r["name"] for r in conn.execute("PRAGMA table_info(locacoes_registros)")}
        if "editando_por" not in existentes:
            conn.execute("ALTER TABLE locacoes_registros ADD COLUMN editando_por TEXT")
        if "editando_desde" not in existentes:
            conn.execute("ALTER TABLE locacoes_registros ADD COLUMN editando_desde TEXT")
        if "versao" not in existentes:
            conn.execute("ALTER TABLE locacoes_registros ADD COLUMN versao INTEGER DEFAULT 0")
        if "tipo" not in existentes:
            conn.execute("ALTER TABLE locacoes_registros ADD COLUMN tipo TEXT DEFAULT ''")
        if "pedido_compra_numero" not in existentes:
            conn.execute(
                "ALTER TABLE locacoes_registros ADD COLUMN pedido_compra_numero TEXT DEFAULT ''"
            )


# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================
def init_db():
    inicio = time.perf_counter()
    tempos = []

    def marcar(etapa):
        tempos.append((etapa, time.perf_counter() - inicio))

    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    marcar("garantir-pasta-db")

    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS obras (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                nome                TEXT NOT NULL UNIQUE,
                escola              TEXT,
                faturamento         TEXT,
                endereco_entrega    TEXT,
                bairro              TEXT,
                cep                 TEXT,
                cidade              TEXT,
                uf                  TEXT DEFAULT 'SP',
                contrato_obra       TEXT DEFAULT '0',
                empreiteiro         TEXT,
                contato_empreiteiro TEXT,
                ativo               INTEGER DEFAULT 1,
                criado_em           TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS fornecedores (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nome         TEXT NOT NULL UNIQUE,
                razao_social TEXT,
                email        TEXT,
                vendedor     TEXT,
                telefone     TEXT,
                pix          TEXT,
                favorecido   TEXT,
                ativo        INTEGER DEFAULT 1,
                criado_em    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pedidos (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                numero              TEXT NOT NULL UNIQUE,
                data_pedido         TEXT,
                obra_nome           TEXT,
                escola              TEXT,
                fornecedor_nome     TEXT,
                fornecedor_razao    TEXT,
                empresa_faturadora  TEXT,
                condicao_pagamento  TEXT,
                forma_pagamento     TEXT,
                pagamento_etapas_ativo INTEGER DEFAULT 0,
                percentual_entrada  INTEGER,
                percentual_final    INTEGER,
                marco_percentual_final TEXT,
                prazo_entrega       INTEGER,
                comprador           TEXT,
                valor_total         REAL,
                caminho_pdf         TEXT,
                status              TEXT DEFAULT 'emitido',
                emitido_em          TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS itens_pedido (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id      INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
                descricao      TEXT NOT NULL,
                quantidade     REAL,
                unidade        TEXT,
                valor_unitario REAL,
                valor_total    REAL,
                categoria      TEXT
            );

            CREATE TABLE IF NOT EXISTS cotacoes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                obra_nome       TEXT,
                fornecedor_nome TEXT,
                data_cotacao    TEXT DEFAULT (datetime('now')),
                status          TEXT DEFAULT 'aberta'
            );

            CREATE TABLE IF NOT EXISTS itens_cotacao (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                cotacao_id   INTEGER NOT NULL REFERENCES cotacoes(id) ON DELETE CASCADE,
                descricao    TEXT NOT NULL,
                quantidade   REAL,
                unidade      TEXT,
                preco_f1     REAL,
                preco_f2     REAL,
                preco_f3     REAL,
                fornecedor_1 TEXT,
                fornecedor_2 TEXT,
                fornecedor_3 TEXT
            );

            CREATE TABLE IF NOT EXISTS contador_pedidos (
                id     INTEGER PRIMARY KEY CHECK (id = 1),
                ultimo INTEGER NOT NULL DEFAULT 2548
            );

            CREATE TABLE IF NOT EXISTS ferramentas_registros (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria             TEXT,
                numero_serie          TEXT,
                ferramenta            TEXT NOT NULL,
                responsavel           TEXT,
                data_saida            TEXT,
                data_devolucao        TEXT,
                obra                  TEXT,
                observacoes           TEXT,
                numero_serie_escritorio TEXT,
                foto_ref              TEXT,
                status                TEXT DEFAULT 'EM USO',
                origem_planilha       TEXT,
                atualizado_em         TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS locacoes_registros (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                obra              TEXT,
                comprador         TEXT,
                numero_pedido     TEXT,
                fornecedor        TEXT,
                item_locado       TEXT,
                tipo              TEXT DEFAULT '',
                pedido_compra_numero TEXT DEFAULT '',
                data_pedido       TEXT,
                periodo_dias      INTEGER,
                data_vencimento   TEXT,
                dias_a_vencer     TEXT,
                situacao          TEXT,
                pedido_ok         TEXT,
                origem_planilha   TEXT,
                atualizado_em     TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_ferramentas_saida
                ON ferramentas_registros(data_saida);
            CREATE INDEX IF NOT EXISTS idx_ferramentas_status
                ON ferramentas_registros(status);
            CREATE INDEX IF NOT EXISTS idx_ferramentas_obra
                ON ferramentas_registros(obra);
            CREATE INDEX IF NOT EXISTS idx_ferramentas_responsavel
                ON ferramentas_registros(responsavel);
            CREATE INDEX IF NOT EXISTS idx_locacoes_numero
                ON locacoes_registros(numero_pedido);
            CREATE INDEX IF NOT EXISTS idx_locacoes_obra
                ON locacoes_registros(obra);
            CREATE INDEX IF NOT EXISTS idx_locacoes_comprador
                ON locacoes_registros(comprador);
            CREATE INDEX IF NOT EXISTS idx_locacoes_situacao
                ON locacoes_registros(situacao);
            CREATE INDEX IF NOT EXISTS idx_locacoes_vencimento
                ON locacoes_registros(data_vencimento);
            CREATE INDEX IF NOT EXISTS idx_pedidos_emitido_em
                ON pedidos(emitido_em);
            CREATE INDEX IF NOT EXISTS idx_pedidos_obra_emitido_em
                ON pedidos(obra_nome, emitido_em);
            CREATE INDEX IF NOT EXISTS idx_pedidos_fornecedor_emitido_em
                ON pedidos(fornecedor_nome, emitido_em);

            INSERT OR IGNORE INTO contador_pedidos (id, ultimo) VALUES (1, 2548);
        """)
        _garantir_colunas_pagamento_etapas(conn)
    marcar("schema-e-migracoes")

    print(f"[DB] Banco inicializado: {DATABASE_PATH}")
    print(f"[REDE] Espelho configurado para: {REDE_DB_PATH}")

    _fazer_backup_se_necessario()
    marcar("backup-semanal")
    sincronizar_com_rede(silencioso=True)
    marcar("sincronizar-rede")
    init_locacoes_shared_db()
    marcar("locacoes-shared-init")

    try:
        from app.data.locacoes_import import tentar_sincronizar_planilha_locacoes_no_startup

        tentar_sincronizar_planilha_locacoes_no_startup()
        marcar("locacoes-sync-planilha")
    except Exception as e:
        print(f"[Locações] Aviso: sincronização automática da planilha ignorada: {e}")

    try:
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        log_path = os.path.join(base, "startup_v2.log")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        linhas = [f"[Database.init_db] {agora}"]
        anterior = 0.0
        for etapa, acumulado in tempos:
            delta = acumulado - anterior
            linhas.append(f"{etapa:24s} +{delta:7.3f}s  total={acumulado:7.3f}s")
            anterior = acumulado
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n".join(linhas) + "\n")
    except Exception:
        pass


def _garantir_colunas_pagamento_etapas(conn):
    """
    Migração leve para bases antigas que ainda não têm os campos
    estruturados de pagamento em etapas.
    """
    colunas = {
        "pagamento_etapas_ativo": "ALTER TABLE pedidos ADD COLUMN pagamento_etapas_ativo INTEGER DEFAULT 0",
        "percentual_entrada": "ALTER TABLE pedidos ADD COLUMN percentual_entrada INTEGER",
        "percentual_final": "ALTER TABLE pedidos ADD COLUMN percentual_final INTEGER",
        "marco_percentual_final": "ALTER TABLE pedidos ADD COLUMN marco_percentual_final TEXT",
    }
    existentes = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(pedidos)").fetchall()
    }
    for nome, sql in colunas.items():
        if nome not in existentes:
            conn.execute(sql)


# ============================================================
# CONTADOR DE PEDIDOS
# ============================================================
def proximo_numero_pedido():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT ultimo FROM contador_pedidos WHERE id = 1"
        ).fetchone()

        proximo = (row["ultimo"] if row else 2548) + 1
        return str(proximo)


def incrementar_numero_pedido():
    with get_connection() as conn:
        conn.execute(
            "UPDATE contador_pedidos SET ultimo = ultimo + 1 WHERE id = 1"
        )


def atualizar_numero_pedido(numero):
    try:
        n = int(numero)
        with get_connection() as conn:
            conn.execute(
                "UPDATE contador_pedidos SET ultimo = ? WHERE id = 1",
                (n,)
            )
        print(f"[DB] Contador atualizado para {n}")
    except Exception as e:
        print(f"[DB] Erro ao atualizar contador: {e}")


def atualizar_numero_pedido_se_maior(numero):
    """
    Atualiza o contador apenas se o número informado for maior que o atual.
    Evita regressão ao regerar pedidos antigos.
    """
    try:
        n = int(numero)
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE contador_pedidos
                   SET ultimo = CASE WHEN ultimo < ? THEN ? ELSE ultimo END
                 WHERE id = 1
                """,
                (n, n)
            )
        print(f"[DB] Contador verificado com base no pedido {n}")
    except Exception as e:
        print(f"[DB] Erro ao atualizar contador (se maior): {e}")


# ============================================================
# SINCRONIZAÇÃO PARA A REDE
# ============================================================
def sincronizar_com_rede(silencioso=True):
    """
    Se o banco principal já está na rede, não copia nada.
    Evita corromper ou tentar espelhar o arquivo nele mesmo.
    """
    if not REDE_DB_PATH:
        return False

    try:
        origem = os.path.abspath(DATABASE_PATH).lower()
        destino = os.path.abspath(REDE_DB_PATH).lower()

        if origem == destino:
            if not silencioso:
                print("[REDE] Banco principal já está na rede. Sincronização ignorada.")
            return True

        pasta_rede = os.path.dirname(REDE_DB_PATH)
        os.makedirs(pasta_rede, exist_ok=True)

        if not os.path.exists(DATABASE_PATH):
            if not silencioso:
                print("[REDE] Banco local ainda não existe para sincronizar.")
            return False

        shutil.copy2(DATABASE_PATH, REDE_DB_PATH)

        if not silencioso:
            print(f"[REDE] Banco espelhado com sucesso em: {REDE_DB_PATH}")

        return True

    except Exception as e:
        if not silencioso:
            print(f"[REDE] Aviso ao sincronizar: {e}")
        return False


# ============================================================
# BACKUP LOCAL
# ============================================================
def _fazer_backup_se_necessario():
    if not os.path.exists(DATABASE_PATH):
        return

    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)

        semana = datetime.now().strftime("%Y-W%W")
        nome = f"cotacao_backup_{semana}.db"
        caminho = os.path.join(BACKUP_DIR, nome)

        if not os.path.exists(caminho):
            shutil.copy2(DATABASE_PATH, caminho)
            print(f"[DB] Backup criado: {caminho}")
            _limpar_backups_antigos()

    except Exception as e:
        print(f"[DB] Aviso no backup: {e}")


def _limpar_backups_antigos():
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith("cotacao_backup_") and f.endswith(".db")
        ])

        for antigo in backups[:-8]:
            os.remove(os.path.join(BACKUP_DIR, antigo))

    except Exception:
        pass


# ============================================================
# APOIO / DIAGNÓSTICO
# ============================================================
def info_ambiente_banco():
    return {
        "comprador_padrao": _normalizar_nome_comprador(COMPRADOR_PADRAO),
        "database_local": DATABASE_PATH,
        "database_rede": REDE_DB_PATH,
        "rede_base_dir": REDE_BASE_DIR,
    }

def obter_pasta_rede_usuario():
    comprador = _normalizar_nome_comprador(COMPRADOR_PADRAO)
    pasta = _nome_pasta_comprador(comprador)
    return os.path.join(REDE_BASE_DIR, pasta)


def copiar_arquivo_para_rede(caminho_origem, subpasta):
    try:
        base = obter_pasta_rede_usuario()
        destino_dir = os.path.join(base, subpasta)
        os.makedirs(destino_dir, exist_ok=True)

        nome = os.path.basename(caminho_origem)
        destino = os.path.join(destino_dir, nome)

        shutil.copy2(caminho_origem, destino)
        print(f"[REDE] Arquivo copiado: {destino}")
    except Exception as e:
        print(f"[REDE] Erro ao copiar arquivo: {e}")