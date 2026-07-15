# Handover — Sistemas Brasul (Pedidos, Auditoria, Atestados)

Documento de passagem de bastão. Objetivo: a empresa conseguir **operar, atualizar e dar suporte** sem depender do desenvolvedor original.

**Última atualização:** 2026-07-10  
**Autor do sistema:** Yuri Borges (Iury)  
**Uso:** interno Brasul Construtora Ltda

---

## 1. Visão geral (o que cada sistema faz)

```
Compradores (Iury / Thamyres)
        │
        ▼
┌───────────────────────────────┐
│  Sistema de Pedidos v2        │  emite PDF, grava SQLite, cadastros
│  SistemaPedidosV2.exe         │
└───────────────┬───────────────┘
                │ consolida
                ▼
        cotacao_rede.db
                │
                ▼
┌───────────────────────────────┐
│  Sistema de Auditoria         │  painel gerencial / pendências
│  SISTEMA AUDITORIA BRASUL.exe │
└───────────────────────────────┘

┌───────────────────────────────┐
│  Sistema de Atestados         │  busca / cadastro de atestados FDE
│  Cofre_Brasul.exe             │
└───────────────────────────────┘
```

| Sistema | Pasta na rede | Executável (atalho da equipe) |
|---------|---------------|-------------------------------|
| Pedidos | `0 OBRAS\sistema_de_pedidos_brasulv2\` | `current\SistemaPedidosV2.exe` |
| Auditoria | `0 OBRAS\sistema_auditoria_brasul\` | `current\SISTEMA AUDITORIA BRASUL.exe` |
| Atestados | `0 OBRAS\Sistema_de_atestado_brasul\` | `current\Cofre_Brasul.exe` |

Atalhos usados pela equipe ficam em:

```
\\192.168.15.250\arquivos brasul\0 OBRAS\
```

(ou `Z:\0 OBRAS\` / `Y:\0 OBRAS\` conforme o mapeamento do PC)

---

## 2. Checklist de entrega (marcar ao passar)

### Código e GitHub

- [ ] Repositório Pedidos atualizado e com push: [sistema_de_pedidos_de_compra](https://github.com/Yuritborges/sistema_de_pedidos_de_compra)
- [ ] Repositório Auditoria atualizado e com push: [sistema_auditoria_brasul](https://github.com/Yuritborges/sistema_auditoria_brasul)
- [ ] Repositório Atestados atualizado e com push (se versionado)
- [ ] Conta/org GitHub da **empresa** com acesso admin (ou transferência do repo)
- [ ] Branch principal documentada: `main`
- [ ] Lista do que **não** vai no Git conferida (abaixo)

### Ambiente de desenvolvimento

- [ ] Python 3.10+ / 3.11+ instalado no PC de manutenção
- [ ] `.venv` criado e `pip install -r requirements.txt` testado
- [ ] `config_exemplo.py` → `config.py` explicado (não versionar `config.py`)
- [ ] App sobe em modo dev: `python main.py`

### Build e publicação

- [ ] Responsável sabe gerar release (local **ou** GitHub Actions)
- [ ] Responsável sabe publicar em `current\`
- [ ] Regra clara: **fechar o .exe em todos os PCs** antes de atualizar `current\`
- [ ] Teste de smoke: abrir Pedidos, emitir/reimprimir 1 PDF, abrir Auditoria

### Rede e dados

- [ ] Acesso ao servidor `\\192.168.15.250\arquivos brasul`
- [ ] Pasta `brasul_pedidos` localizada e com backup recente
- [ ] Quem usa `Z:` e quem usa `Y:` identificado
- [ ] Cadastros compartilhados (`obras.json`, `fornecedores.json`, `empresas_faturadoras.json`) conhecidos

### Segredos e acessos (cofre da empresa — nunca no Git)

- [ ] Credenciais Google Drive (backup), se usadas
- [ ] Tokens / `token.json` / client secret (se existirem)
- [ ] Contas GitHub / Actions
- [ ] Contato dos usuários (compradores / gestão)

### Operação e suporte

- [ ] Contato de suporte definido (interno ou PJ)
- [ ] Canal e horário de atendimento combinados
- [ ] Problemas conhecidos lidos (seção 8)
- [ ] Este `HANDOVER.md` entregue à diretoria / TI

---

## 3. O que vai e o que não vai no Git

| Versionar (Git) | Nunca versionar |
|-----------------|-----------------|
| `app/`, `main.py`, `tools/`, `.github/` | `config.py` |
| `SistemaPedidosV2.spec`, `config_exemplo.py` | `*.db` (bancos) |
| `assets/` (ícones, logos) | `token.json`, credenciais Drive |
| README, este HANDOVER | `dist/`, `current/`, `releases/`, `backups/` |
| | `cadastros_compartilhados/` na rede (dados operacionais) |

---

## 4. Estrutura de dados na rede

```
{unidade}:\0 OBRAS\brasul_pedidos\
├── Iury\
│   ├── cotacao_iury.db
│   ├── pdfs de pedidos\
│   ├── cotações_salvas\
│   └── backup\
├── Thamyres\
│   ├── cotacao_thamyres.db
│   └── ...
├── cotacao_rede.db                 ← consolidado (lido pela Auditoria)
├── cadastros_compartilhados\
│   ├── fornecedores.json
│   ├── obras.json
│   ├── funcionarios.json
│   └── empresas_faturadoras.json
├── _shared\
│   └── locacoes.db
└── BACKUPS\
```

Detecção automática: o Pedidos procura `brasul_pedidos` em `Z:`, `Y:`, etc.

Forçar caminho (opcional):

```cmd
setx BRASUL_REDE_DIR "Y:\0 OBRAS\brasul_pedidos"
```

Diagnóstico:

```powershell
powershell -ExecutionPolicy Bypass -File tools\diagnostico_rede_pedidos.ps1
```

---

## 5. Como atualizar o Pedidos (passo a passo)

### Opção A — Build local (PC com o projeto na rede ou clone)

1. Peça para **todos** fecharem o Sistema de Pedidos.
2. Na pasta do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File tools\release_full.ps1
```

