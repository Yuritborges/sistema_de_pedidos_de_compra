# Sistema de Pedidos — Brasul Construtora

**Versão:** 2 (interface desktop)  
**Stack:** Python 3.11+, PySide6 (Qt), SQLite, ReportLab, OpenPyXL, Pandas  
**Uso:** sistema interno da **Brasul Construtora Ltda** para emissão de pedidos de compra, cotação comparativa entre fornecedores, cadastros compartilhados, locações e integração com pasta de rede.

Este documento descreve o software de forma que **qualquer leitor** (docente, colega ou novo colaborador) compreenda o propósito, a arquitetura e como instalar, configurar e gerar o executável.

---

## 1. Resumo executivo

O sistema substitui fluxos manuais dispersos (planilhas, Word, e-mail) por uma **aplicação única** com:

- **Pedido de compra** padronizado em PDF, com numeração sequencial, múltiplas empresas faturadoras e dados de obra/fornecedor.
- **Pedidos gerados**: consulta, filtros, impressão de relações, reimpressão, edição, controle visual de **entrega na obra** (OK na obra) e sincronização com banco na rede.
- **Cotação comparativa** entre até três fornecedores, com destaque de preços e texto auxiliar para negociação.
- **Locações**, **ferramentas** auxiliares e **cadastros** (fornecedores, obras, funcionários em JSON).

Os dados operacionais vivem em **SQLite** (local por comprador e consolidado na rede), com opção de **espelhamento** periódico para pastas compartilhadas.

---

## 2. Contexto e problema de negócio

Construtoras geram grande volume de **pedidos de material** com requisitos distintos por obra, fornecedor e empresa do grupo econômico. Sem um sistema único, surgem inconsistências de numeração, dificuldade de rastrear o que já foi emitido e pouca visibilidade para o financeiro e para o canteiro.

**Este sistema** centraliza a geração do documento oficial (PDF), mantém histórico consultável e apoia a equipe de compras com cotação lado a lado e cadastros reutilizáveis.

---

## 3. Objetivos

| Objetivo | Como o sistema atende |
|----------|------------------------|
| Padronizar pedidos | Layout PDF único por empresa faturadora, dados vindos de formulário validado |
| Rastrear pedidos emitidos | Tabela em SQLite + pasta de PDFs + aba Pedidos Gerados |
| Apoiar negociação | Cotação comparativa com ranking visual e texto copiável |
| Trabalho em rede | `DATABASE_PATH` e pastas em servidor; scripts de backup e consolidação |
| Distribuição simples | Build com PyInstaller → `SistemaPedidosV2.exe` |

---

## 4. Requisitos técnicos

| Requisito | Detalhe |
|-----------|---------|
| Sistema operacional | Windows 10/11 (principal); desenvolvimento testado neste ambiente |
| Python | 3.11 ou superior (recomendado LTS estável) |
| Rede | Pastas mapeadas (ex.: `Z:\...`) para banco e PDFs, conforme `config.py` |
| Permissões | Leitura/escrita nas pastas de pedidos, backup e cadastros compartilhados |

Dependências Python: ver `requirements.txt` (PySide6, reportlab, openpyxl, pandas, matplotlib onde usado em relatórios).

---

## 5. Arquitetura do projeto

Organização em camadas dentro de `app/`:

```
app/
├── core/           # Regras de negócio leves, DTOs, serviços (ex.: pedido_service)
├── data/           # SQLite, migrações na inicialização, sync com cotacao_rede.db
├── infrastructure/ # PDF (pedido, relação de pedidos), imagens (prazo na obra)
└── ui/             # main_window, estilos, widgets por módulo, diálogos
```

- **`main.py`**: entrada do programa; seleção de utilizador (`BRASUL_USUARIO`), splash, `init_db()`, janela principal.
- **`main_patrao.py`**: variante com `main_window_patrao` (ex.: consulta consolidada para patrão) — fluxo separado do comprador.
- **`config.py`**: **não versionado**; cada máquina copia de `config_exemplo.py` e ajusta caminhos e `COMPRADOR_PADRAO`.

