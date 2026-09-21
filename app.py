import streamlit as st
import json
import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Súmula de Vôlei",
    page_icon="🏐",
    layout="wide"
)

ARQUIVO_HISTORICO = "historico_partidas.json"


# ============================================================
# FUNÇÕES
# ============================================================

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except:
            return []
    return []


def salvar_historico(partida):
    historico = carregar_historico()
    historico.append(partida)

    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, ensure_ascii=False, indent=4)


def inicializar():
    valores = {
        "pontos_a": 0,
        "pontos_b": 0,
        "sets_a": 0,
        "sets_b": 0,
        "sets": [],
        "partida_finalizada": False,
        "inicio": None,
        "fim": None,
        "substituicoes": [],
        "cartoes": [],
        "ocorrencias": [],
        "salvou_historico": False
    }

    for chave, valor in valores.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


inicializar()


def resetar_partida():
    st.session_state.pontos_a = 0
    st.session_state.pontos_b = 0
    st.session_state.sets_a = 0
    st.session_state.sets_b = 0
    st.session_state.sets = []
    st.session_state.partida_finalizada = False
    st.session_state.inicio = None
    st.session_state.fim = None
    st.session_state.substituicoes = []
    st.session_state.cartoes = []
    st.session_state.ocorrencias = []
    st.session_state.salvou_historico = False


def set_atual():
    return len(st.session_state.sets) + 1


def pontuacao_necessaria():
    # 5º set = 15 pontos
    if set_atual() == 5:
        return 15
    return 25


def verificar_fim_set():
    a = st.session_state.pontos_a
    b = st.session_state.pontos_b

    necessario = pontuacao_necessaria()

    if (a >= necessario or b >= necessario) and abs(a - b) >= 2:
        if a > b:
            vencedor = "Equipe A"
            st.session_state.sets_a += 1
        else:
            vencedor = "Equipe B"
            st.session_state.sets_b += 1

        numero = set_atual()

        st.session_state.sets.append({
            "set": numero,
            "equipe_a": a,
            "equipe_b": b,
            "vencedor": vencedor
        })

        st.session_state.pontos_a = 0
        st.session_state.pontos_b = 0

        # Melhor de 5: 3 sets vence
        if st.session_state.sets_a == 3 or st.session_state.sets_b == 3:
            st.session_state.partida_finalizada = True
            st.session_state.fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            if st.session_state.sets_a > st.session_state.sets_b:
                st.session_state.vencedor = st.session_state.nome_a
            else:
                st.session_state.vencedor = st.session_state.nome_b

            salvar_partida_historico()


def salvar_partida_historico():
    if st.session_state.salvou_historico:
        return

    partida = {
        "data": str(st.session_state.data_partida),
        "hora_inicio": st.session_state.inicio,
        "hora_fim": st.session_state.fim,
        "campeonato": st.session_state.campeonato,
        "local": st.session_state.local,
        "equipe_a": st.session_state.nome_a,
        "equipe_b": st.session_state.nome_b,
        "sets_a": st.session_state.sets_a,
        "sets_b": st.session_state.sets_b,
        "sets": st.session_state.sets,
        "vencedor": st.session_state.vencedor
    }

    salvar_historico(partida)
    st.session_state.salvou_historico = True


