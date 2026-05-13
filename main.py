# main.py
# Ponto de entrada do sistema.
# Rode com: python main.py

import sys
import os
import json
import time
from datetime import datetime

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("brasul.pedidos.v2")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


GLOBAL_CSS = """
    QWidget                { color: #111827; }
    QLineEdit              { color: #111827; background: #FFFFFF;
                             selection-background-color: #BFDBFE;
                             selection-color: #1E3A5F; }
    QLineEdit:read-only    { color: #6B7280; background: #F3F4F6; }
    QComboBox              { color: #111827; background: #FFFFFF; }
    QSpinBox               { color: #111827; background: #FFFFFF; }
    QDoubleSpinBox         { color: #111827; background: #FFFFFF; }
    QTextEdit              { color: #111827; background: #FFFFFF; }
    QLabel                 { color: #111827; background: transparent; }
    QGroupBox              { color: #111827; }
    /* QTableWidget: cada aba define seu próprio QSS; cor global em ::item quebrava delegates (ex.: Locações). */
    QHeaderView::section   { color: #FFFFFF; }
    QMessageBox QLabel     { color: #111827; }
    QComboBox QAbstractItemView {
        color: #111827; background: #FFFFFF;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A5F;
    }
"""


def main():
    try:
        inicio_total = time.perf_counter()
        tempos = []

        def marcar(etapa):
            tempos.append((etapa, time.perf_counter() - inicio_total))

        # Cada processo deve escolher utilizador de novo (evita env herdado).
        os.environ.pop("BRASUL_USUARIO", None)

        from PySide6.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QLabel, QPushButton,
            QHBoxLayout, QInputDialog, QMessageBox
        )
        from PySide6.QtGui import QIcon
        marcar("imports-qt")

        from app.ui.qt_i18n import instalar_traducoes_qt_pt_br

        app = QApplication(sys.argv)
        instalar_traducoes_qt_pt_br(app)
        app.setApplicationName("Sistema de Cotação - Brasul")
        app.setOrganizationName("Brasul Construtora")
        app.setStyle("Fusion")
        app.setStyleSheet(GLOBAL_CSS)
        marcar("qapplication-criada")
        icon_path = _icone_app_path()
        if icon_path:
            app.setWindowIcon(QIcon(icon_path))
        marcar("icone-aplicado")

        usuario = _selecionar_usuario(app)
        if not usuario:
            return
        marcar("usuario-selecionado")

        os.environ["BRASUL_USUARIO"] = usuario

        from app.data.database import init_db
        from app.ui.main_window import MainWindow, criar_splash
        marcar("imports-app")

        init_db()
        marcar("init-db")

        # Mostra splash enquanto a janela carrega
        splash = criar_splash()
        splash.show()
        app.processEvents()
        marcar("splash-pronta")

        window = MainWindow()
        marcar("main-window-criada")

        # Fecha a splash assim que a janela principal estiver pronta.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: (splash.finish(window), window.show()))
        marcar("timer-show-janela")

        try:
            base = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(base, "startup_v2.log")
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            linhas = [f"\n=== Startup {agora} ===", f"usuario={usuario}"]
            anterior = 0.0
            for etapa, acumulado in tempos:
                delta = acumulado - anterior
                linhas.append(f"{etapa:24s} +{delta:7.3f}s  total={acumulado:7.3f}s")
                anterior = acumulado
            linhas.append(f"TOTAL_INICIALIZACAO        total={anterior:7.3f}s")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
        except Exception:
            pass

        sys.exit(app.exec())

    except ImportError as e:
        # Não confundir "DLL load failed" (rede, antivírus, PySide na rede) com "pacote não instalado".
        msg = str(e).lower()
        print("ERRO: não foi possível carregar a interface gráfica (PySide6 / Qt).", file=sys.stderr)
        print(f"Detalhe: {e}", file=sys.stderr)
        if "dll" in msg or "rede" in msg or "network" in msg or "126" in msg:
            print(
                "\nSe o programa está numa pasta de rede (Z: ou \\\\servidor), copie a pasta "
                "'SistemaPedidosV2' para o disco local (ex.: C:\\Apps\\) e execute de lá, "
                "ou verifique VPN, cabo e antivírus bloqueando DLLs.",
                file=sys.stderr,
            )
        else:
            print(
                "\nInstale as dependências na máquina de desenvolvimento:\n"
                "  pip install -r requirements.txt",
                file=sys.stderr,
            )
        sys.exit(1)


