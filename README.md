# Sistema de Pedidos — Brasul Construtora

Sistema interno de geração de pedidos de compra, cotação comparativa e controle de obras.

---

## Instalação (Windows)

### 1. Instalar Python 3.11+
Baixe em: https://www.python.org/downloads/
> Marque a opção **"Add Python to PATH"** durante a instalação.

### 2. Abrir o terminal na pasta do projeto
Clique com botão direito na pasta do projeto → "Abrir no Terminal"

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o sistema
```bash
python main.py
```

---

## Estrutura de pastas

```
sistema-de-pedido-brasul/
│
├── main.py                              ← Execute este para iniciar
├── config.py                            ← Empresas, caminhos e constantes
├── requirements.txt                     ← Dependências Python
├── .gitignore                           ← Arquivos ignorados pelo Git
│
├── app/
│   ├── core/
│   │   ├── dto/
│   │   │   └── pedido_dto.py            ← Estrutura de dados do pedido
│   │   ├── services/
│   │   │   └── pedido_service.py        ← Valida e gera o pedido
│   │   └── funcionarios.py             ← Gerencia lista de compradores
│   │
│   ├── data/
│   │   └── database.py                  ← SQLite: tabelas e backup automático
│   │
│   ├── infrastructure/
│   │   ├── pdf_generator.py             ← Gera o PDF do pedido de compra
│   │   └── relacao_pedidos_pdf.py       ← Gera PDF da relação diária de pedidos
│   │
│   └── ui/
│       ├── main_window.py               ← Janela principal + sidebar
│       ├── style.py                     ← Cores e componentes visuais
│       ├── dialogs/
│       │   └── selecionar_comprador_dialog.py
│       └── widgets/
│           ├── formulario_pedido.py     ← Tela de geração de pedido
│           ├── pedidos_widget.py        ← Pedidos do dia + impressão
│           ├── cotacao_widget.py        ← Cotação comparativa entre fornecedores
│           ├── historico_widget.py      ← Histórico e dashboard executivo
│           └── obras_widget.py          ← Cadastro de obras
│
├── assets/
│   ├── logos/                           ← Logos das empresas (.png)
│   ├── cotacoes_salvas/                 ← Cotações salvas em JSON
│   ├── obras.json                       ← Cadastro de obras
│   └── funcionarios.json               ← Lista de compradores
│
├── database/
│   ├── cotacao.db                       ← Banco SQLite (criado automaticamente)
│   └── backup/                          ← Backups semanais automáticos
│
└── pedidos_gerados/                     ← PDFs dos pedidos emitidos
```

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
| Ctrl+4 | Obras |
| Ctrl+5 | Histórico |

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

## Backup do banco de dados

O sistema faz backup automático toda semana na pasta `database/backup/`.
Os últimos 8 backups são mantidos (aproximadamente 2 meses).

Para restaurar manualmente: copie o arquivo `.db` desejado de `database/backup/` para `database/cotacao.db`.

---

## Dependências

```
PySide6       — interface gráfica
reportlab     — geração de PDF
openpyxl      — relatórios Excel
pandas        — análise de dados no histórico
matplotlib    — gráficos do dashboard
```

---

## Desenvolvido por
Yuri Borges — Brasul Construtora Ltda