def criar_pdf():
    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        textColor=HexColor("#0B3D91"),
        spaceAfter=8
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Heading2"],
        alignment=TA_CENTER,
        fontSize=12,
        textColor=HexColor("#444444")
    )

    normal = ParagraphStyle(
        "Normal2",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12
    )

    elementos = []

    elementos.append(Paragraph("🏐 SÚMULA OFICIAL DE VÔLEI", titulo))
    elementos.append(
        Paragraph(
            f"{st.session_state.campeonato}",
            subtitulo
        )
    )
    elementos.append(Spacer(1, 15))

    dados = [
        ["INFORMAÇÕES DA PARTIDA", ""],
        ["Data", st.session_state.data_partida],
        ["Local", st.session_state.local],
        ["Início", str(st.session_state.inicio)],
        ["Fim", str(st.session_state.fim)],
    ]

    tabela = Table(dados, colWidths=[5 * cm, 11 * cm])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (0, -1), HexColor("#EAF1FF")),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 15))

    resultado = [
        ["EQUIPE", "SETS"],
        [st.session_state.nome_a, str(st.session_state.sets_a)],
        [st.session_state.nome_b, str(st.session_state.sets_b)]
    ]

    tabela_resultado = Table(
        resultado,
        colWidths=[11 * cm, 5 * cm]
    )

    tabela_resultado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(Paragraph("RESULTADO FINAL", subtitulo))
    elementos.append(Spacer(1, 7))
    elementos.append(tabela_resultado)
    elementos.append(Spacer(1, 10))

    elementos.append(
        Paragraph(
            f"<b>VENCEDOR: {st.session_state.vencedor}</b>",
            ParagraphStyle(
                "Vencedor",
                parent=normal,
                alignment=TA_CENTER,
                fontSize=14,
                textColor=HexColor("#0B3D91")
            )
        )
    )

    elementos.append(Spacer(1, 18))

    # SETS
    elementos.append(Paragraph("PLACAR POR SET", subtitulo))
    elementos.append(Spacer(1, 7))

    dados_sets = [["Set", st.session_state.nome_a, st.session_state.nome_b, "Vencedor"]]

    for item in st.session_state.sets:
        dados_sets.append([
            str(item["set"]),
            str(item["equipe_a"]),
            str(item["equipe_b"]),
            item["vencedor"]
        ])

    tabela_sets = Table(
        dados_sets,
        colWidths=[2 * cm, 5 * cm, 5 * cm, 4 * cm]
    )

    tabela_sets.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabela_sets)
    elementos.append(Spacer(1, 18))

    # JOGADORES
    elementos.append(Paragraph("JOGADORES", subtitulo))
    elementos.append(Spacer(1, 7))

    dados_jogadores = [
        ["Equipe", "Nº", "Jogador", "Posição", "Tipo"]
    ]

    for jogador in st.session_state.jogadores_a:
        dados_jogadores.append([
            st.session_state.nome_a,
            jogador["numero"],
            jogador["nome"],
            jogador["posicao"],
            jogador["tipo"]
        ])

    for jogador in st.session_state.jogadores_b:
        dados_jogadores.append([
            st.session_state.nome_b,
            jogador["numero"],
            jogador["nome"],
            jogador["posicao"],
            jogador["tipo"]
        ])

    tabela_jogadores = Table(
        dados_jogadores,
        colWidths=[3.2 * cm, 1.5 * cm, 5 * cm, 3 * cm, 3 * cm]
    )

    tabela_jogadores.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))

    elementos.append(tabela_jogadores)
    elementos.append(Spacer(1, 18))

    # ARBITRAGEM
    elementos.append(Paragraph("ARBITRAGEM", subtitulo))
    elementos.append(Spacer(1, 7))

    arbitragem = [
        ["Função", "Nome"],
        ["1º Árbitro", st.session_state.arbitro1],
        ["2º Árbitro", st.session_state.arbitro2],
        ["Apontador", st.session_state.apontador]
    ]

    tabela_arbitragem = Table(
        arbitragem,
        colWidths=[5 * cm, 11 * cm]
    )

    tabela_arbitragem.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabela_arbitragem)
    elementos.append(Spacer(1, 18))

    # SUBSTITUIÇÕES
    elementos.append(Paragraph("SUBSTITUIÇÕES", subtitulo))
    elementos.append(Spacer(1, 7))

    subs = [["Equipe", "Sai", "Entra"]]

    for sub in st.session_state.substituicoes:
        subs.append([
            sub["equipe"],
            sub["sai"],
            sub["entra"]
        ])

    if len(subs) == 1:
        subs.append(["Nenhuma", "-", "-"])

    tabela_subs = Table(
        subs,
        colWidths=[4 * cm, 6 * cm, 6 * cm]
    )

    tabela_subs.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabela_subs)
    elementos.append(Spacer(1, 18))

    # CARTÕES
    elementos.append(Paragraph("CARTÕES / OCORRÊNCIAS DISCIPLINARES", subtitulo))
    elementos.append(Spacer(1, 7))

    cartoes = [["Equipe", "Jogador", "Cartão", "Motivo"]]

    for cartao in st.session_state.cartoes:
        cartoes.append([
            cartao["equipe"],
            cartao["jogador"],
            cartao["cartao"],
            cartao["motivo"]
        ])

    if len(cartoes) == 1:
        cartoes.append(["Nenhum", "-", "-", "-"])

    tabela_cartoes = Table(
        cartoes,
        colWidths=[3 * cm, 4 * cm, 3 * cm, 6 * cm]
    )

    tabela_cartoes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))

    elementos.append(tabela_cartoes)
    elementos.append(Spacer(1, 18))

    # OCORRÊNCIAS
    elementos.append(Paragraph("OCORRÊNCIAS", subtitulo))
    elementos.append(Spacer(1, 7))

    if st.session_state.ocorrencias:
        for ocorrencia in st.session_state.ocorrencias:
            elementos.append(Paragraph("• " + ocorrencia, normal))
            elementos.append(Spacer(1, 4))
    else:
        elementos.append(Paragraph("Nenhuma ocorrência registrada.", normal))

    elementos.append(Spacer(1, 30))

    # ASSINATURAS
    assinaturas = [
        ["____________________________", "____________________________"],
        ["1º Árbitro", "2º Árbitro"],
        ["", ""],
        ["____________________________", "____________________________"],
        ["Apontador", "Responsável pela equipe"]
    ]

    tabela_assinaturas = Table(
        assinaturas,
        colWidths=[8 * cm, 8 * cm]
    )

    tabela_assinaturas.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))

    elementos.append(tabela_assinaturas)

    elementos.append(Spacer(1, 20))

    elementos.append(
        Paragraph(
            "Sistema de Súmula de Vôlei • Desenvolvido em Python + Streamlit",
            ParagraphStyle(
                "Rodape",
                parent=normal,
                alignment=TA_CENTER,
                fontSize=8,
                textColor=colors.grey
            )
        )
    )

    documento.build(elementos)

    buffer.seek(0)
    return buffer


