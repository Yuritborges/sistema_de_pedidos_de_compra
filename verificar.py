
import sqlite3
r = sqlite3.connect(r'Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db').execute('SELECT COUNT(*) FROM pedidos').fetchone()[0]
t = sqlite3.connect(r'Z:\0 OBRAS\brasul_pedidos\Thamyres\cotacao_thamyres.db').execute('SELECT COUNT(*) FROM pedidos').fetchone()[0]
print('cotacao_rede.db:', r, 'pedidos')
print('cotacao_thamyres.db:', t, 'pedidos')