Fluxo típico de um pedido:

1. Utilizador preenche **Pedido de Compra** → `PedidoService` valida → `pdf_generator` gera PDF → `pedido_service` grava pedido e itens no SQLite → opcionalmente sincroniza com `cotacao_rede.db`.

2. **Pedidos Gerados** lê o mesmo SQLite, lista PDFs, aplica filtros e ações (abrir, exportar, OK na obra, excluir).

---

## 6. Módulos da interface (abas)

A barra lateral (`app/ui/main_window.py`) carrega páginas sob demanda (*lazy load*). Atalhos **Ctrl+1** … **Ctrl+6** seguem a ordem abaixo.

| # | Aba | Ficheiro principal | Função |
|---|-----|-------------------|--------|
| 1 | Pedido de Compra | `formulario_pedido.py` | Montagem do pedido, itens, desconto, empresa faturadora; geração via `PedidoService` |
| 2 | Pedidos Gerados | `pedidos_widget.py` | Lista, busca, filtros de data, «A Entregar» / «Entregue», cards, impressão de relação, OK na obra |
| 3 | Cotação | `cotacao_widget.py` | Comparação de preços, persistência em JSON na pasta configurada |
| 4 | Ferramentas | `ferramentas_widget.py` | Utilitários internos (importações, apoio operacional) |
| 5 | Locações | `locacoes_widget.py` | Registros em banco compartilhado, alertas de vencimento na sidebar |
| 6 | Cadastros | `cadastros_widget.py` | Fornecedores, obras e funcionários (JSON em `assets/` + regras em `cadastros_store.py`) |

**Consulta patrão:** `consulta_patrao_widget.py` é usada pela janela `main_window_patrao.py`, não pela barra lateral do fluxo principal de compras.

---

## 7. Banco de dados e regras importantes

### 7.1 Ficheiros SQLite

- **Banco local do comprador:** caminho em `DATABASE_PATH` (ex.: `cotacao_iury.db` na pasta do comprador na rede).
- **Consolidado:** `cotacao_rede.db` na raiz da pasta de rede (merge de compradores), atualizado por scripts e por hooks após salvar pedido (ver `app/data/cotacao_rede_sync.py`).
- **Locações:** ficheiro partilhado em `_shared/locacoes.db` (conforme configuração em `database.py`).

### 7.2 Tabela `pedidos` (conceito)

Campos relevantes incluem: número único, datas, obra, fornecedor, empresa faturadora, valores, caminho do PDF, comprador, prazo de entrega, **`material_ok_na_obra`** (0/1) e **`material_entregue_em`** (carimbo de data/hora quando aplicável).

### 7.3 «OK na obra» (Pedidos Gerados)

- A cor da linha (pendente / OK) e a caixa **DATA PREVISTA DA ENTREGA** no PDF seguem a **flag** `material_ok_na_obra`, gravada apenas pelo botão **OK NA OBRA**.
- Migrações controladas por tabelas-marca em SQLite garantem: correção de dados legados, «baseline» de todos os pedidos antigos como OK num release específico, e **pedidos novos** continuam com flag **0** até confirmação explícita. Detalhe da lógica: `app/core/material_obra.py` e `app/data/database.py` (`init_db`).

### 7.4 Locações (partilha entre compradores)

- **Um único `locacoes.db`** em `BASE_REDE_DIR/_shared/`: todos os compradores leem e gravam o mesmo ficheiro (desde que o `config.py` de cada máquina aponte para a **mesma** `BASE_REDE_DIR` na rede).
- A **barra lateral** (contagem / piscar) atualiza a cada ~60 s a partir do banco.
- A **tabela** da aba Locações recarrega ao **mudar para essa aba**, ao clicar em **Atualizar** e, enquanto a aba estiver aberta, **no mesmo ciclo** de atualização da sidebar (~60 s), para ver linhas que outro utilizador acabou de inserir.
- O filtro **«Grade por vencimento»** (±30/60/90 dias ou «Todos») pode **ocultar** linhas cuja data de pedido e de vencimento caem fora da janela (exceto situação **VENCIDO**, que entra sempre). Use **«Todos (sem filtro de data)»** se algo «sumiu» da lista.