# ============================================================
# TÍTULO
# ============================================================

st.title("🏐 Sistema de Súmula de Vôlei")
st.caption("Sistema digital para cadastro, controle e registro de partidas")


# ============================================================
# ABAS
# ============================================================

aba1, aba2, aba3, aba4 = st.tabs([
    "📋 Cadastro",
    "🏐 Partida",
    "📄 Súmula",
    "💾 Histórico"
])


# ============================================================
# ABA 1 - CADASTRO
# ============================================================

with aba1:

    st.header("📋 Cadastro da partida")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.nome_a = st.text_input(
            "🏠 Nome da Equipe A",
            value=st.session_state.get("nome_a", "Equipe A")
        )

        st.session_state.arbitro1 = st.text_input(
            "👨‍⚖️ 1º Árbitro",
            value=st.session_state.get("arbitro1", "")
        )

        st.session_state.data_partida = st.date_input(
            "📅 Data",
            value=datetime.now().date()
        )

    with col2:
        st.session_state.nome_b = st.text_input(
            "🚩 Nome da Equipe B",
            value=st.session_state.get("nome_b", "Equipe B")
        )

        st.session_state.arbitro2 = st.text_input(
            "👨‍⚖️ 2º Árbitro",
            value=st.session_state.get("arbitro2", "")
        )

        st.session_state.local = st.text_input(
            "📍 Local",
            value=st.session_state.get("local", "")
        )

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.apontador = st.text_input(
            "📝 Apontador",
            value=st.session_state.get("apontador", "")
        )

    with col2:
        st.session_state.campeonato = st.text_input(
            "🏆 Campeonato",
            value=st.session_state.get("campeonato", "")
        )

    st.divider()

    # --------------------------------------------------------
    # JOGADORES EQUIPE A
    # --------------------------------------------------------

    st.subheader(f"👥 Jogadores — {st.session_state.nome_a}")

    jogadores_a = []

    for i in range(12):

        col1, col2, col3, col4 = st.columns([1, 4, 2, 2])

        with col1:
            numero = st.number_input(
                f"Nº {i+1}",
                min_value=1,
                max_value=99,
                value=i + 1,
                key=f"a_num_{i}"
            )

        with col2:
            nome = st.text_input(
                f"Nome {i+1}",
                key=f"a_nome_{i}"
            )

        with col3:
            posicao = st.selectbox(
                f"Posição {i+1}",
                [
                    "Levantador",
                    "Oposto",
                    "Ponteiro",
                    "Central",
                    "Líbero"
                ],
                key=f"a_pos_{i}"
            )

        with col4:
            tipo = st.selectbox(
                f"Tipo {i+1}",
                ["Titular", "Reserva"],
                key=f"a_tipo_{i}"
            )

        if nome:
            jogadores_a.append({
                "numero": numero,
                "nome": nome,
                "posicao": posicao,
                "tipo": tipo
            })

    st.session_state.jogadores_a = jogadores_a

    st.divider()

    # --------------------------------------------------------
    # JOGADORES EQUIPE B
    # --------------------------------------------------------

    st.subheader(f"👥 Jogadores — {st.session_state.nome_b}")

    jogadores_b = []

    for i in range(12):

        col1, col2, col3, col4 = st.columns([1, 4, 2, 2])

        with col1:
            numero = st.number_input(
                f"Nº {i+1}",
                min_value=1,
                max_value=99,
                value=i + 1,
                key=f"b_num_{i}"
            )

        with col2:
            nome = st.text_input(
                f"Nome {i+1}",
                key=f"b_nome_{i}"
            )

        with col3:
            posicao = st.selectbox(
                f"Posição {i+1}",
                [
                    "Levantador",
                    "Oposto",
                    "Ponteiro",
                    "Central",
                    "Líbero"
                ],
                key=f"b_pos_{i}"
            )

        with col4:
            tipo = st.selectbox(
                f"Tipo {i+1}",
                ["Titular", "Reserva"],
                key=f"b_tipo_{i}"
            )

        if nome:
            jogadores_b.append({
                "numero": numero,
                "nome": nome,
                "posicao": posicao,
                "tipo": tipo
            })

    st.session_state.jogadores_b = jogadores_b

    st.success("✅ Cadastro atualizado!")