3. Confirme que `current\SistemaPedidosV2.exe` foi atualizado.
4. Peça para a equipe abrir de novo pelo atalho em `0 OBRAS`.

Se o robocopy falhar porque o `.exe` ainda está aberto:

```powershell
powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1
```

### Opção B — Build remoto (GitHub Actions) + publicação na rede

1. Commit + push em `main`.
2. Criar tag de versão:

```powershell
powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.2.0
```

3. Baixar o zip em **GitHub → Releases**.
4. Em um PC **com acesso à rede Brasul**:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SistemaPedidosV2"
```

(ajuste `-Origem` para a pasta extraída do zip)

### Auditoria

```powershell
cd "Z:\0 OBRAS\sistema_auditoria_brasul"
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

### Atestados

```powershell
cd "Z:\0 OBRAS\Sistema_de_atestado_brasul"
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

---

## 6. Desenvolvimento fora da empresa (PJ / remoto)

| Pode fazer sem rede Brasul | Precisa de rede / alguém interno |
|----------------------------|----------------------------------|
| Clonar GitHub, editar código | Publicar em `current\` |
| `git push` | Acessar bancos / PDFs de produção |
| Build local ou GitHub Actions | Mapear `Z:` / `Y:` / UNC |
| Entregar zip do Release | Fechar `.exe` nos PCs da equipe |

Fluxo recomendado com suporte PJ:

1. Desenvolvedor altera e gera Release no GitHub.  
2. Envia link do zip / Release.  
3. Pessoa **interna** fecha o programa e roda `publicar_build_na_rede.ps1`.  
4. Equipe reabre o atalho.

---

## 7. Configuração por máquina (dev)

1. Copiar `config_exemplo.py` → `config.py`
2. Definir `COMPRADOR_PADRAO` (`IURY`, `THAMYRES`, etc.)
3. Rodar:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

No `.exe` de produção, o usuário escolhe o comprador no login; não depende de editar `config.py` em cada PC.

---

## 8. Problemas conhecidos

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| Aviso “arquivo fora da rede local” ao abrir atalho | Windows trata `Y:`/`Z:` como zona Internet | Marcar `\\192.168.15.250` como **Intranet local** (`inetcpl.cpl`). Versões novas do Pedidos/Auditoria/Atestados tentam aplicar isso automaticamente na 1ª abertura. |
| Ícone do atalho branco na pasta de rede | Limitação do Windows com ícones UNC | Atalho na Área de Trabalho com ícone local; ou política `EnableShellShortcutIconRemotePath=1` |
| Build falha ao copiar para `current\` | `.exe` aberto em algum PC | Fechar em todos → `tools\sync_current_from_dist.ps1` |
| Banco “locked” / travado | Outra cópia do app ou backup na rede | Fechar todas as instâncias; aguardar ~30 s; reabrir |
| PC usa `Y:` e outro usa `Z:` | Unidades mapeadas diferentes | Normal — o app detecta; se falhar, `BRASUL_REDE_DIR` |
| Endereço da obra vazio na reimpressão | Bug antigo (já corrigido no código) | Precisa de release com a correção publicada em `current\` |

Scripts úteis (Pedidos):

- `tools\confiar_rede_e_icone_pc.ps1` — Intranet + ícone (rodar no PC do usuário)
- `tools\instalar_pedidos_area_trabalho.ps1` — atalho Desktop com ícone local
- `tools\atualizar_atalho_pedidos_rede.ps1` — atualiza `.lnk` existente (ícone do `.exe`, sem arquivos novos em `0 OBRAS`)
- `tools\diagnostico_rede_pedidos.ps1` — diagnóstico de rede

---

## 9. Contatos e responsabilidades (preencher na entrega)

| Papel | Nome | Contato |
|-------|------|--------|
| Desenvolvedor / suporte PJ | | |
| TI / rede / servidor | | |
| Comprador 1 | | |
| Comprador 2 | | |
| Gestão / auditoria | | |
| Quem publica builds na rede | | |

**Acordo de suporte (se PJ):**

- Horas incluídas / mês: ________  
- Prazo de resposta: ________  
- Quem publica em `current\`: ________  
- Canal (e-mail / WhatsApp): ________  

---

## 10. Critério de “handover concluído”

O handover só está completo quando **outra pessoa** conseguir, sozinha:

1. Abrir o Pedidos pelo atalho da rede  
2. Gerar um build novo (local ou GitHub)  
3. Publicar em `current\`  
4. Abrir a Auditoria e ver dados de `cotacao_rede.db`  
5. Saber onde estão bancos, cadastros e este documento  

Se qualquer item falhar, o handover **não** está pronto.

---

## Referências rápidas

- README Pedidos: `README.md` neste repositório  
- GitHub Pedidos: https://github.com/Yuritborges/sistema_de_pedidos_de_compra  
- GitHub Auditoria: https://github.com/Yuritborges/sistema_auditoria_brasul  
- Servidor de arquivos: `\\192.168.15.250\arquivos brasul`  
)
