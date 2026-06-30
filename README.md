# Sistema de Pedidos de Compra — Brasul Construtora

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/PySide6-Qt%20Framework-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/ReportLab-PDF-CC0000?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/PyInstaller-Executable-4B8BBE?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
</p>

> Aplicação desktop para gestão de pedidos de compra em construção civil — substituindo planilhas e e-mails por um sistema único com PDF oficial, histórico em banco de dados, cotação comparativa, controle de locações e ferramentas, operação em rede compartilhada entre compradores.

**Repositório:** [github.com/Yuritborges/sistema_de_pedidos_de_compra](https://github.com/Yuritborges/sistema_de_pedidos_de_compra)

**Complemento de auditoria:** [Sistema de Auditoria Brasul](https://github.com/Yuritborges/sistema_auditoria_brasul) — lê o banco consolidado `cotacao_rede.db` gerado por este sistema.

---

## Sobre o Projeto

O sistema foi desenvolvido para a **Brasul Construtora Ltda** centralizar o fluxo de compras que antes era disperso entre planilhas, Word e e-mails.

Principais benefícios:

- **PDF oficial** por empresa faturadora, com numeração sequencial única
- **Histórico completo** de pedidos com filtros, reimpressão e controle de entrega na obra
- **Cotação comparativa** entre até 3 fornecedores
- **Cadastros compartilhados** na rede (fornecedores, obras, empresas faturadoras)
- **Múltiplos compradores** (Iury, Thamyres, etc.) com bancos individuais e consolidação automática
- **Executável standalone** (`SistemaPedidosV2.exe`) — não exige Python instalado nas máquinas de uso
- **Build na nuvem** (GitHub Actions) e publicação na pasta `current\` da rede

---

## Módulos do Sistema

Atalhos de teclado: **Ctrl+1** a **Ctrl+6** (ordem abaixo).

| Atalho | Aba | Função |
|--------|-----|--------|
| Ctrl+1 | **Pedido de Compra** | Formulário completo → gera PDF e grava no banco |
| Ctrl+2 | **Pedidos Gerados** | Consulta, filtros, OK na Obra, reimpressão, edição |
| Ctrl+3 | **Cotação Comparativa** | Comparação de preços entre 3 fornecedores |
| Ctrl+4 | **Ferramentas** | Controle de ferramentas da obra (saída, devolução, histórico) |
| Ctrl+5 | **Locações** | Equipamentos locados, vencimentos, vínculo com pedidos |
| Ctrl+6 | **Cadastros** | Manutenção de fornecedores e obras (JSON na rede) |

### Pedido de Compra

- Seleção de **obra** e **fornecedor** com autocomplete (cadastros da rede)
- Tabela de itens (descrição, quantidade, unidade, valor, total)
- **Desconto** em % ou R$ com conversão automática
- Condição e forma de pagamento; observações livres
- **Empresas faturadoras:** botões BRASUL, B&B, INTERIORANA, INTERBRAS (e outras cadastradas)
  - **＋** cadastrar nova empresa
  - **✏** editar dados (endereço de cobrança, razão social, logo, etc.)
  - **🗑** excluir empresa (**BRASUL** não pode ser removida — empresa principal)
- **Salvar / Carregar rascunho** de pedido em andamento
- Geração de PDF em `pdfs de pedidos\` na pasta do comprador na rede
- Sincronização **em tempo real** com a aba Cadastros ao salvar fornecedor/obra

### Pedidos Gerados

- Listagem paginada com filtros por data, obra, fornecedor, empresa faturadora
- Filtros de entrega: hoje, atrasados, período customizado
- **OK NA OBRA** — marca entrega; linha verde; badge de alerta na sidebar
- Reimpressão de PDF, exportação, abrir pasta de pedidos
- **Editar pedido** — reabre o formulário com dados carregados
- **Relação de pedidos do dia** — PDF consolidado para impressão
- Exclusão de pedido (com confirmação)

### Cotação Comparativa

- Até **3 fornecedores** lado a lado na mesma planilha
- Itens com quantidade, unidade e preços por fornecedor
- Frete e desconto por fornecedor
- Dashboard com totais e destaque do melhor preço
- Vinculação à obra; salvamento em JSON na pasta do comprador
- Empresa faturadora de referência

### Ferramentas

- Controle de ferramentas conforme planilha padrão Brasul
- Registro por categoria, número de série, obra, responsável
- **Nova saída para obra**, devolução, histórico de movimentações
- Importação da planilha Excel padrão
- Cards: total, em uso, devolvido
- Filtro por categoria

### Locações

- Banco compartilhado `locacoes.db` na rede
- Cadastro de locações com tipo, obra, fornecedor, datas e valores
- **Vínculo com pedido** — ao digitar nº do pedido, preenche obra, fornecedor, itens
- Alertas visuais: **vencido** (vermelho), **a vencer em ≤ 3 dias** (amarelo)
- Ordenação por urgência de vencimento
- Importação automática da planilha `LOCAÇÕES - LANÇAMENTO.xlsm` (configurável)
- Sidebar pisca quando há locações vencidas ou próximas do vencimento

### Cadastros

- **Fornecedores:** nome, razão social, e-mail, vendedor, telefone, PIX, dados bancários
- **Obras:** endereço, faturamento, escola, contrato, empreiteiro, contato
- Dados gravados em JSON **compartilhado na rede** (`cadastros_compartilhados\`)
- Alterações refletem **automaticamente** na aba Pedido de Compra (e vice-versa)
- Combos **sem troca acidental** ao rolar o mouse na página

---

## Empresas Faturadoras

Dados padrão vêm de `app/config/settings.py`. Personalizações ficam na **rede**:

```
{BASE_REDE_DIR}\cadastros_compartilhados\empresas_faturadoras.json
```

| Recurso | Detalhe |
|---------|---------|
| Edição pelo programa | Aba Pedido → **✏** → escolher empresa → alterar endereço, CEP, cidade, UF, etc. |
| Persistência | Arquivo na rede — **sobrevive a build/release** |
| Compartilhamento | Iury e Thamyres usam o **mesmo arquivo** |
| BRASUL | Sempre presente; **não pode ser excluída** |
| Demais empresas | Podem ser excluídas pelo **🗑** no painel |
| JB | Removida do cadastro padrão |
| PDF antigo | Pedidos já emitidos continuam reimprimindo com dados históricos |

---

## Rede e Múltiplos Compradores

### Estrutura na rede (`brasul_pedidos`)

```
Z:\0 OBRAS\brasul_pedidos\          ← ou Y:\, detectado automaticamente
├── Iury\
│   ├── cotacao_iury.db
│   ├── pdfs de pedidos\
│   ├── cotações_salvas\
│   └── backup\
├── Thamyres\
│   └── cotacao_thamyres.db
│   └── ...
├── cotacao_rede.db                 ← consolidado (auditoria)
├── cadastros_compartilhados\
│   ├── fornecedores.json
│   ├── obras.json
│   ├── funcionarios.json
│   └── empresas_faturadoras.json
├── _shared\
│   └── locacoes.db
└── BACKUPS\
```

### Detecção automática da unidade (Z:, Y:, etc.)

O sistema procura a pasta `brasul_pedidos` em todas as unidades mapeadas. Funciona mesmo quando um PC usa **Z:** e outro **Y:** apontando para o mesmo servidor.

Variável opcional (fixar caminho manualmente):

```cmd
setx BRASUL_REDE_DIR "Y:\0 OBRAS\brasul_pedidos"
```

Diagnóstico:

```powershell
powershell -ExecutionPolicy Bypass -File tools\diagnostico_rede_pedidos.ps1
```

### Sincronização em background

Com o app aberto, periodicamente:

- Espelha o `.db` do comprador na rede
- Consolida Iury + Thamyres → `cotacao_rede.db` (para auditoria)
- Backup dos bancos na pasta `BACKUPS\`

Variáveis de ambiente (opcionais):

| Variável | Função |
|----------|--------|
| `BRASUL_USUARIO` | Comprador logado (definido no login) |
| `BRASUL_REDE_DIR` | Caminho fixo da pasta `brasul_pedidos` |
| `BRASUL_REDE_SYNC_SEG` | Intervalo de sync (padrão 300 s) |
| `BRASUL_BACKUP_REDE_SEG` | Intervalo backup rede (padrão 900 s) |
| `BRASUL_REDE_CONSOLIDAR` | `1` = merge completo Iury+Thamyres |
| `BRASUL_LOCACOES_XLSM` | Caminho da planilha de locações |
| `BRASUL_LOCACOES_AUTO` | Importar planilha se BD vazio |

---

## PDF de Pedido

Gerado com **ReportLab** (`app/infrastructure/pdf_generator.py`):

- Cabeçalho com logo da empresa faturadora
- Blocos: dados do pedido, obra, fornecedor, endereço de cobrança, faturamento
- Endereço de cobrança lê dados editáveis da empresa (incl. CEP, cidade, UF)
- Tabela de itens com paginação automática (> 15 itens)
- Observação padrão da empresa + observações livres
- PIX / favorecido quando forma de pagamento for PIX
- Nome do arquivo: `PC-{numero}-{empresa}-{obra}.pdf`

---

## Stack Tecnológica

```
Python 3.11+       → linguagem principal
PySide6 (Qt6)      → interface gráfica desktop
SQLite             → banco local e consolidado em rede
ReportLab          → geração de PDFs
OpenPyXL / Pandas  → importação Excel (ferramentas, locações)
Matplotlib         → gráficos auxiliares
Google Drive API   → backup diário na nuvem
PyInstaller        → build do executável .exe
PowerShell         → scripts de release, deploy e backup
GitHub Actions     → build Windows na nuvem (CI)
```

---

## Arquitetura do Projeto

```
sistema_de_pedidos_brasulv2/
├── .github/workflows/
│   └── build-pedidos.yml       # CI: PyInstaller + Release (tags v*)
├── app/
│   ├── config/                 # settings.py — constantes compartilhadas
│   ├── core/                   # DTOs, serviços, regras de negócio
│   ├── data/                   # SQLite, sync rede, cadastros, empresas faturadoras
│   ├── infrastructure/         # PDF, relatórios, imagens
│   └── ui/                     # MainWindow, widgets, estilos
├── assets/
│   ├── logos/                  # Logos das empresas faturadoras
│   └── usuarios.json           # Usuários do login
├── current/                    # Atalho fixo na rede (NÃO versionar)
├── dist/                       # Build PyInstaller (NÃO versionar)
├── releases/                   # Snapshots datados (NÃO versionar)
├── docs/
│   ├── BUILD_REMOTO.md
│   └── CHECKLIST_BUILD_RELEASE.md
├── tools/                      # Scripts PowerShell e utilitários Python
├── main.py                     # Entrada principal (login + MainWindow)
├── main_patrao.py              # Painel gerencial (consulta patrão)
├── config_exemplo.py           # Template → copiar para config.py
├── backup_agendado.py          # Backup cotacao_rede.db → Google Drive
├── requirements.txt
└── SistemaPedidosV2.spec       # Spec PyInstaller
```

**Fluxo de um pedido:**

```
Formulário → PedidoService → pdf_generator → SQLite local → sync rede → cotacao_rede.db
```

---

## Configuração

Copie `config_exemplo.py` para `config.py` e ajuste se necessário:

| Variável | Função |
|----------|--------|
| `COMPRADOR_PADRAO` | Nome do comprador (ex.: `IURY`) — sobrescrito no login |
| `BASE_REDE_DIR` | Raiz `brasul_pedidos` (auto-detectada se omitida) |
| `DATABASE_PATH` | SQLite do comprador na rede |
| `PEDIDOS_DIR` | Pasta de PDFs gerados |
| `EMPRESAS_FATURADORAS` | Defaults em `app/config/settings.py` |

> `config.py` **não é versionado** — cada ambiente mantém o seu na máquina/rede.  
> **Não execute** `tools/prepare_config_ci.py` no PC de produção (só no GitHub Actions).

---

## Instalação (modo desenvolvimento)

**Pré-requisitos:** Windows 10/11, Python 3.11+, acesso à pasta de rede.

```powershell
git clone https://github.com/Yuritborges/sistema_de_pedidos_de_compra.git
cd sistema_de_pedidos_de_compra

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

copy config_exemplo.py config.py
# Ajuste config.py se necessário

python main.py
```

Na primeira execução, selecione o usuário na tela de login (`assets/usuarios.json`).

Painel gerencial (somente consulta):

```powershell
python main_patrao.py
```

---

## Build, release e distribuição

A equipe usa o atalho em:

```
{unidade}:\0 OBRAS\sistema_de_pedidos_brasulv2\current\SistemaPedidosV2.exe
```

(`Z:` ou `Y:` conforme o mapeamento de cada PC.)

### Opção 1 — Tag de versão (recomendado)

```powershell
git push origin main
powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.2.0
```

- Dispara **GitHub Actions** → artefato + **Release** no GitHub
- Baixe o zip em **Releases**, teste, publique na rede:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SistemaPedidosV2"
```

### Opção 2 — Build local completo

```powershell
powershell -ExecutionPolicy Bypass -File tools\release_full.ps1
```

Fecha o app → backup pré-release → PyInstaller → espelha em `current\`.

Se falhar só na cópia para `current\` (arquivo em uso na rede):

```powershell
powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1
```

### Ícone do atalho na rede

Windows nem sempre mostra o ícone do `.exe` em pasta de rede. Após o build:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_icone_atalho.ps1 -CriarAtalhoDesktop
```

Ou em Propriedades do atalho → **Alterar ícone** → `current\SistemaPedidosV2.ico`.

---

## Scripts utilitários (`tools/`)

| Script | Descrição |
|--------|-----------|
| `release_full.ps1` | Backup + build + atualiza `current\` |
| `build_release.ps1` | PyInstaller + `releases/` + `current/` |
| `sync_current_from_dist.ps1` | Copia `dist\` → `current\` sem rebuild |
| `publicar_build_na_rede.ps1` | Publica zip/ pasta extraída na rede |
| `tag_release.ps1` | Cria tag `vX.Y.Z` e dispara CI |
| `publicar_icone_atalho.ps1` | Copia `.ico` e cria atalho com ícone |
| `diagnostico_rede_pedidos.ps1` | Testa mapeamento Z:/Y: e pasta `brasul_pedidos` |
| `consolidar_rede.py` | Merge manual Iury + Thamyres → `cotacao_rede.db` |
| `backup_pre_release.py` | Snapshot antes do build |
| `backup_diario.py` | Backup local legado (vários `.db` + JSON) |
| `agendar_backup_drive.ps1` | Agenda `backup_agendado.py` no Windows (18h) |
| `desagendar_backup_diario.ps1` | Remove tarefas antigas de backup |
| `gerar_token_drive.py` | OAuth Google Drive (uso único) |
| `close_local_sistema_pedidos.ps1` | Encerra processos antes do robocopy |
| `robocopy_mirror.ps1` | Espelha pasta do build (usado internamente) |

Detalhes: [`docs/BUILD_REMOTO.md`](docs/BUILD_REMOTO.md) · [`docs/CHECKLIST_BUILD_RELEASE.md`](docs/CHECKLIST_BUILD_RELEASE.md)

---

## Backup

### Automático — Google Drive

`backup_agendado.py` envia `cotacao_rede.db` para o Google Drive (pasta **Brasul_Backups**).

- Agendar: `tools\agendar_backup_drive.ps1`
- Log: `backup_agendado.log` na raiz do projeto
- Roda com `pythonw` (sem janela preta de CMD)
- Credenciais OAuth em `app/config/` (não versionadas)

### Rede — timer com app aberto

Backup periódico dos `.db` em `brasul_pedidos\BACKUPS\` enquanto o sistema está em uso.

### Antes do release

`tools\backup_pre_release.py` — snapshot de segurança antes de cada build local.

---

## Banco de Dados

| Arquivo | Uso |
|---------|-----|
| `cotacao_{comprador}.db` | Pedidos do comprador (Iury, Thamyres…) |
| `cotacao_rede.db` | Consolidado — **Sistema de Auditoria** |
| `_shared/locacoes.db` | Locações compartilhadas |
| Tabela `ferramentas` | Dentro do `.db` do comprador |

Colunas relevantes em `pedidos`:

- `material_ok_na_obra` — entrega confirmada na obra
- `material_entregue_obra` — carimbo de data da confirmação
- `empresa_faturadora`, `numero`, itens serializados em JSON

Consolidar manualmente (fechar o app em todos os PCs antes):

```powershell
.\.venv\Scripts\python.exe tools\consolidar_rede.py
```

---

## O que versionar no Git

| Caminho | Versionar? |
|---------|------------|
| `app/`, `main.py`, `tools/`, `.github/` | Sim |
| `SistemaPedidosV2.spec`, `config_exemplo.py` | Sim |
| `assets/logos/`, `assets/usuarios.json` | Sim |
| `config.py`, `*.db`, `token.json`, credenciais Drive | **Não** |
| `dist/`, `current/`, `releases/`, `backups/` | **Não** |
| `cadastros_compartilhados/` na rede | **Não** (dados operacionais) |

---

## Trabalho remoto / sem IDE

| Sozinho (Git + GitHub) | Precisa VPN / rede |
|------------------------|-------------------|
| Editar código, `git push` | Publicar em `current\` |
| Tag → build no GitHub Actions | Fechar `.exe` nos PCs antes do robocopy |
| Baixar zip em **Releases** | Mapear unidade (`Z:` ou `Y:`) |

---

## Autor

**Yuri Borges** — Desenvolvimento no âmbito da Brasul Construtora Ltda.

[![GitHub](https://img.shields.io/badge/GitHub-Yuritborges-181717?style=flat-square&logo=github)](https://github.com/Yuritborges)

---

## Licença

Software de **uso interno** da Brasul Construtora Ltda. Reprodução fora do contexto autorizado deve seguir a política da empresa.