---

## 8. Configuração (`config.py`)

Copie `config_exemplo.py` → `config.py` e ajuste no mínimo:

| Variável | Função |
|----------|--------|
| `COMPRADOR_PADRAO` | Nome do comprador (ex.: IURY) |
| `PASTA_COMPRADOR` | Subpasta na rede (ex.: Iury) |
| `DATABASE_PATH` | SQLite de trabalho desse comprador |
| `BASE_REDE_DIR` | Raiz onde estão pastas por comprador e `cotacao_rede.db` |
| `PEDIDOS_DIR` / `COTACOES_DIR` / `BACKUP_DIR` / `RELACOES_DIR` | Pastas de saída e backup |
| `EMPRESAS_FATURADORAS` | Dados e logos por empresa para o PDF |
| `REDE_SYNC_INTERVALO_SEGUNDOS` | Espelhamento periódico (0 = desligado) |
| `REDE_SYNC_MESCLAR_CONSOLIDADO` | Merge pesado no consolidado (uso avançado) |

O ficheiro exemplo valida placeholders e cria pastas necessárias ao importar.

---

## 9. Instalação (modo desenvolvimento)

1. Instale **Python 3.11+** (opção «Add Python to PATH» no instalador Windows).  
2. Na raiz do projeto: `python -m venv .venv` e ative o ambiente virtual.  
3. `pip install -r requirements.txt`  
4. Copie `config_exemplo.py` para `config.py` e edite caminhos.  
5. Execute: `python main.py`  
6. Na primeira execução, escolha o utilizador na caixa de diálogo (lista em `assets/usuarios.json` + padrões no código).

---

## 10. Build e distribuição (executável)

Scripts PowerShell em `tools/`:

| Script | Descrição |
|--------|-----------|
| `release_full.ps1` | Encerra o app local → **backup pré-release** (`backup_pre_release.py`) → **PyInstaller** → cópias para `releases/` e `current/` |
| `build_release.ps1` | Apenas gera `dist/` e copia para `releases/` e opcionalmente `current/` |
| `backup_pre_release.py` | Zip do código + cópia SQLite (local, rede, locações, cadastros) para `backups/pre_release_*` |
| `sync_current_from_dist.ps1` | Atualiza `current/` quando o robocopy falhou por ficheiro em uso na rede |
| `consolidar_rede.py` | Merge manual dos `.db` dos compradores no consolidado (Python, com `sys.path` para `app`) |

Comando típico na raiz:

```powershell
powershell -ExecutionPolicy Bypass -File tools\release_full.ps1
```

Use `-IncludePythonMain` se estiver a correr `main.py` em modo desenvolvimento; `-SkipCurrent` se não quiser atualizar `current/` enquanto outros PCs tiverem o `.exe` aberto.

O ficheiro de especificação do PyInstaller é `SistemaPedidosV2.spec`.

---

## 11. Pastas e artefactos gerados

| Pasta / ficheiro | Conteúdo | Versionar no Git? |
|------------------|----------|---------------------|
| `app/`, `main.py`, `tools/*.py` | Código-fonte | Sim |
| `config.py` | Segredos/caminhos locais | **Não** (`.gitignore`) |
| `dist/`, `build/`, `releases/`, `current/` | Saída PyInstaller | Não |
| `backups/` | Snapshots `pre_release_*` | Não |
| `pedidos_gerados/` (ou pasta em rede) | PDFs emitidos | Não |
| `assets/*.json` | Cadastros exemplo / dados | Sim (sem backups `.bak_*`) |
| `assets/logos/` | Logos para PDF | Sim |

