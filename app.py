import os, urllib.parse
from io import BytesIO
from datetime import datetime, timedelta
import streamlit as st
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

st.set_page_config(page_title="Astrologia Consciente | Astrolodoug", page_icon="✨", layout="wide")

st.markdown("""
<style>
.stApp { background: #2b263b; color: #f0f0f0; }
[data-testid="stSidebar"] { background: #1f1b29; color: #f0f0f0; }
h1, h2, h3 { color: #7df9ff !important; }
p, label, span { color: #dcd6f7 !important; }
.stButton > button {
    background: linear-gradient(135deg, #7df9ff 0%, #48cae4 100%) !important;
    border: 1px solid #7df9ff !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 4px 14px rgba(125, 249, 255, 0.35) !important;
    width: 100% !important;
}
.stButton > button p, .stButton > button span {
    color: #0e0b16 !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
}
.stSuccess, .stInfo, .stWarning {
    background: #1f1b29 !important;
    color: #7df9ff !important;
    border: 1px solid #7df9ff;
}
</style>
""", unsafe_allow_html=True)

SIGNOS = [("Áries","♈"),("Touro","♉"),("Gêmeos","♊"),("Câncer","♋"),("Leão","♌"),("Virgem","♍"),("Libra","♎"),("Escorpião","♏"),("Sagitário","♐"),("Capricórnio","♑"),("Aquário","♒"),("Peixes","♓")]
SIGLAS = {"Ari":"Áries","Tau":"Touro","Gem":"Gêmeos","Can":"Câncer","Leo":"Leão","Vir":"Virgem","Lib":"Libra","Sco":"Escorpião","Sag":"Sagitário","Cap":"Capricórnio","Aqu":"Aquário","Pis":"Peixes"}
GLIFOS = dict(SIGNOS)
REGENTES = {"Áries":["Marte"],"Touro":["Vênus"],"Gêmeos":["Mercúrio"],"Câncer":["Lua"],"Leão":["Sol"],"Virgem":["Mercúrio"],"Libra":["Vênus"],"Escorpião":["Marte","Plutão"],"Sagitário":["Júpiter"],"Capricórnio":["Saturno"],"Aquário":["Saturno","Urano"],"Peixes":["Júpiter","Netuno"]}
REG_TXT = {"Áries":"Marte","Touro":"Vênus","Gêmeos":"Mercúrio","Câncer":"Lua","Leão":"Sol","Virgem":"Mercúrio","Libra":"Vênus","Escorpião":"Marte e Plutão","Sagitário":"Júpiter","Capricórnio":"Saturno","Aquário":"Saturno e Urano","Peixes":"Júpiter e Netuno"}

# Regra de Orbes das Casas
ORBES_CASAS = {
    1: 10.0, 4: 10.0, 7: 10.0, 10: 10.0, # Angulares: 10°
    2: 5.0,  5: 5.0,  8: 5.0,  11: 5.0,  # Sucedentes: 5°
    3: 3.0,  6: 3.0,  9: 3.0,  12: 3.0   # Cadentes: 3°
}

CIDADES_PADRAO = [
    "São Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG", "Brasília, DF",
    "Salvador, BA", "Fortaleza, CE", "Curitiba, PR", "Recife, PE", "Porto Alegre, RS",
    "Manaus, AM", "Belém, PA", "Goiânia, GO", "Guarulhos, SP", "Campinas, SP",
    "São Luís, MA", "Maceió, AL", "Natal, RN", "Teresina, PI", "Campo Grande, MS",
    "João Pessoa, PB", "Aracaju, SE", "Cuiabá, MT", "Porto Velho, RO", "Florianópolis, SC",
    "Macapá, AP", "Rio Branco, AC", "Vitória, ES", "Boa Vista, RR", "Palmas, TO",
    "Santos, SP", "São Bernardo do Campo, SP", "Santo André, SP", "Osasco, SP",
    "Ribeirão Preto, SP", "São José dos Campos, SP", "Sorocaba, SP", "Niterói, RJ",
    "Uberlândia, MG", "Londrina, PR", "Joinville, SC", "Caxias do Sul, RS",
    "Lisboa, Portugal", "Porto, Portugal", "Outra (digitar manualmente)"
]

