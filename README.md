# 🏗️ Sistema de Pedidos de Compra — Brasul Construtora

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/PySide6-Qt%20Framework-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/ReportLab-PDF%20Generator-CC0000?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/PyInstaller-Executable-4B8BBE?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
</p>

> Aplicação desktop para gestão de pedidos de compra em construção civil — substituindo planilhas e e-mails por um sistema único com PDF oficial, histórico em banco de dados, cotação comparativa entre fornecedores e operação em rede compartilhada.

**Repositório:** [github.com/Yuritborges/sistema_de_pedidos_de_compra](https://github.com/Yuritborges/sistema_de_pedidos_de_compra)

Complemento de gestão e auditoria: [Sistema de Auditoria Brasul](https://github.com/Yuritborges/sistema_auditoria_brasul) (lê o banco consolidado `cotacao_rede.db` gerado por este sistema).

---

## 📋 Sobre o Projeto

O sistema foi desenvolvido para resolver um problema real da **Brasul Construtora Ltda**: o fluxo de pedidos de compra era disperso entre planilhas, Word e e-mails, gerando inconsistências de numeração, dificuldade de rastreamento e pouca visibilidade para o financeiro e para o canteiro de obras.

A solução centraliza todo o ciclo em uma **única aplicação desktop** com:

- Geração de **PDF oficial** por empresa faturadora, com numeração sequencial única
- **Histórico completo** de pedidos com filtros, reimpressão e controle de entrega na obra
- **Cotação comparativa** lado a lado entre até 3 fornecedores
- Banco de dados compartilhado em **rede interna** (múltiplos compradores)
- Geração de **executável standalone** (sem necessidade de instalar Python nas máquinas)
- **Build na nuvem** (GitHub Actions) e publicação na rede sem depender de um PC fixo de desenvolvimento

---

## 🚀 Funcionalidades

| Módulo | Descrição |
|---|---|
| 📄 **Pedido de Compra** | Formulário validado → geração de PDF com layout por empresa faturadora |
| 📦 **Pedidos Gerados** | Consulta, filtros, status **OK na Obra** (atualização imediata na grade e no badge da sidebar), reimpressão |
| 📊 **Cotação Comparativa** | Comparação de preços entre 3 fornecedores com destaque visual |
| 🔧 **Ferramentas** | Utilitários auxiliares de importação e suporte operacional |
| 🏗️ **Locações** | Controle de equipamentos locados; ordenação por proximidade do vencimento (vencido → alerta → demais) |
| 👥 **Cadastros** | Fornecedores, obras e funcionários em JSON compartilhado |

### Melhorias recentes (operacionais)

- **PDF:** cabeçalho com logos alinhados; endereço de cobrança da Interiorana sem cortar cidade duplicada no fim do texto
- **Pedidos Gerados:** marcar **OK NA OBRA** recarrega a lista na hora (badge lateral incluído)
- **Locações:** lista ordenada por urgência de vencimento; alerta amarelo para itens a vencer em ≤ 7 dias
- **Backup diário silencioso:** `tools/backup_diario.py --silencioso` + agendamento via `tools/agendar_backup_diario.ps1` (sem janela de CMD)

---

## 🛠️ Stack Tecnológica

```
Python 3.11+       → linguagem principal
PySide6 (Qt6)      → interface gráfica desktop
SQLite             → banco de dados local e consolidado em rede
ReportLab          → geração de PDFs dos pedidos
OpenPyXL / Pandas  → exportação e análise de dados
PyInstaller        → build do executável .exe
PowerShell         → scripts de release, deploy e backup
GitHub Actions     → build Windows na nuvem (CI)
```

---

## 🗂️ Arquitetura do Projeto

```
sistema_de_pedidos_de_compra/
├── .github/workflows/
│   └── build-pedidos.yml      # CI: PyInstaller + artefato + Release (tags v*)
├── app/
│   ├── core/                  # Regras de negócio, DTOs, serviços
│   ├── data/                  # SQLite, migrações, sync com cotacao_rede.db
│   ├── infrastructure/        # PDF, imagens, relatórios
│   └── ui/                    # MainWindow, widgets, estilos
├── assets/                    # Logos, JSON de cadastros
├── database/                  # Pasta versionada (.gitkeep); .db locais ignorados
├── docs/
│   ├── BUILD_REMOTO.md        # Build na nuvem + publicação na rede
│   └── CHECKLIST_BUILD_RELEASE.md  # Checklist de 1 página
├── tools/                     # Build, backup, consolidar rede, publicar
├── main.py / main_patrao.py
├── config_exemplo.py            # Template (copiar para config.py)
├── requirements.txt
└── SistemaPedidosV2.spec
```

**Fluxo de um pedido:**
```
Formulário → PedidoService → pdf_generator (ReportLab) → SQLite → Sync rede
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

> ⚠️ `config.py` **não é versionado** — cada máquina mantém sua configuração na rede.  
> ⚠️ **Não execute** `tools/prepare_config_ci.py` no PC de produção (só no GitHub Actions).

---

## 🖥️ Instalação e Execução (modo desenvolvimento)

**Pré-requisitos:** Windows 10/11, Python 3.11+, acesso à pasta de rede (`Z:\`).

```powershell
git clone https://github.com/Yuritborges/sistema_de_pedidos_de_compra.git
cd sistema_de_pedidos_de_compra

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

copy config_exemplo.py config.py
# Edite config.py com os caminhos da sua máquina

python main.py
```

Na primeira execução, selecione o usuário na caixa de diálogo (`assets/usuarios.json`).

---

## 📦 Build e release

Há **três formas** de gerar e distribuir o `.exe`. A equipe usa o atalho em `current\SistemaPedidosV2.exe` na rede.

### Opção 1 — Tag de versão (recomendado)

Após `git commit` + `git push` em `main`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.1.2
```

- Dispara **GitHub Actions** automaticamente
- Cria **Release** no GitHub com zip nomeado (ex.: `SistemaPedidosV2-v2.1.2.zip`)
- Baixe em **Releases**, extraia em `C:\Temp`, teste o `.exe`
- Publique na rede:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SistemaPedidosV2"
```

**Versões publicadas:** use `vMAJOR.MINOR.PATCH` (ex.: `v2.1.0`). Correção → +0.0.1; função nova → +0.1.0.

### Opção 2 — Build na nuvem sem tag (teste)

GitHub → **Actions** → **Build Sistema Pedidos** → **Run workflow** (branch `main`).  
Baixe o artefato (válido 30 dias). Use **Run workflow**, não **Re-run** de execução antiga falha.

### Opção 3 — Build local na rede

```powershell
powershell -ExecutionPolicy Bypass -File tools\release_full.ps1
```

| Script | Descrição |
|---|---|
| `tag_release.ps1` | Cria tag `vX.Y.Z` e dispara CI + Release |
| `publicar_build_na_rede.ps1` | Copia build para `releases/` e `current/` |
| `release_full.ps1` | Fecha app → backup → PyInstaller → `current/` |
| `build_release.ps1` | Só build + cópia para `releases/` |
| `backup_diario.py` | Backup silencioso (`--silencioso`) |
| `consolidar_rede.py` | Merge dos `.db` dos compradores → `cotacao_rede.db` |

📄 Detalhes: [`docs/BUILD_REMOTO.md`](docs/BUILD_REMOTO.md) · [`docs/CHECKLIST_BUILD_RELEASE.md`](docs/CHECKLIST_BUILD_RELEASE.md)

---

## 🗄️ Banco de Dados

- **Banco local do comprador:** `cotacao_{comprador}.db`
- **Banco consolidado:** `cotacao_rede.db` — usado pela auditoria e relatórios
- **Locações:** `_shared/locacoes.db` — compartilhado em rede
- **`material_ok_na_obra`:** flag de entrega na obra (migrações automáticas no `init_db()`)

Consolidar antes da auditoria:

```powershell
cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
.\.venv\Scripts\python.exe tools\consolidar_rede.py
```

> Feche o sistema de pedidos nas máquinas antes de consolidar.

---

## 📁 O que versionar no Git

| Caminho | Versionar? |
|---|---|
| `app/`, `main.py`, `tools/`, `.github/` | ✅ Sim |
| `SistemaPedidosV2.spec`, `database/.gitkeep` | ✅ Sim |
| `config.py`, `*.db`, `dist/`, `current/`, `releases/` | ❌ Não |
| `assets/*.json`, `assets/logos/` | ✅ Sim |

---

## 🔗 Trabalhar sem IDE / de casa

| Você faz sozinho | Precisa de VPN / rede |
|---|---|
| Editar código, `git push` | Publicar em `current\` (`Z:`) |
| Tag → build no GitHub | Fechar `.exe` nos PCs antes do robocopy |
| Baixar zip em **Releases** | `publicar_build_na_rede.ps1` |

---

## 👨‍💻 Autor

**Yuri Borges** — Desenvolvedor do sistema no âmbito da Brasul Construtora Ltda.

[![GitHub](https://img.shields.io/badge/GitHub-Yuritborges-181717?style=flat-square&logo=github)](https://github.com/Yuritborges)

---

## 📄 Licença

Software de **uso interno** da Brasul Construtora Ltda. Não é distribuição pública genérica; reprodução fora do contexto autorizado deve seguir a política da empresa.
