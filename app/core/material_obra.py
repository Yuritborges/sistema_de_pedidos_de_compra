# Migrações e regras de persistência para «OK na obra» (flag material_ok_na_obra + carimbo material_entregue_em).


def migrar_coluna_material_entregue_em_sqlite(conn) -> None:
    """Garante pedidos.material_entregue_em (carimbo texto / ISO). Bases antigas só tinham a flag."""
    existentes = {r[1] for r in conn.execute("PRAGMA table_info(pedidos)").fetchall()}
    if "material_entregue_em" in existentes:
        return
    conn.execute("ALTER TABLE pedidos ADD COLUMN material_entregue_em TEXT")


def migrar_coluna_material_ok_na_obra_sqlite(conn) -> None:
    """
    Garante a coluna pedidos.material_ok_na_obra (0/1).
    Não copia de material_entregue_em — isso gerava «verde fantasma».
    Só o botão «OK NA OBRA» grava 1.
    """
    existentes = {r[1] for r in conn.execute("PRAGMA table_info(pedidos)").fetchall()}
    if "material_ok_na_obra" in existentes:
        return
    conn.execute(
        "ALTER TABLE pedidos ADD COLUMN material_ok_na_obra INTEGER NOT NULL DEFAULT 0"
    )


def migracao_uma_vez_zera_flags_ok_obra_sqlite(conn) -> None:
    """
    Uma vez por arquivo SQLite: zera material_ok_na_obra em todos os pedidos.
    Corrige bases já migradas com a lógica antiga que copiava flag a partir do carimbo ISO.
    O texto em material_entregue_em não é apagado (só deixa de pintar verde sem o botão).
    """
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='_brasul_ok_obra_flags_reset_v1'"
    ).fetchone()
    if row:
        return
    conn.execute(
        "CREATE TABLE _brasul_ok_obra_flags_reset_v1 (x INTEGER PRIMARY KEY CHECK (x = 1))"
    )
    conn.execute("INSERT INTO _brasul_ok_obra_flags_reset_v1 VALUES (1)")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(pedidos)").fetchall()}
    if "material_ok_na_obra" in cols:
        conn.execute("UPDATE pedidos SET material_ok_na_obra = 0")


def migracao_uma_vez_ok_legado_todos_pedidos_sqlite(conn) -> None:
    """
    Uma vez por banco (release): marca todos os pedidos já existentes como OK na obra.
    Pedidos novos (INSERT após esta migração) continuam com material_ok_na_obra = 0 até o botão.
    Preenche material_entregue_em só quando estiver vazio (carimbo para PDF).
    """
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='_brasul_ok_obra_legado_todos_v1'"
    ).fetchone()
    if row:
        return
    conn.execute(
        "CREATE TABLE _brasul_ok_obra_legado_todos_v1 (x INTEGER PRIMARY KEY CHECK (x = 1))"
    )
    conn.execute("INSERT INTO _brasul_ok_obra_legado_todos_v1 VALUES (1)")
    migrar_coluna_material_entregue_em_sqlite(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(pedidos)").fetchall()}
    if "material_ok_na_obra" not in cols:
        return
    conn.execute(
        """
        UPDATE pedidos
           SET material_ok_na_obra = 1,
               material_entregue_em = CASE
                 WHEN material_entregue_em IS NULL
                   OR TRIM(CAST(material_entregue_em AS TEXT)) = ''
                 THEN datetime('now')
                 ELSE material_entregue_em
               END
        """
    )