def obter_dado(obj, chave, padrao=0.0):
    if isinstance(obj, dict): return obj.get(chave, padrao)
    return getattr(obj, chave, padrao)

def nome_sig(r):
    s = str(r).strip()[:3].capitalize()
    return SIGLAS.get(s, str(r).strip())

def fmt_sig(r):
    n = nome_sig(r)
    return f"{GLIFOS.get(n,'✨')} {n}"

def fmt_g(g):
    g = g % 360
    idx, sob = int(g // 30), g % 30
    n, gl = SIGNOS[idx]
    return f"{sob:.2f}° {gl} ({n})"

def calc_casa_orbe(p_abs, cuspides_dict):
    p_abs = p_abs % 360
    for h in range(1, 13):
        c_at = cuspides_dict[h]
        prox_h = 1 if h == 12 else h + 1
        c_pr = cuspides_dict[prox_h]
        tam = (c_pr - c_at) % 360
        dist_ini = (p_abs - c_at) % 360
        if 0 <= dist_ini < tam:
            dist_prox = tam - dist_ini
            orbe_prox = ORBES_CASAS[prox_h]
            if dist_prox <= orbe_prox:
                return prox_h, True, orbe_prox
            return h, False, 0.0
    return 1, False, 0.0

def svg_mandala(subj):
    try:
        data = ChartDataFactory.create_natal_chart_data(subj)
        return ChartDrawer(data).generate_svg_string()
    except Exception:
        return None

def seguro_latin(t):
    return str(t).encode('latin-1', 'replace').decode('latin-1')

def fabricar_pdf(nome_c, cid_c, dt_ref, tab_pont_raw, tab_proj_raw):
    if not REPORTLAB_DISPONIVEL: return None
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(45, 800, seguro_latin("Astrologia Consciente | Relatório Preditivo"))
    c.setFont("Helvetica", 10)
    c.drawString(45, 782, seguro_latin(f"Consulente: {nome_c} | Local: {cid_c}"))
    c.drawString(45, 768, seguro_latin(f"Data de Referência da Análise: {dt_ref}"))
    c.drawString(45, 754, seguro_latin("Método: A Dança dos Ponteiros & APRS (Douglas Rosa - @astrolodoug)"))
    c.line(45, 744, 550, 744)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(45, 725, seguro_latin("1. Posicionamento Atual dos 9 Ponteiros"))
    c.setFont("Helvetica", 9)
    y = 705
    for item in tab_pont_raw:
        txt = f"• {item['Ponteiro']}: {item['Pos']} | {item['Reg']}"
        c.drawString(55, y, seguro_latin(txt))
        y -= 16

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(45, y, seguro_latin("2. Projeção Preditiva dos Próximos 12 Meses"))
    y -= 20
    c.setFont("Helvetica", 9)
    for p in tab_proj_raw:
        txt_proj = f"• {p['Data']}: {p['Ponteiro']} em {p['Aspecto']} ({p['Regência']})"
        c.drawString(55, y, seguro_latin(txt_proj))
        y -= 16

    y -= 15
    c.line(45, y, 550, y)
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, y, seguro_latin("Direcionamento Estratégico:"))
    y -= 16
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(45, y, seguro_latin("• Saturno e tensões apontam os setores de rigor e maturidade necessária."))
    y -= 14
    c.drawString(45, y, seguro_latin("• Júpiter e Plutão sinalizam janelas de expansão e visibilidade profissional."))
    y -= 25
    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, y, seguro_latin("Atendimentos e Estudos: WhatsApp (11) 97711-7024 | Instagram @astrolodoug"))
    c.save()
    buf.seek(0)
    return buf.getvalue()

st.title("✨ Astrologia Consciente")
st.markdown("### A Dança dos Ponteiros: Relatório Preditivo e Mandala")

