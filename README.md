# Sistema de Pedidos — Brasul Construtora

Sistema interno de geração de pedidos de compra, cotação comparativa e controle de obras.

---

## Instalação (Windows)

### 1. Instalar Python
Use **Python 3.11 ou superior** (recomendado uma versão estável LTS). Baixe em: https://www.python.org/downloads/

> Marque a opção **"Add Python to PATH"** durante a instalação.

### 2. Abrir o terminal na pasta do projeto
Clique com botão direito na pasta do projeto → "Abrir no Terminal"

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar `config.py`
Copie `config_exemplo.py` para `config.py`, defina `COMPRADOR_PADRAO`, `PASTA_COMPRADOR` e os caminhos de rede/pastas conforme o ambiente.

### 5. Executar o sistema
```bash
python main.py
```

---

## Build do executável (rede)

Para gerar o `SistemaPedidosV2.exe` em `current/` (atalhos da rede):

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

Feche o programa em todos os PCs antes do fim do script. Se a cópia para `current/` falhar (arquivo em uso), rode:

```powershell
powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1
```

---

## Estrutura de pastas

```
sistema_de_pedidos_brasulv2/
│
├── main.py                    ← Entrada principal (desenvolvimento)
├── config_exemplo.py          ← Modelo para criar config.py (não usar o nome em produção)
├── config.py                  ← Criado localmente (não versionado): caminhos e empresas
├── SistemaPedidosV2.spec      ← PyInstaller (build Release)
├── requirements.txt
├── tools/                     ← backup_pre_release, backup_diario, build_release, sync rede
├── current/                   ← Saída do build (exe na rede; não versionar)
├── releases/                  ← Histórico de builds (não versionar)
├── backups/                   ← Snapshots manuais pre_release (não versionar)
│
├── app/
│   ├── core/                  ← DTOs, pedido_service, funcionarios
│   ├── data/                  ← database.py, locacoes_import, cotacao_rede_sync, cadastros_store
│   ├── infrastructure/        ← PDFs (pedido, relação)
│   └── ui/                    ← main_window, widgets por aba
│
├── assets/                    ← logos, funcionarios.json, obras.json
├── database/                  ← SQLite local (não versionar em produção)
└── pedidos_gerados/           ← PDFs emitidos (não versionar)
```

Principais widgets de interface: `formulario_pedido`, `pedidos_widget`, `cotacao_widget`, `ferramentas_widget`, `locacoes_widget`, `cadastros_widget`, `historico_widget`, `obras_widget`, `consulta_patrao_widget` (visão consolidada).

---

## Funcionalidades

### Pedido de Compra
- Geração de PDF com layout profissional para 5 empresas faturadoras
- Numeração automática e sequencial de pedidos
- Campos completos: obra, fornecedor, itens, condições de pagamento

### Pedidos Gerados
- Lista todos os pedidos emitidos com filtros por data e empresa
- Impressão da Relação de Pedidos para o financeiro (PDF)
- Recarrega automaticamente ao acessar a aba

### Cotação Comparativa
- Compara até 3 fornecedores item a item
- Destaque automático: verde = mais barato, vermelho = mais caro
- Análise de negociação: identifica itens onde o concorrente foi mais barato
- Gera texto de negociação pronto para copiar ou enviar por WhatsApp
- Salva e carrega cotações em JSON

### Ferramentas
- Utilitários internos (importações, manutenção, apoio operacional).

### Locações
- Controle de itens locados (banco compartilhado na rede), situação na obra, vencimentos e exportação.

### Cadastros
- Manutenção de dados auxiliares usados pelo sistema.

### Histórico
- Dashboard com totais, obras ativas e ticket médio
- Gráfico mensal de pedidos
- Filtros encadeados por ano, empresa, obra e busca por texto

### Obras
- Cadastro completo com endereço de entrega
- Empresa faturadora associada (preenchimento automático nos pedidos)

---

## Atalhos de teclado

| Atalho | Aba |
|--------|-----|
| Ctrl+1 | Pedido de Compra |
| Ctrl+2 | Pedidos Gerados |
| Ctrl+3 | Cotação |
| Ctrl+4 | Ferramentas |
| Ctrl+5 | Locações |
| Ctrl+6 | Cadastros |

> **Obras:** cadastro em **Cadastros → Obras**. O módulo **Histórico** (`historico_widget.py`) existe no repositório, mas **não está na barra lateral** desta versão do `main_window` — confira se outro fluxo ou build ainda o utiliza.

---

## Configurações em `config.py`

| Parâmetro | O que faz |
|-----------|-----------|
| `COMPRADOR_PADRAO` | Nome padrão no campo Comprador |
| `EMPRESAS_FATURADORAS` | Dados de cada empresa (endereço, logo, cor, observação padrão) |
| `PEDIDOS_DIR` | Pasta onde os PDFs são salvos |
| `COTACOES_DIR` | Pasta onde as cotações JSON são salvas |
| `BACKUP_DIR` | Pasta dos backups semanais do banco |

> O número do último pedido é controlado exclusivamente pelo banco de dados (`contador_pedidos`). Não edite manualmente.

---

## Logos das empresas

Coloque os arquivos na pasta `assets/logos/`:

| Arquivo | Empresa |
|---------|---------|
| `logo_brasul.png` | Brasul Construtora |
| `logo_jb.png` | JB Construções |
| `logo_bb.png` | B&B Engenharia |
| `logo_interiorana.png` | Interiorana |
| `logo_interbras.png` | Interbras |

> Tamanho recomendado: 200×80 px, fundo branco ou transparente.

---

## Backup do banco de dados e da rede

- **Automático (semana):** o app mantém cópias na pasta de backup configurada em `config.py` / `database` local, conforme `database.py`.
- **Antes de release / manutenção:** na raiz do projeto, com a rede disponível:

```bash
python tools/backup_pre_release.py
```

Esse script grava em `backups/pre_release_<data>/`: zip do código-fonte, cópia do banco local (via `config.py`), pasta de backups do comprador, espelhos de `cotacao_iury.db`, `cotacao_thamyres.db`, `cotacao_rede.db`, `locacoes.db` e pasta `cadastros_compartilhados` em `Z:\0 OBRAS\brasul_pedidos\` quando acessíveis.

- **Agendado:** `tools/backup_diario.py` (ajuste agendador do Windows conforme a política da empresa).

Para restaurar manualmente um `.db` local: copie o arquivo desejado para o caminho apontado por `DATABASE_PATH` no `config.py`.

---

## Dependências

```
PySide6       — interface gráfica
reportlab     — geração de PDF
openpyxl      — relatórios Excel
pandas        — ferramentas / relatórios tabulares
matplotlib    — gráficos (histórico, quando integrado)
```

---

## Desenvolvido por
Yuri Borges — Brasul Construtora Ltda
