# atualizar_contador.py
# Rode este script UMA VEZ para corrigir o número do último pedido no banco.
# Depois pode apagar.
#
# Como usar:
#   1. Abra o terminal na pasta do projeto
#   2. python atualizar_contador.py
#   3. Digite o número do último pedido emitido

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.database import get_connection, init_db

init_db()

print("=" * 40)
print("ATUALIZAR CONTADOR DE PEDIDOS")
print("=" * 40)

with get_connection() as conn:
    row = conn.execute("SELECT ultimo FROM contador_pedidos WHERE id=1").fetchone()
    atual = row["ultimo"] if row else "?"
    print(f"Número atual no banco: {atual}")

numero = input("Digite o número do ÚLTIMO pedido emitido: ").strip()

try:
    n = int(numero)
    with get_connection() as conn:
        conn.execute("UPDATE contador_pedidos SET ultimo=? WHERE id=1", (n,))
    print(f"\n✅ Contador atualizado para {n}.")
    print(f"   Próximo pedido será: {n + 1}")
except ValueError:
    print("Número inválido. Nada foi alterado.")
