"""
criar_indices.py
----------------
Cria índices no banco para acelerar a abertura da aba Pedidos Gerados.
Execute UMA VEZ em cada banco (Iury e Thamyres).

    python criar_indices.py
"""

import sqlite3
import os
from config import DATABASE_PATH

def main():
    if not os.path.exists(DATABASE_PATH):
        print(f"ERRO: Banco não encontrado em:\n  {DATABASE_PATH}")
        input("\nPressione Enter para sair...")
        return

    print(f"Criando índices em: {DATABASE_PATH}\n")

    conn = sqlite3.connect(DATABASE_PATH)

    indices = [
        # Pedidos — colunas mais consultadas
        ("idx_pedidos_comprador",      "CREATE INDEX IF NOT EXISTS idx_pedidos_comprador      ON pedidos (comprador)"),
        ("idx_pedidos_data",           "CREATE INDEX IF NOT EXISTS idx_pedidos_data           ON pedidos (data_pedido)"),
        ("idx_pedidos_numero",         "CREATE INDEX IF NOT EXISTS idx_pedidos_numero         ON pedidos (CAST(numero AS INTEGER) DESC)"),
        ("idx_pedidos_empresa",        "CREATE INDEX IF NOT EXISTS idx_pedidos_empresa        ON pedidos (empresa_faturadora)"),
        ("idx_pedidos_obra",           "CREATE INDEX IF NOT EXISTS idx_pedidos_obra           ON pedidos (obra_nome)"),
        ("idx_pedidos_fornecedor",     "CREATE INDEX IF NOT EXISTS idx_pedidos_fornecedor     ON pedidos (fornecedor_nome)"),
        ("idx_pedidos_comp_data",      "CREATE INDEX IF NOT EXISTS idx_pedidos_comp_data      ON pedidos (comprador, data_pedido)"),
        # Itens — join com pedidos
        ("idx_itens_pedido_id",        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_id        ON itens_pedido (pedido_id)"),
    ]

    for nome, sql in indices:
        try:
            conn.execute(sql)
            print(f"  [OK] {nome}")
        except Exception as e:
            print(f"  [ERRO] {nome}: {e}")

    # Otimiza o banco depois de criar os índices
    print("\nOtimizando banco...")
    conn.execute("ANALYZE")
    conn.commit()
    conn.close()

    print("\n" + "="*50)
    print("Índices criados com sucesso!")
    print("A aba Pedidos Gerados vai abrir bem mais rápido agora.")
    print("="*50)
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()