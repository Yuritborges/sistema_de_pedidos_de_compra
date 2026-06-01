# Build e release sem depender de uma máquina fixa

Hoje o fluxo antigo (`release_full.ps1` neste PC) faz **tudo junto**: backup, PyInstaller e cópia para `current\`.

A partir daqui dá para **separar em duas etapas**:

| Etapa | Onde roda | Precisa de `Z:`? |
|-------|-----------|------------------|
| **1. Build** (gerar o `.exe`) | GitHub Actions **ou** qualquer PC com Python | **Não** |
| **2. Publicar** (copiar para `current\`) | Qualquer PC na rede com `Z:` mapeado | **Sim** |

Assim você pode desenvolver e **compilar de casa**; só precisa de acesso à rede na hora de **publicar** para a equipe.

---

## Opção A — Tag de versão (recomendado para release oficial)

Depois de **commit + push** em `main`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.1.1
```

Isso cria a tag `v2.1.1`, dispara o build no GitHub e publica em **Releases** com o zip anexado (nome `SistemaPedidosV2-v2.1.1.zip`). Checklist completo: `docs/CHECKLIST_BUILD_RELEASE.md`.

---

## Opção B — Build na nuvem sem tag (teste rápido)

1. Faça **commit + push** do código para `main`.
2. No GitHub: **Actions** → **Build Sistema Pedidos** → **Run workflow**
3. Baixe o artefato **`SistemaPedidosV2-build.zip`** (válido 30 dias).
4. Extraia o zip (pasta com `SistemaPedidosV2.exe` e DLLs).
5. De **qualquer PC** com `Z:` (VPN se estiver fora):
   ```powershell
   cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\caminho\para\pasta\extraida"
   ```

A equipe reabre o atalho em `current\` e recebe a versão nova.

---

## Opção C — Build local (qualquer máquina)

Na pasta do projeto (clone do GitHub):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
python tools\prepare_config_ci.py   # ou use seu config.py real
pyinstaller SistemaPedidosV2.spec --clean --noconfirm
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1
```

Não precisa ser o PC onde você desenvolve hoje.

---

## Opção D — Publicação 100% automática na rede (avançado)

Instalar um **GitHub Actions self-hosted runner** em um PC/servidor **sempre ligado** na empresa, com `Z:` mapeado. O workflow pode buildar **e** rodar `publicar_build_na_rede.ps1` sozinho.

Requisitos: TI autorizar, runner Windows na rede, conta de serviço com permissão em `Z:\0 OBRAS\...`.

---

## O que continua na rede (não vai para o GitHub)

- `config.py` de cada comprador (caminhos `Z:\`, nome IURY/THAMYRES)
- Bancos SQLite e PDFs em `brasul_pedidos\`
- Pasta `current\` (executável que a equipe usa)

O `.exe` **não embute** o `config.py` — cada instalação usa o `config.py` da pasta do projeto na rede (ou ao lado do exe, conforme o atalho).

---

## Se você sair da empresa

| Você consegue de casa | Precisa de alguém na empresa / VPN |
|------------------------|-------------------------------------|
| Editar código no GitHub | Publicar em `current\` |
| Disparar build no Actions | Mapear `Z:` (VPN) |
| Baixar o zip do build | Fechar `.exe` nos PCs antes do robocopy (ou `-SkipKill`) |

**Plano mínimo:** VPN + este script de publicar + documentar para TI ou um colega rodar `publicar_build_na_rede.ps1` quando você enviar o zip.
