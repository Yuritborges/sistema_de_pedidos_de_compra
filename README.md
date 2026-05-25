# 🏗️ Sistema de Pedidos de Compra — Brasul Construtora

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/PySide6-Qt%20Framework-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/ReportLab-PDF%20Generator-CC0000?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/PyInstaller-Executable-4B8BBE?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
</p>

> Aplicação desktop para gestão de pedidos de compra em construção civil — substituindo planilhas e e-mails por um sistema único com PDF oficial, histórico em banco de dados, cotação comparativa entre fornecedores e operação em rede compartilhada.

---

## 📋 Sobre o Projeto

O sistema foi desenvolvido para resolver um problema real da **Brasul Construtora Ltda**: o fluxo de pedidos de compra era disperso entre planilhas, Word e e-mails, gerando inconsistências de numeração, dificuldade de rastreamento e pouca visibilidade para o financeiro e para o canteiro de obras.

A solução centraliza todo o ciclo em uma **única aplicação desktop** com:

- Geração de **PDF oficial** por empresa faturadora, com numeração sequencial única
- **Histórico completo** de pedidos com filtros, reimpressão e controle de entrega na obra
- **Cotação comparativa** lado a lado entre até 3 fornecedores
- Banco de dados compartilhado em **rede interna** (múltiplos compradores)
- Geração de **executável standalone** (sem necessidade de instalar Python nas máquinas)

Complemento de gestão e auditoria: [Sistema de Auditoria Brasul](https://github.com/Yuritborges/sistema_auditoria_brasul) (lê o banco consolidado `cotacao_rede.db` gerado por este sistema).

---

## 🚀 Funcionalidades

| Módulo | Descrição |
|---|---|
| 📄 **Pedido de Compra** | Formulário validado → geração de PDF com layout por empresa faturadora |
| 📦 **Pedidos Gerados** | Consulta, filtros por data, status "OK na Obra", reimpressão e exportação |
| 📊 **Cotação Comparativa** | Comparação de preços entre 3 fornecedores com destaque visual |
| 🔧 **Ferramentas** | Utilitários auxiliares de importação e suporte operacional |
| 🏗️ **Locações** | Controle de equipamentos locados com alertas de vencimento |
| 👥 **Cadastros** | Fornecedores, obras e funcionários em JSON compartilhado |

---

## 🛠️ Stack Tecnológica

```
Python 3.11+       → linguagem principal
PySide6 (Qt6)      → interface gráfica desktop
SQLite             → banco de dados local e consolidado em rede
ReportLab          → geração de PDFs dos pedidos
OpenPyXL / Pandas  → exportação e análise de dados
PyInstaller        → build do executável .exe
PowerShell         → scripts de release e deploy
```

---

## 🗂️ Arquitetura do Projeto

O projeto segue uma arquitetura em camadas dentro de `app/`:

```
sistema_de_pedidos_de_compra/
├── app/
│   ├── core/            # Regras de negócio, DTOs, serviços (PedidoService)
│   ├── data/            # SQLite, migrações, sync com cotacao_rede.db
│   ├── infrastructure/  # Geração de PDF, imagens, relatórios
│   └── ui/              # MainWindow, widgets por módulo, estilos, diálogos
├── assets/
│   ├── logos/           # Logotipos por empresa faturadora para o PDF
│   └── *.json           # Cadastros compartilhados (obras, fornecedores)
├── tools/               # Scripts PowerShell e Python de build e release
├── main.py              # Entrada principal (seleção de comprador, splash, init)
├── main_patrao.py       # Variante com visão consolidada (perfil gestor)
├── config_exemplo.py    # Template de configuração (copiar para config.py)
├── requirements.txt
└── SistemaPedidosV2.spec  # Spec do PyInstaller
```

**Fluxo de um pedido:**
```
Formulário → PedidoService (validação) → pdf_generator (ReportLab) → SQLite → Sync rede
```

---

## ⚙️ Configuração

Copie `config_exemplo.py` para `config.py` e ajuste as variáveis:

| Variável | Função |
|---|---|
| `COMPRADOR_PADRAO` | Nome do comprador (ex.: `IURY`) |
| `PASTA_COMPRADOR` | Subpasta na rede (ex.: `Iury`) |
| `DATABASE_PATH` | Caminho do SQLite local desse comprador |
| `BASE_REDE_DIR` | Raiz da pasta de rede compartilhada |
| `PEDIDOS_DIR` / `BACKUP_DIR` | Pastas de saída e backup |
| `EMPRESAS_FATURADORAS` | Dados e logos de cada empresa para o PDF |
| `REDE_SYNC_INTERVALO_SEGUNDOS` | Sincronização periódica (0 = desligado) |

> ⚠️ `config.py` **não é versionado** (consta no `.gitignore`) — cada máquina mantém sua própria configuração.

---

## 🖥️ Instalação e Execução (modo desenvolvimento)

**Pré-requisitos:** Windows 10/11, Python 3.11+, acesso à pasta de rede.

```bash
# 1. Clone o repositório
git clone https://github.com/Yuritborges/sistema_de_pedidos_de_compra.git
cd sistema_de_pedidos_de_compra

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o sistema
copy config_exemplo.py config.py
# Edite config.py com os caminhos da sua máquina

# 5. Execute
python main.py
```

Na primeira execução, selecione o usuário na caixa de diálogo (lista em `assets/usuarios.json`).

---

## 📦 Build do Executável

Para gerar o `.exe` com PyInstaller e distribuir para as máquinas da construtora:

```powershell
# Build completo com backup pré-release
powershell -ExecutionPolicy Bypass -File tools\release_full.ps1

# Apenas build (sem atualizar current/)
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1 -SkipCurrent
```

O executável é gerado em `dist/` e copiado automaticamente para `releases/` e `current/`.

| Script | Descrição |
|---|---|
| `release_full.ps1` | Fecha app → backup → PyInstaller → copia para releases e current |
| `build_release.ps1` | Gera dist/ e copia para releases/ |
| `backup_pre_release.py` | Zip do código + cópia dos bancos SQLite |
| `consolidar_rede.py` | Merge manual dos .db de todos os compradores no consolidado |

---

## 🗄️ Banco de Dados

- **Banco local do comprador:** `cotacao_{comprador}.db` — pedidos e cotações do usuário logado
- **Banco consolidado:** `cotacao_rede.db` — merge de todos os compradores, usado por relatórios
- **Banco de locações:** `_shared/locacoes.db` — compartilhado entre todos os compradores em rede

A flag **`material_ok_na_obra`** (0/1) controla o status de entrega na obra. Migrações são executadas automaticamente no `init_db()` na inicialização.

---

## 📁 O que versionar no Git

| Caminho | Versionar? |
|---|---|
| `app/`, `main.py`, `tools/*.py` | ✅ Sim |
| `config.py` | ❌ Não (segredos e caminhos locais) |
| `assets/*.json`, `assets/logos/` | ✅ Sim |
| `dist/`, `build/`, `releases/` | ❌ Não |
| `backups/`, `*.db` | ❌ Não |

---

## 👨‍💻 Autor

**Yuri Borges** — Desenvolvedor do sistema no âmbito da Brasul Construtora Ltda.

[![GitHub](https://img.shields.io/badge/GitHub-Yuritborges-181717?style=flat-square&logo=github)](https://github.com/Yuritborges)

---

## 📄 Licença

Software de **uso interno** da Brasul Construtora Ltda. Não é distribuição pública genérica; reprodução fora do contexto autorizado deve seguir a política da empresa.
