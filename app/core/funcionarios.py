# app/core/funcionarios.py
# Gerencia a lista de compradores salvos em assets/funcionarios.json

import os
import json
from app.data.cadastros_store import FUNCIONARIOS_JSON as _JSON

# Funcionários criados na primeira vez que o sistema rodar
_PADRAO = ["IURY", "THAMYRES"]


def _carregar():
    try:
        with open(_JSON, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(n).strip().upper() for n in data if str(n).strip()]
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[funcionarios] erro ao carregar: {e}")
    return list(_PADRAO)


def _salvar(lista):
    os.makedirs(os.path.dirname(_JSON), exist_ok=True)
    with open(_JSON, 'w', encoding='utf-8') as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


def listar():
    return sorted(_carregar())


def adicionar(nome):
    nome = nome.strip().upper()
    if not nome:
        return False
    func = _carregar()
    if nome in func:
        return False
    func.append(nome)
    _salvar(sorted(func))
    return True


def remover(nome):
    nome = nome.strip().upper()
    func = _carregar()
    if nome not in func:
        return False
    func.remove(nome)
    _salvar(func)
    return True
