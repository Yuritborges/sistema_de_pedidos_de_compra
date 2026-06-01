# Checklist — Build e release (1 página)

**Projetos:** Sistema de Pedidos (`sistema_de_pedidos_brasulv2`) · Auditoria (`sistema_auditoria_brasul`)

---

## Antes de começar

- [ ] Python 3.11+ e Git instalados
- [ ] Código testado: `.\.venv\Scripts\activate` → `python main.py`
- [ ] Alterações commitadas: `git add .` → `git commit -m "..."` → `git push origin main`
- [ ] Para **publicar na rede**: VPN/AnyDesk + unidade `Z:` mapeada

---

## Release recomendado — tag de versão (GitHub build + Release)

| | **Pedidos** | **Auditoria** |
|---|-------------|---------------|
| Pasta | `Z:\0 OBRAS\sistema_de_pedidos_brasulv2` | `Z:\0 OBRAS\sistema_auditoria_brasul` |
| Tag (exemplo) | `v2.1.0` | `v1.0.0` |
| Workflow | Build Sistema Pedidos | Build Sistema Auditoria |

### Passos

1. [ ] Na pasta do projeto:
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 2.1.1
   ```
   (Use `2.1.1` = próximo número: correção → último +0.0.1; função nova → +0.1.0)

2. [ ] GitHub → **Actions** → aguarde job **verde** (~3–5 min)

3. [ ] GitHub → **Releases** → abra a versão `v2.1.1` → baixe o `.zip`  
   (Não precisa caçar artefato em run antiga.)

4. [ ] Extraia o zip em `C:\Temp\...`

5. [ ] Publicar na rede (`Z:`):
   ```powershell
   # Pedidos
   cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SistemaPedidosV2"

   # Auditoria
   cd "Z:\0 OBRAS\sistema_auditoria_brasul"
   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SISTEMA AUDITORIA BRASUL"
   ```

6. [ ] Validar: abrir `current\*.exe` · pedidos: PDF/obra · auditoria: dados + pendências

---

## Alternativa — build sem tag (teste rápido)

1. [ ] GitHub → **Actions** → **Run workflow** (branch `main`) — **não** use Re-run de run falha antiga  
2. [ ] Baixar artefato no fim da run (expira em 30 dias)  
3. [ ] Mesmo passo 4–6 acima (`publicar_build_na_rede.ps1`)

---

## Alternativa — tudo no PC da rede (sem GitHub)

```powershell
# Pedidos (backup + build + current)
cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
.\.venv\Scripts\activate
powershell -ExecutionPolicy Bypass -File tools\release_full.ps1

# Auditoria
cd "Z:\0 OBRAS\sistema_auditoria_brasul"
.\.venv\Scripts\activate
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

---

## Erros comuns

| Problema | Solução |
|----------|---------|
| CI falha `database` / `.spec not found` | **Run workflow** novo no `main` (commit recente), não Re-run antigo |
| `prepare_config_ci.py` no PC real | **Não rode** em produção — só no GitHub |
| Robocopy falhou | Fechar `.exe` em todos os PCs; repetir publicar |
| Só copiei o `.exe` | Copiar pasta inteira (`_internal` + `.exe`) ou usar `publicar_build_na_rede.ps1` |

---

## Versão — quando subir o número

| Mudança | Exemplo |
|---------|---------|
| Correção de bug | `v2.1.0` → `v2.1.1` |
| Função nova | `v2.1.1` → `v2.2.0` |
| Mudança grande / quebra compatibilidade | `v2.2.0` → `v3.0.0` |

**Autor / TI:** Guia completo em `docs/BUILD_REMOTO.md` · script `tools\tag_release.ps1`