st.sidebar.header("Dados do Consulente")
nome = st.sidebar.text_input("Nome Completo", "Douglas Rosa")

cid_selecionada = st.sidebar.selectbox("Cidade de Nascimento", CIDADES_PADRAO, index=0)
if cid_selecionada == "Outra (digitar manualmente)":
    cidade = st.sidebar.text_input("Digite sua cidade e estado/país:", value="Campinas, SP")
else:
    cidade = cid_selecionada

ano = st.sidebar.number_input("Ano", 1900, 2100, 1989)
mes = st.sidebar.number_input("Mês", 1, 12, 7)
dia = st.sidebar.number_input("Dia", 1, 31, 13)
hora = st.sidebar.number_input("Hora", 0, 23, 14)
minuto = st.sidebar.number_input("Minuto", 0, 59, 30)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Período de Análise")
data_analise_input = st.sidebar.date_input("Data de Referência", value=datetime(2026, 10, 11))
DATA_ANALISE = datetime.combine(data_analise_input, datetime.min.time())

FATORES = [("Ponteiro Solar",1.0,"Sol"),("Ponteiro de Mercúrio",1.066,"Mercúrio"),("Ponteiro de Vênus",1.133,"Vênus"),("Ponteiro de Marte",1.2,"Marte"),("Ponteiro de Júpiter",1.26,"Júpiter"),("Ponteiro de Saturno",1.32,"Saturno"),("Ponteiro de Urano",1.38,"Urano"),("Ponteiro de Netuno",1.44,"Netuno"),("Ponteiro de Plutão",1.5,"Plutão")]

btn_gerar = st.sidebar.button("🔮 Gerar Mapa, Mandala e Relatório")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📲 Conecte-se com Douglas Rosa")
st.sidebar.link_button("💬 Conversar no WhatsApp", "https://wa.me/5511977117024", use_container_width=True)
st.sidebar.link_button("📸 Seguir no Instagram", "https://instagram.com/astrolodoug?dlrf=MWMyd2ZsendvemtnMQ%3D%3D", use_container_width=True)
st.sidebar.link_button("▶️ Acessar Canal no YouTube", "https://youtube.com/@astrolodoug?si=YimzRQs7yL1jJMSO", use_container_width=True)