def _users_file_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", "usuarios.json")


def _icone_app_path():
    base = os.path.dirname(os.path.abspath(__file__))
    candidatos = [
        os.path.join(base, "assets", "iconebrasul2.ico"),
        os.path.join(base, "assets", "logos", "logo_brasul.ico"),
        os.path.join(base, "assets", "logo.ico"),
        os.path.join(base, "assets", "logos", "logo_brasul.png"),
        os.path.join(base, "assets", "logo_brasul.png"),
    ]
    return next((p for p in candidatos if os.path.exists(p)), "")


def _carregar_usuarios():
    usuarios = ["IURY", "THAMYRES"]
    caminho = _users_file_path()
    try:
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            extras = dados.get("usuarios", [])
            for nome in extras:
                n = str(nome or "").strip().upper()
                if n and n not in usuarios:
                    usuarios.append(n)
    except Exception:
        pass
    return usuarios


def _salvar_novo_usuario(nome_usuario: str):
    caminho = _users_file_path()
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    atuais = _carregar_usuarios()
    if nome_usuario not in atuais:
        atuais.append(nome_usuario)

    apenas_extras = [u for u in atuais if u not in ("IURY", "THAMYRES")]
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"usuarios": apenas_extras}, f, ensure_ascii=False, indent=2)