# ============================================================
# ABA 2 - PARTIDA
# ============================================================

with aba2:

    st.header("🏐 Partida ao vivo")

    if st.session_state.inicio is None:
        if st.button("▶️ INICIAR PARTIDA", use_container_width=True):
            st.session_state.inicio = datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )
            st.rerun()

    if st.session_state.inicio:

        st.info(
            f"⏱️ Partida iniciada em: {st.session_state.inicio}"
        )

        if not st.session_state.partida_finalizada:

            st.subheader(
                f"🏐 SET {set_atual()} — "
                f"Primeiro a {pontuacao_necessaria()} pontos, "
                "com diferença mínima de 2"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"## 🏠 {st.session_state.nome_a}"
                )

                st.markdown(
                    f"# {st.session_state.pontos_a}"
                )

                if st.button(
                    "➕ PONTO",
                    key="ponto_a",
                    use_container_width=True
                ):
                    st.session_state.pontos_a += 1
                    verificar_fim_set()
                    st.rerun()

            with col2:
                st.markdown(
                    f"## 🚩 {st.session_state.nome_b}"
                )

                st.markdown(
                    f"# {st.session_state.pontos_b}"
                )

                if st.button(
                    "➕ PONTO",
                    key="ponto_b",
                    use_container_width=True
                ):
                    st.session_state.pontos_b += 1
                    verificar_fim_set()
                    st.rerun()

            st.divider()

            # PLACAR DOS SETS
            st.subheader("📊 Placar dos sets")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    st.session_state.nome_a,
                    st.session_state.sets_a
                )

            with col2:
                st.metric(
                    "Sets",
                    len(st.session_state.sets)
                )

            with col3:
                st.metric(
                    st.session_state.nome_b,
                    st.session_state.sets_b
                )

        else:
            st.success(
                f"🏆 PARTIDA ENCERRADA — "
                f"Vencedor: {st.session_state.vencedor}"
            )

        # ----------------------------------------------------
        # SETS JÁ FINALIZADOS
        # ----------------------------------------------------

        if st.session_state.sets:

            st.subheader("📊 Resultados dos sets")

            for item in st.session_state.sets:
                st.write(
                    f"**Set {item['set']}:** "
                    f"{st.session_state.nome_a} "
                    f"{item['equipe_a']} x "
                    f"{item['equipe_b']} "
                    f"{st.session_state.nome_b} "
                    f"→ 🏆 {item['vencedor']}"
                )

        st.divider()

        # ----------------------------------------------------
        # SUBSTITUIÇÕES
        # ----------------------------------------------------

        st.subheader("🔄 Registrar substituição")

        col1, col2, col3 = st.columns(3)

        with col1:
            equipe_sub = st.selectbox(
                "Equipe",
                [
                    st.session_state.nome_a,
                    st.session_state.nome_b
                ]
            )

        with col2:
            jogador_sai = st.text_input("Jogador que saiu")

        with col3:
            jogador_entra = st.text_input("Jogador que entrou")

        if st.button("🔄 Registrar substituição"):

            if jogador_sai and jogador_entra:

                st.session_state.substituicoes.append({
                    "equipe": equipe_sub,
                    "sai": jogador_sai,
                    "entra": jogador_entra
                })

                st.success("Substituição registrada!")
                st.rerun()

        if st.session_state.substituicoes:

            for sub in st.session_state.substituicoes:
                st.write(
                    f"🔄 **{sub['equipe']}** — "
                    f"{sub['sai']} ➡️ {sub['entra']}"
                )

        st.divider()

        # ----------------------------------------------------
        # CARTÕES
        # ----------------------------------------------------

        st.subheader("🟨🟥 Cartões")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            equipe_cartao = st.selectbox(
                "Equipe",
                [
                    st.session_state.nome_a,
                    st.session_state.nome_b
                ],
                key="equipe_cartao"
            )

        with col2:
            jogador_cartao = st.text_input(
                "Jogador",
                key="jogador_cartao"
            )

        with col3:
            tipo_cartao = st.selectbox(
                "Cartão",
                ["🟨 Amarelo", "🟥 Vermelho"],
                key="tipo_cartao"
            )

        with col4:
            motivo_cartao = st.text_input(
                "Motivo",
                key="motivo_cartao"
            )

        if st.button("📝 Registrar cartão"):

            if jogador_cartao:

                st.session_state.cartoes.append({
                    "equipe": equipe_cartao,
                    "jogador": jogador_cartao,
                    "cartao": tipo_cartao,
                    "motivo": motivo_cartao
                })

                st.success("Cartão registrado!")
                st.rerun()

        st.divider()

        # ----------------------------------------------------
        # OCORRÊNCIAS
        # ----------------------------------------------------

        st.subheader("⚠️ Ocorrências")

        ocorrencia = st.text_area(
            "Descreva uma ocorrência da partida"
        )

        if st.button("➕ Registrar ocorrência"):

            if ocorrencia:
                st.session_state.ocorrencias.append(
                    ocorrencia
                )

                st.success("Ocorrência registrada!")
                st.rerun()

        for item in st.session_state.ocorrencias:
            st.write("⚠️", item)

        st.divider()

        # ----------------------------------------------------
        # ENCERRAR MANUALMENTE
        # ----------------------------------------------------

        if not st.session_state.partida_finalizada:

            if st.button(
                "⏹️ Encerrar partida",
                use_container_width=True
            ):

                st.session_state.partida_finalizada = True

                st.session_state.fim = datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

                if st.session_state.sets_a > st.session_state.sets_b:
                    st.session_state.vencedor = (
                        st.session_state.nome_a
                    )
                elif st.session_state.sets_b > st.session_state.sets_a:
                    st.session_state.vencedor = (
                        st.session_state.nome_b
                    )
                else:
                    st.session_state.vencedor = "Partida encerrada"

                salvar_partida_historico()

                st.rerun()

        if st.button("🔄 Nova partida"):
            resetar_partida()
            st.rerun()