if btn_gerar:
    with st.spinner("A processar cálculos astrológicos..."):
        try:
            geo = Nominatim(user_agent="astrolodoug_app")
            loc = geo.geocode(cidade)
            if not loc:
                st.error("Cidade não encontrada.")
            else:
                lat, lng = loc.latitude, loc.longitude
                tf = TimezoneFinder()
                tz_str = tf.timezone_at(lng=lng, lat=lat) or "UTC"

                sujeito = AstrologicalSubjectFactory.from_birth_data(name=nome, year=int(ano), month=int(mes), day=int(dia), hour=int(hora), minute=int(minuto), lat=float(lat), lng=float(lng), tz_str=tz_str)
                st.success(f"Mapa gerado: {nome} ({cidade}) | Data base: {DATA_ANALISE.strftime('%d/%m/%Y')}")

                st.markdown("---")
                st.markdown("### 🔵 Mandala Astrológica (Roda do Mapa Natal)")
                svg = svg_mandala(sujeito)
                if svg: st.components.v1.html(svg, height=650, scrolling=True)

                casas_ref = [("1ª Casa (Ascendente)", sujeito.first_house, 1), ("2ª Casa", sujeito.second_house, 2), ("3ª Casa", sujeito.third_house, 3), ("4ª Casa (Fundo do Céu)", sujeito.fourth_house, 4), ("5ª Casa", sujeito.fifth_house, 5), ("6ª Casa", sujeito.sixth_house, 6), ("7ª Casa (Descendente)", sujeito.seventh_house, 7), ("8ª Casa", sujeito.eighth_house, 8), ("9ª Casa", sujeito.ninth_house, 9), ("10ª Casa (Meio do Céu)", sujeito.tenth_house, 10), ("11ª Casa", sujeito.eleventh_house, 11), ("12ª Casa", sujeito.twelfth_house, 12)]
                
                # Mapeamento de Cúspides Absolutas para Cálculo de Orbes
                cuspides_abs = {num: float(obter_dado(oc, 'abs_pos', 0.0)) for _, oc, num in casas_ref}
                casas_p = {p: [] for p in ["Sol","Lua","Mercúrio","Vênus","Marte","Júpiter","Saturno","Urano","Netuno","Plutão"]}

                tab_c = []
                for nc, oc, num in casas_ref:
                    sn = nome_sig(obter_dado(oc, 'sign', ''))
                    for r in REGENTES.get(sn, []):
                        if r in casas_p: casas_p[r].append(f"Casa {num}")
                    pos_c = float(obter_dado(oc, 'position', 0.0))
                    tab_c.append({"Casa Astrológica": nc, "Cúspide": f"{pos_c:.2f}° {fmt_sig(sn)}", "Regentes": REG_TXT.get(sn, "Desconhecido")})

                st.markdown("---")
                st.markdown("### 🏛️ Cúspides e Regências das Casas Natais")
                st.table(tab_c)

                planetas_dados = [("Sol", sujeito.sun), ("Lua", sujeito.moon), ("Mercúrio", sujeito.mercury), ("Vênus", sujeito.venus), ("Marte", sujeito.mars), ("Júpiter", sujeito.jupiter), ("Saturno", sujeito.saturn), ("Urano", sujeito.uranus), ("Netuno", sujeito.neptune), ("Plutão", sujeito.pluto)]
                
                # Aplicação da Regra de Orbes Dinâmicas
                tab_pl = []
                for pn, po in planetas_dados:
                    p_abs = float(obter_dado(po, 'abs_pos', 0.0))
                    num_casa, por_orbe, orbe_val = calc_casa_orbe(p_abs, cuspides_abs)
                    rotulo_casa = f"{num_casa}ª Casa (orbe de {int(orbe_val)}°)" if por_orbe else f"{num_casa}ª Casa"
                    pos_p = float(obter_dado(po, 'position', 0.0))
                    tab_pl.append({
                        "Planeta": pn,
                        "Posição": f"{pos_p:.2f}° {fmt_sig(obter_dado(po, 'sign', ''))}",
                        "Casa Natal (com Orbe)": rotulo_casa,
                        "Regente": REG_TXT.get(nome_sig(obter_dado(po, 'sign', '')), "Desconhecido")
                    })

                st.markdown("---")
                st.markdown("### 🪐 Posicionamentos Natais nas Casas (com Orbes de Cúspides)")
                st.caption("ℹ️ Orbes aplicadas: 10° antes das Casas Angulares (1, 4, 7, 10) | 5° antes das Sucedentes (2, 5, 8, 11) | 3° antes das Cadentes (3, 6, 9, 12).")
                st.table(tab_pl)

                def reg_de(p):
                    c = casas_p.get(p, [])
                    return f"Regente das {', '.join(c)}" if c else "Eixo Angular"

                dt_nasc = datetime(int(ano), int(mes), int(dia), int(hora), int(minuto))
                dias_v = (DATA_ANALISE - dt_nasc).days
                asc_b = float(obter_dado(sujeito.first_house, 'abs_pos', 0.0))

                tab_pont = [{"Ponteiro": pn, "Posição Atual": fmt_g((asc_b + (dias_v / 0.25 / ft)) % 360), "Fator": f"{ft:.3f}", "Regência Ativada": reg_de(pb)} for pn, ft, pb in FATORES]
                st.markdown("---")
                st.markdown(f"### 🔭 Os 9 Ponteiros Ativos em {DATA_ANALISE.strftime('%d/%m/%Y')}")
                st.table(tab_pont)

                trans_atuais = [("Netuno","Quadratura","Urano Natal","Urano"),("Plutão","Trígono","Sol Natal","Sol"),("Saturno","Conjunção","Meio do Céu","Saturno"),("Júpiter","Sextil","Vênus Natal","Vênus")]
                tab_ta = [{"Trânsito": t, "Aspecto": a, "Natal Alvo": n, "Regência Ativada": f"{p} {reg_de(p)}"} for t, a, n, p in trans_atuais]
                st.markdown("---")
                st.markdown(f"### ⚡ Trânsitos de Planetas Lentos ({DATA_ANALISE.strftime('%d/%m/%Y')})")
                st.table(tab_ta)

                proj_pont = [(15,"Ponteiro de Mercúrio","Conjunção","Sol Natal","Sol"),(45,"Ponteiro de Vênus","Sextil","Lua Natal","Lua"),(90,"Ponteiro Solar","Quadratura","Marte Natal","Marte"),(150,"Ponteiro de Marte","Trígono","Meio do Céu","Sol"),(210,"Ponteiro de Júpiter","Oposição","Vênus Natal","Vênus"),(270,"Ponteiro de Saturno","Sextil","Ascendente","Marte"),(320,"Ponteiro de Urano","Trígono","Mercúrio Natal","Mercúrio"),(350,"Ponteiro de Netuno","Conjunção","Saturno Natal","Saturno")]
                tab_fp = [{"Data": (DATA_ANALISE + timedelta(days=d)).strftime('%d/%m/%Y'), "Ponteiro": pt, "Aspecto": f"{asp} com {alvo}", "Regência": reg_de(p)} for d, pt, asp, alvo, p in proj_pont]

                # =======================================================
                # PORTAL DE CAPTAÇÃO E ENVIO MULTICANAL (PDF / WHATSAPP / E-MAIL)
                # =======================================================
                st.markdown("---")
                st.markdown("## 🔒 Desbloqueie a Projeção de 12 Meses & Receba o seu Resumo")
                st.info("Insira o seu WhatsApp ou E-mail para desbloquear as ativações do próximo ano e escolher como deseja receber o seu resumo:")

                c_lead1, c_lead2 = st.columns([3, 1])
                contato_in = c_lead1.text_input("WhatsApp (com DDD) ou E-mail:", placeholder="ex: 11999998888 ou seu@email.com")

                if contato_in:
                    with open("leads.csv", "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')};{nome};{cidade};{contato_in}\n")

                    tab_pont_pdf = [{"Ponteiro": it["Ponteiro"], "Pos": it["Posição Atual"], "Reg": it["Regência Ativada"]} for it in tab_pont]
                    pdf_bytes = fabricar_pdf(nome, cidade, DATA_ANALISE.strftime('%d/%m/%Y'), tab_pont_pdf, tab_fp)

                    st.success("✅ Acesso liberado! Escolha abaixo como deseja descarregar ou receber o seu resumo:")

                    # Preparação do Texto Formatado para WhatsApp e E-mail
                    txt_whats = f"✨ *Astrologia Consciente | A Dança dos Ponteiros*\n"
                    txt_whats += f"👤 *Consulente:* {nome} ({cidade})\n"
                    txt_whats += f"📅 *Data Base:* {DATA_ANALISE.strftime('%d/%m/%Y')}\n\n"
                    txt_whats += "🔭 *Principais Ponteiros Ativos:*\n"
                    for p_it in tab_pont[:4]:
                        txt_whats += f"• {p_it['Ponteiro']}: {p_it['Posição Atual']}\n"
                    txt_whats += "\n📅 *Próximas Ativações (12 Meses):*\n"
                    for pr_it in tab_fp[:3]:
                        txt_whats += f"• {pr_it['Data']}: {pr_it['Ponteiro']} em {pr_it['Aspecto']}\n"
                    txt_whats += "\n🌟 *Idealizador:* Douglas Rosa (@astrolodoug) | wa.me/5511977117024"

                    txt_encoded = urllib.parse.quote(txt_whats)
                    
                    digitos_tel = ''.join(filter(str.isdigit, contato_in))
                    if len(digitos_tel) in [10, 11] and not digitos_tel.startswith('55'):
                        num_whats = "55" + digitos_tel
                    else:
                        num_whats = digitos_tel

                    link_whatsapp = f"https://api.whatsapp.com/send?phone={num_whats}&text={txt_encoded}" if num_whats else f"https://api.whatsapp.com/send?text={txt_encoded}"
                    link_email = f"mailto:{contato_in if '@' in contato_in else ''}?subject={urllib.parse.quote('Seu Resumo Astrológico | Astrologia Consciente')}&body={txt_encoded}"

                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if pdf_bytes:
                            st.download_button(
                                label="📥 Baixar PDF Completo",
                                data=pdf_bytes,
                                file_name=f"Relatorio_{nome.replace(' ','_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                    with col_btn2:
                        st.link_button("📲 Salvar no WhatsApp", link_whatsapp, use_container_width=True)
                    with col_btn3:
                        st.link_button("✉️ Enviar para meu E-mail", link_email, use_container_width=True)

                    st.markdown("---")
                    st.markdown(f"### 📅 Projeção dos 9 Ponteiros (12 Meses a partir de {DATA_ANALISE.strftime('%d/%m/%Y')})")
                    st.table(tab_fp)

                    proj_len = [(30,"Saturno em Trânsito","Sextil","Sol Natal","Sol"),(90,"Urano em Trânsito","Trígono","Lua Natal","Lua"),(160,"Júpiter em Trânsito","Conjunção","Ascendente","Marte"),(220,"Netuno em Trânsito","Oposição","Mercúrio Natal","Mercúrio"),(300,"Plutão em Trânsito","Sextil","Meio do Céu","Sol"),(355,"Saturno em Trânsito","Trígono","Vênus Natal","Vênus")]
                    tab_fl = [{"Data": (DATA_ANALISE + timedelta(days=d)).strftime('%d/%m/%Y'), "Planeta Lento": t, "Aspecto": f"{asp} com {alvo}", "Regência": reg_de(p)} for d, t, asp, alvo, p in proj_len]
                    st.markdown("---")
                    st.markdown(f"### 📅 Projeção de Trânsitos Lentos (12 Meses a partir de {DATA_ANALISE.strftime('%d/%m/%Y')})")
                    st.table(tab_fl)

                    st.markdown("---")
                    st.markdown("## 🧠 Síntese Interpretativa e Direcionamento Consciente")
                    ce, cd = st.columns(2)
                    with ce:
                        st.markdown("### ⚠️ Setores de Tensão Construtiva")
                        st.warning("Carreira (Casa 10): Saturno exige disciplina e método.")
                        st.warning("Emocional (Casas de Água): Netuno pede discernimento e limites.")
                        st.info("Orientação: Encare a tensão como filtro de maturidade.")
                    with cd:
                        st.markdown("### ✨ Setores de Fluxo Positivo")
                        st.success("Oportunidades: Plutão e Júpiter trazem reconhecimento público.")
                        st.success("Ensino e Expansão: Sol e Vênus favorecem alianças sólidas.")
                        st.info("Orientação: Momento ideal para difundir a Astrologia Consciente.")
                else:
                    st.warning("👆 Digite o seu WhatsApp ou E-mail no campo acima para desbloquear a projeção dos próximos 12 meses e receber o seu resumo.")

        except Exception as e:
            st.error(f"Erro ao processar: {e}")
else:
    t1, t2, t3 = st.tabs(["🌟 Sobre o Projeto & Quem Sou Eu", "⏱️ A Dança dos Ponteiros", "📖 Mini Glossário Consciente"])

    with t1:
        st.markdown("#### Boas-vindas à Astrologia Consciente")
        st.info("A Astrologia Consciente é uma abordagem técnica, empírica e investigativa concebida para superar generalizações e fatalismos. Aqui, o mapa astral é compreendido como uma matriz viva de potenciais e ciclos exatos.")
        st.markdown("**Quem é Douglas Rosa (@astrolodoug)?**")
        st.write("Pesquisador astrológico e comunicador, Douglas dedica-se ao resgate da astrologia séria, integrando tradição, ciclos mundiais e técnicas preditivas de precisão matemática para transformar o simbolismo celeste em estratégia prática de vida.")
        st.markdown("---")
        st.markdown("##### 📲 Conecte-se e Agende uma Consulta:")
        cb1, cb2, cb3 = st.columns(3)
        with cb1: st.link_button("💬 Conversar no WhatsApp", "https://wa.me/5511977117024", use_container_width=True)
        with cb2: st.link_button("📸 Seguir no Instagram", "https://instagram.com/astrolodoug?dlrf=MWMyd2ZsendvemtnMQ%3D%3D", use_container_width=True)
        with cb3: st.link_button("▶️ Assistir no YouTube", "https://youtube.com/@astrolodoug?si=YimzRQs7yL1jJMSO", use_container_width=True)

    with t2:
        st.markdown("#### O que é a Dança dos Ponteiros?")
        st.write("A Dança dos Ponteiros é uma técnica preditiva desenvolvida a partir do estudo do Ascendente Progredido dos Retornos (APRS).")
        st.write("Assim como num relógio os ponteiros das horas, minutos e segundos movem-se a velocidades distintas, no céu do consulente cada um dos 9 astros (do Sol a Plutão) atua como um ponteiro vivo.")
        st.write("À medida que esses ponteiros avançam no zodíaco, ativam planetas natais e cúspides, indicando o timing exato em que novas oportunidades se abrem ou velhas estruturas exigem amadurecimento.")

    with t3:
        st.markdown("#### Mini Glossário: A Gramática Celeste")
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.markdown("**🪐 Os Planetas (O 'Quê')**")
            st.caption("Representam as forças e funções psíquicas fundamentais:")
            st.write("• **Sol:** Essência, consciência e identidade.")
            st.write("• **Lua:** Emoções, nutrição e memória.")
            st.write("• **Mercúrio:** Mente, comunicação e trocas.")
            st.write("• **Vênus:** Afeto, valores e harmonia.")
            st.write("• **Marte:** Ação, coragem e iniciativa.")
            st.write("• **Júpiter:** Expansão, sabedoria e visão.")
            st.write("• **Saturno:** Estrutura, limites e tempo.")
            st.write("• **Urano:** Inovação, liberdade e rupturas.")
            st.write("• **Netuno:** Inspiração, sensibilidade e sonhos.")
            st.write("• **Plutão:** Transformação, poder e renascimento.")
        with col_g2:
            st.markdown("**♈ Os Signos (O 'Como')**")
            st.caption("Filtros arquetípicos que conferem tom à ação:")
            st.write("• **Fogo (Áries, Leão, Sagitário):** Entusiasmo, vitalidade e impulso.")
            st.write("• **Terra (Touro, Virgem, Capricórnio):** Realismo, matéria e estabilidade.")
            st.write("• **Ar (Gêmeos, Libra, Aquário):** Ideias, intelecto e conexões.")
            st.write("• **Água (Câncer, Escorpião, Peixes):** Intuição, profundidade e sensibilidade.")
        with col_g3:
            st.markdown("**🏛️ As Casas (O 'Onde')**")
            st.caption("As 12 arenas práticas da experiência humana:")
            st.write("• **1ª / 2ª:** Identidade/Corpo e Recursos/Finanças.")
            st.write("• **3ª / 4ª:** Comunicação/Ambiente e Lar/Raízes.")
            st.write("• **5ª / 6ª:** Criatividade/Autoexpressão e Rotina/Trabalho.")
            st.write("• **7ª / 8ª:** Parcerias/O Outro e Transformações/Partilha.")
            st.write("• **9ª / 10ª:** Conhecimento/Viagens e Carreira/Propósito.")
            st.write("• **11ª / 12ª:** Coletivo/Projetos e Inconsciente/Espiritualidade.")

    st.markdown("---")
    st.info("👈 Para começar, defina os dados natais e a data de análise na barra lateral e clique em **'🔮 Gerar Mapa, Mandala e Relatório'**.")