def _selecionar_usuario(app) -> str:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QLabel, QPushButton, QWidget,
        QHBoxLayout, QInputDialog, QMessageBox, QFrame
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap, QIcon, QGuiApplication

    dlg = QDialog()
    dlg.setWindowTitle("Acesso ao Sistema")
    dlg.setWindowModality(Qt.ApplicationModal)
    dlg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    icon_path = _icone_app_path()
    if icon_path:
        dlg.setWindowIcon(QIcon(icon_path))
    dlg.setModal(True)
    dlg.setFixedSize(520, 430)
    dlg.setStyleSheet(
        """
        QDialog { background: #F3F4F6; }
        QFrame#card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
        }
        QLabel#titulo {
            font-size: 22px;
            font-weight: 800;
            color: #111827;
        }
        QLabel#subtitulo {
            font-size: 12px;
            color: #6B7280;
        }
        QPushButton#userBtn {
            background: #FFFFFF;
            border: 1px solid #D1D5DB;
            border-radius: 8px;
            min-height: 42px;
            font-size: 14px;
            font-weight: 700;
            text-align: left;
            padding: 0 14px;
            color: #111827;
        }
        QPushButton#userBtn:hover {
            background: #FEF2F2;
            border-color: #DC2626;
            color: #B91C1C;
        }
        QPushButton#novoBtn {
            background: #DC2626;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            min-height: 38px;
            font-size: 13px;
            font-weight: 700;
            padding: 0 14px;
        }
        QPushButton#novoBtn:hover { background: #B91C1C; }
        QPushButton#cancelarBtn {
            background: #FFFFFF;
            color: #374151;
            border: 1px solid #D1D5DB;
            border-radius: 8px;
            min-height: 38px;
            font-size: 13px;
            font-weight: 600;
            padding: 0 14px;
        }
        QPushButton#cancelarBtn:hover { background: #F9FAFB; }
        """
    )

    outer = QVBoxLayout(dlg)
    outer.setContentsMargins(22, 20, 22, 20)

    card = QFrame()
    card.setObjectName("card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)

    lbl_logo = QLabel()
    lbl_logo.setAlignment(Qt.AlignCenter)
    base = os.path.dirname(os.path.abspath(__file__))
    logo_candidates = [
        os.path.join(base, "assets", "logos", "logo_brasul.png"),
        os.path.join(base, "assets", "logo_brasul.png"),
        os.path.join(base, "assets", "brasul.png"),
    ]
    logo_path = next((p for p in logo_candidates if os.path.exists(p)), "")
    if logo_path:
        pix = QPixmap(logo_path)
        if not pix.isNull():
            lbl_logo.setPixmap(pix.scaledToHeight(36, Qt.SmoothTransformation))
    if lbl_logo.pixmap() is None:
        lbl_logo.setText("BRASUL")
        lbl_logo.setStyleSheet("font-size:11px; font-weight:800; letter-spacing:1px; color:#B91C1C;")
    layout.addWidget(lbl_logo)

    titulo = QLabel("Sistema de Pedidos")
    titulo.setObjectName("titulo")
    titulo.setAlignment(Qt.AlignCenter)
    layout.addWidget(titulo)

    subtitulo = QLabel("Selecione o usuário para iniciar")
    subtitulo.setObjectName("subtitulo")
    subtitulo.setAlignment(Qt.AlignCenter)
    layout.addWidget(subtitulo)

    separador = QWidget()
    separador.setFixedHeight(8)
    layout.addWidget(separador)

    escolhido = {"nome": None}

    def escolher(nome):
        escolhido["nome"] = nome
        dlg.accept()

    for nome in _carregar_usuarios():
        b = QPushButton(nome.title())
        b.setObjectName("userBtn")
        b.clicked.connect(lambda _=False, n=nome: escolher(n))
        layout.addWidget(b)

    rodape = QHBoxLayout()
    btn_novo = QPushButton("+ Novo usuário")
    btn_novo.setObjectName("novoBtn")
    btn_cancelar = QPushButton("Cancelar")
    btn_cancelar.setObjectName("cancelarBtn")
    btn_cancelar.clicked.connect(dlg.reject)

    def adicionar_usuario():
        nome, ok = QInputDialog.getText(
            dlg, "Novo usuário", "Digite o nome do novo usuário (ex: JOAO):"
        )
        nome = str(nome or "").strip().upper()
        if not ok:
            return
        if not nome:
            QMessageBox.warning(dlg, "Nome inválido", "Informe um nome de usuário.")
            return
        _salvar_novo_usuario(nome)
        escolhido["nome"] = nome
        dlg.accept()

    btn_novo.clicked.connect(adicionar_usuario)
    rodape.addWidget(btn_novo)
    rodape.addWidget(btn_cancelar)
    layout.addLayout(rodape)
    outer.addWidget(card)

    pm = QGuiApplication.primaryScreen()
    if pm:
        dlg.adjustSize()
        fg = dlg.frameGeometry()
        fg.moveCenter(pm.availableGeometry().center())
        dlg.move(fg.topLeft())
    dlg.raise_()
    dlg.activateWindow()

    if dlg.exec() != QDialog.Accepted:
        return ""
    return escolhido["nome"] or ""


def _demo_cli():
    """Só para teste manual (não é chamado no arranque normal). Ex.: definir BRASUL_DEMO_CLI=1."""
    from app.core.services.pedido_service import PedidoService
    from app.core.dto.pedido_dto import PedidoDTO, ItemPedidoDTO
    from app.data.database import proximo_numero_pedido

    dto = PedidoDTO(
        numero=proximo_numero_pedido(),
        data_pedido="09/04/2026",
        empresa_faturadora="BRASUL", comprador="IURY",
        obra="MARIA RITA ARAÚJO", escola="E.E Maria Rita Araújo",
        endereco_entrega="R. Ernesto Bergamasco, 665",
        bairro_entrega="Vila São Pedro", cep_entrega="13183-080",
        cidade_entrega="Hortolândia", uf_entrega="SP",
        fornecedor_nome="AZEFER MATERIAIS",
        fornecedor_razao="AZEFER MATERIAIS PARA CONSTRUÇÃO EIRELI",
        fornecedor_email="vendas@azevedoconstrucao.com.br",
        fornecedor_vendedor="Cleber", fornecedor_telefone="19 98745-3060",
        prazo_entrega=5, condicao_pagamento="14", forma_pagamento="BOLETO",
        itens=[
            ItemPedidoDTO("AREIA GROSSA MD MT", 2.0, "M3", 153.09),
            ItemPedidoDTO("CIMENTO 50KG VOTORAN CPII", 10.0, "SACO", 39.90),
        ]
    )
    service = PedidoService()
    print("PDF gerado em:", service.gerar_pdf(dto))


if __name__ == "__main__":
    if os.environ.get("BRASUL_DEMO_CLI", "").strip() in ("1", "true", "yes", "sim"):
        _demo_cli()
    else:
        main()