---

## 12. Logos no PDF

Coloque imagens em `assets/logos/` conforme nomes referenciados em `EMPRESAS_FATURADORAS` no `config.py` (ex.: `logo_brasul.png`, `logo_jb.png`, …). Tamanho sugerido na ordem de **200×80 px**, fundo branco ou transparente.

---

## 13. Testes e qualidade de código

- **Sintaxe:** na raiz do projeto, `python -m compileall -q app main.py main_patrao.py tools` deve concluir sem erros.  
- **Testes automatizados:** o repositório não inclui suíte pytest extensa; validação principal é execução manual do `main.py` e do `.exe` após build.  
- **Logs:** `startup_v2.log` na raiz do projeto pode registar tempos de arranque e etapas de `init_db` / janela principal.

---

## 14. Guia para trabalho académico (faculdade)

Este README serve como **documentação técnica** do projeto para relatório, apresentação ou monografia.

| Sugestão | Detalhe |
|----------|---------|
| **Problema** | Volume de pedidos de compra em construção civil, numeração inconsistente, dispersão entre planilhas e PDFs. |
| **Solução** | Aplicação desktop única: formulário validado, PDF oficial (ReportLab), histórico em SQLite, cotação multi-fornecedor, trabalho em rede. |
| **Arquitetura** | Camadas `app/core`, `app/data`, `app/infrastructure`, `app/ui` (ver secção 5). |
| **Dados na demo** | Não versionar `config.py` nem bases reais da empresa. Para demonstração, usar `config_exemplo.py` como base, **caminhos locais** e **dados fictícios** (obras/fornecedores de exemplo em `assets/`). |
| **Executável** | Após `tools\build_release.ps1`, o `.exe` está em `dist\` ou `releases\`; o atalho interno costuma apontar para `current\`. |
| **Evoluções recentes (exemplo para “trabalho desenvolvido”)** | Correção de leitura `sqlite3.Row` na edição de pedidos; validação de número de pedido já existente ao editar; alinhamento do contador de numeração com o `MAX` real em `proximo_numero_pedido`; contagem na sidebar **Pedidos Gerados (n)** alinhada aos pedidos **sem OK na obra** na lista filtrada; script de reparação pontual `tools/fix_iury_contador_pedidos.py` (caso de legado em bases antigas). |

**Figuras úteis para o documento:** capturas das abas *Pedido de Compra*, *Pedidos Gerados* (filtros e OK na obra) e *Cotação*; diagrama simples “formulário → DTO → `PedidoService` → PDF + SQLite”.

---

## 15. Referência académica (sugestão de citação)

> **Título do trabalho (exemplo):** Sistema desktop de gestão de pedidos de compra e cotações para construção civil — estudo de caso Brasul Construtora.  
> **Tecnologias:** Python, Qt (PySide6), SQLite, geração de PDF, integração com partilha de ficheiros em rede.

Autor do software no âmbito empresarial: **Yuri Borges** — Brasul Construtora Ltda (conforme rodapé histórico do README).

---

## 16. Licença e uso

Software de **uso interno** da Brasul Construtora. Não é distribuição pública genérica; reprodução fora do contexto autorizado deve seguir política da empresa e da instituição de ensino.

---

## 17. Histórico de alterações deste README

- Secção **«Guia para trabalho académico»** com tabela de problema/solução, dados de demo e evoluções recentes do código.
- Documentação alargada para trabalho académico: visão de produto, arquitetura, base de dados, OK na obra, build e tabelas de referência.
- Remoção de módulos UI não referenciados pelo `main_window` (evitar duplicação e confusão): listagem simples antiga de pedidos, widgets de histórico/obras autónomos não ligados ao menu atual.
- Limpeza de ficheiro de backup acidental em `assets/` e regra `.gitignore` para `*.bak_*` gerados pelo editor de cadastros.

Para questões técnicas ou melhorias futuras, usar o repositório e o fluxo de issues/commits da equipa.