# ============================================================
# ABA 3 - SÚMULA
# ============================================================

with aba3:

    st.header("📄 Súmula da partida")

    if not st.session_state.inicio:
        st.warning(
            "⚠️ Inicie uma partida primeiro."
        )

    elif not st.session_state.partida_finalizada:
        st.info(
            "ℹ️ A partida ainda está em andamento."
        )

    else:

        st.success(
            f"🏆 Vencedor: {st.session_state.vencedor}"
        )

        st.write(
            f"**{st.session_state.nome_a}** "
            f"{st.session_state.sets_a} x "
            f"{st.session_state.sets_b} "
            f"**{st.session_state.nome_b}**"
        )

        pdf = criar_pdf()

        st.download_button(
            label="📥 BAIXAR SÚMULA EM PDF",
            data=pdf,
            file_name="sumula_volei.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# ============================================================
# ABA 4 - HISTÓRICO
# ============================================================

with aba4:

    st.header("💾 Histórico das partidas")

    historico = carregar_historico()

    if not historico:

        st.info(
            "Nenhuma partida foi registrada ainda."
        )

    else:

        st.write(
            f"📚 Partidas registradas: **{len(historico)}**"
        )

        for i, partida in enumerate(
            reversed(historico),
            start=1
        ):

            with st.expander(
                f"🏐 {partida['equipe_a']} "
                f"{partida['sets_a']} x "
                f"{partida['sets_b']} "
                f"{partida['equipe_b']} "
                f"— {partida['data']}"
            ):

                st.write(
                    f"🏆 **Vencedor:** {partida['vencedor']}"
                )

                st.write(
                    f"📍 **Local:** {partida['local']}"
                )

                st.write(
                    f"🏆 **Campeonato:** {partida['campeonato']}"
                )

                st.write(
                    f"⏱️ **Início:** {partida['hora_inicio']}"
                )

                st.write(
                    f"⏱️ **Fim:** {partida['hora_fim']}"
                )

                st.subheader("📊 Sets")

                for item in partida["sets"]:
                    st.write(
                        f"Set {item['set']}: "
                        f"{item['equipe_a']} x "
                        f"{item['equipe_b']} "
                        f"— {item['vencedor']}"
                    )

        st.divider()

        if st.button("🗑️ Apagar histórico"):

            if os.path.exists(ARQUIVO_HISTORICO):
                os.remove(ARQUIVO_HISTORICO)

            st.success("Histórico apagado!")
            st.rerun()
