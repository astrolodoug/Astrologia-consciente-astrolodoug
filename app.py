import os, json, ssl, math, textwrap, urllib.request, urllib.parse
from io import BytesIO
from datetime import datetime, timedelta
import streamlit as st
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

st.set_page_config(page_title="Astrologia Consciente | Astrolodoug", page_icon="✨", layout="wide")

if "mapa_gerado" not in st.session_state:
    st.session_state.mapa_gerado = False
if "contato_salvo" not in st.session_state:
    st.session_state.contato_salvo = ""

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

ORBES_CASAS = {
    1: 10.0, 4: 10.0, 7: 10.0, 10: 10.0,
    2: 5.0,  5: 5.0,  8: 5.0,  11: 5.0,
    3: 3.0,  6: 3.0,  9: 3.0,  12: 3.0
}

POTENCIAL_CASAS = {
    1: "Liderança nata, autonomia e pioneirismo no desenvolvimento da própria identidade.",
    2: "Capacidade de estruturação financeira, gestão de recursos e monetização de talentos.",
    3: "Poder de comunicação, articulação estratégica, ensino e criação de redes sociais.",
    4: "Construção de bases emocionais e familiares sólidas, imobiliário e valorização de raízes.",
    5: "Expressão criativa genuína, magnetismo pessoal, autoridade autoral e capacidade empreendedora.",
    6: "Aperfeiçoamento contínuo, domínio de técnicas refinadas, método e gestão da rotina.",
    7: "Habilidade diplomática para fechar parcerias estratégicas, contratos e negociações.",
    8: "Poder de transformação profunda, superação de crises e gestão de investimentos partilhados.",
    9: "Visão filosófica ampla, expansão acadêmica, internacionalização e transmissão de sabedoria.",
    10: "Construção de autoridade profissional, liderança pública, reputação e legado de carreira.",
    11: "Articulação de grandes projetos coletivos, impacto comunitário e visão de futuro inovadora.",
    12: "Sensibilidade intuitiva refinada, compreensão psíquica e talento para atuar nos bastidores."
}

ESTADOS_BR = [
    "SP - São Paulo", "RJ - Rio de Janeiro", "MG - Minas Gerais", "BA - Bahia",
    "PR - Paraná", "RS - Rio Grande do Sul", "PE - Pernambuco", "CE - Ceará", "PA - Pará",
    "AC - Acre", "AP - Amapá", "RR - Roraima", "SC - Santa Catarina", "GO - Goiás",
    "MA - Maranhão", "AM - Amazonas", "ES - Espírito Santo", "PB - Paraíba",
    "RN - Rio Grande do Norte", "MT - Mato Grosso", "AL - Alagoas", "PI - Piauí",
    "DF - Distrito Federal", "MS - Mato Grosso do Sul", "SE - Sergipe", "RO - Rondônia", "TO - Tocantins"
]

CIDADES_AC = sorted(["Acrelândia", "Assis Brasil", "Brasiléia", "Bujari", "Capixaba", "Cruzeiro do Sul", "Epitaciolândia", "Feijó", "Jordão", "Mâncio Lima", "Manoel Urbano", "Marechal Thaumaturgo", "Plácido de Castro", "Porto Acre", "Porto Walter", "Rio Branco", "Rodrigues Alves", "Santa Rosa do Purus", "Sena Madureira", "Senador Guiomard", "Tarauacá", "Xapuri"])
CIDADES_AP = sorted(["Amapá", "Calçoene", "Cutias", "Ferreira Gomes", "Itaubal", "Laranjal do Jari", "Macapá", "Mazagão", "Oiapoque", "Pedra Branca do Amapari", "Porto Grande", "Pracuúba", "Santana", "Serra do Navio", "Tartarugalzinho", "Vitória do Jari"])
CIDADES_RR = sorted(["Alto Alegre", "Amajari", "Boa Vista", "Bonfim", "Cantá", "Caracaraí", "Caroebe", "Iracema", "Mucajaí", "Normandia", "Pacaraima", "Rorainópolis", "São João da Baliza", "São Luiz", "Uiramutã"])
CIDADES_RJ = sorted(["Angra dos Reis", "Aperibé", "Araruama", "Areal", "Armação dos Búzios", "Arraial do Cabo", "Barra do Piraí", "Barra Mansa", "Belford Roxo", "Bom Jardim", "Bom Jesus do Itabapoana", "Cabo Frio", "Cachoeiras de Macacu", "Cambuci", "Campos dos Goytacazes", "Cantagalo", "Carapebus", "Cardoso Moreira", "Carmo", "Casimiro de Abreu", "Comendador Levy Gasparian", "Conceição de Macabu", "Cordeiro", "Duas Barras", "Duque de Caxias", "Engenheiro Paulo de Frontin", "Guapimirim", "Iguaba Grande", "Itaboraí", "Itaguaí", "Italva", "Itaocara", "Itaperuna", "Itatiaia", "Japeri", "Laje do Muriaé", "Macaé", "Macuco", "Magé", "Mangaratiba", "Maricá", "Mendes", "Mesquita", "Miguel Pereira", "Miracema", "Natividade", "Nilópolis", "Niterói", "Nova Friburgo", "Nova Iguaçu", "Paracambi", "Paraíba do Sul", "Paraty", "Paty do Alferes", "Petrópolis", "Pinheiral", "Piraí", "Porciúncula", "Porto Real", "Quatis", "Queimados", "Quissamã", "Resende", "Rio Bonito", "Rio Claro", "Rio das Flores", "Rio das Ostras", "Rio de Janeiro", "Santa Maria Madalena", "Santo Antônio de Pádua", "São Fidélis", "São Francisco de Itabapoana", "São Gonçalo", "São João da Barra", "São João de Meriti", "São José de Ubá", "São José do Vale do Rio Preto", "São Pedro da Aldeia", "São Sebastião do Alto", "Saquarema", "Seropédica", "Silva Jardim", "Sumidouro", "Tanguá", "Teresópolis", "Trajano de Moraes", "Três Rios", "Valença", "Varre-Sai", "Vassouras", "Volta Redonda"])
CIDADES_BA = sorted(["Abaíra", "Abaré", "Acajutiba", "Alagoinhas", "Alcobaça", "Amargosa", "Barreiras", "Bom Jesus da Lapa", "Brumado", "Camaçari", "Cruz das Almas", "Eunápolis", "Feira de Santana", "Guanambi", "Ilhéus", "Irecê", "Itabuna", "Itacaré", "Jacobina", "Jequié", "Juazeiro", "Lauro de Freitas", "Lençóis", "Paulo Afonso", "Porto Seguro", "Salvador", "Senhor do Bonfim", "Serrinha", "Simões Filho", "Teixeira de Freitas", "Valença", "Vitória da Conquista", "Xique-Xique"])
CIDADES_PR = sorted(["Apucarana", "Arapongas", "Araucária", "Campo Mourão", "Cascavel", "Castro", "Cianorte", "Colombo", "Curitiba", "Fazenda Rio Grande", "Foz do Iguaçu", "Francisco Beltrão", "Guarapuava", "Londrina", "Maringá", "Paranaguá", "Paranavaí", "Pato Branco", "Pinhais", "Ponta Grossa", "São José dos Pinhais", "Sarandi", "Telêmaco Borba", "Toledo", "Umuarama", "União da Vitória"])
CIDADES_RS = sorted(["Alegrete", "Alvorada", "Bagé", "Bento Gonçalves", "Cachoeirinha", "Camaquã", "Canoas", "Caxias do Sul", "Cruz Alta", "Erechim", "Esteio", "Farroupilha", "Gravataí", "Ijuí", "Lajeado", "Novo Hamburgo", "Passo Fundo", "Pelotas", "Porto Alegre", "Rio Grande", "Santa Cruz do Sul", "Santa Maria", "Santa Rosa", "Sant'Ana do Livramento", "São Leopoldo", "Sapucaia do Sul", "Uruguaiana", "Vacaria", "Viamão"])
CIDADES_PE = sorted(["Abreu e Lima", "Araripina", "Arcoverde", "Belo Jardim", "Cabo de Santo Agostinho", "Camaragibe", "Carpina", "Caruaru", "Garanhuns", "Gravatá", "Igarassu", "Ipojuca", "Jaboatão dos Guararapes", "Olinda", "Paudalho", "Paulista", "Pesqueira", "Petrolina", "Recife", "Santa Cruz do Capibaribe", "Serra Talhada", "Vitória de Santo Antão"])
CIDADES_CE = sorted(["Aquiraz", "Aracati", "Barbalha", "Baturité", "Camocim", "Canindé", "Cascavel", "Caucaia", "Crateús", "Crato", "Eusébio", "Fortaleza", "Iguatu", "Itapipoca", "Juazeiro do Norte", "Maracanaú", "Maranguape", "Morada Nova", "Quixadá", "Quixeramobim", "Russas", "Sobral", "Tianguá"])
CIDADES_PA = sorted(["Abaetetuba", "Altamira", "Ananindeua", "Barcarena", "Belém", "Bragança", "Cametá", "Capanema", "Castanhal", "Itaituba", "Marabá", "Marituba", "Paragominas", "Parauapebas", "Redenção", "Salinópolis", "Santarém", "Tailândia", "Tucuruí"])
CIDADES_MG_BASE = sorted(["Belo Horizonte", "Betim", "Contagem", "Divinópolis", "Governador Valadares", "Ipatinga", "Juiz de Fora", "Montes Claros", "Poços de Caldas", "Pouso Alegre", "Ribeirão das Neves", "Sete Lagoas", "Uberaba", "Uberlândia", "Varginha"])
CIDADES_SP_BASE = sorted(["São Paulo", "Guarulhos", "Campinas", "São Bernardo do Campo", "Santo André", "São José dos Campos", "Osasco", "Ribeirão Preto", "Sorocaba", "Santos", "Mauá", "São José do Rio Preto", "Mogi das Cruzes", "Diadema", "Jundiaí", "Piracicaba", "Bauru", "Franca", "Praia Grande", "Taubaté"])

@st.cache_data(ttl=86400, show_spinner=False)
def carregar_municipios(sigla_uf):
    mapa_direto = {"AC": CIDADES_AC, "AP": CIDADES_AP, "RR": CIDADES_RR, "RJ": CIDADES_RJ, "BA": CIDADES_BA, "PR": CIDADES_PR, "RS": CIDADES_RS, "PE": CIDADES_PE, "CE": CIDADES_CE, "PA": CIDADES_PA}
    if sigla_uf in mapa_direto:
        return mapa_direto[sigla_uf]
    try:
        url_bapi = f"https://brasilapi.com.br/api/ibge/municipios/v1/{sigla_uf}"
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url_bapi, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            if dados and isinstance(dados, list):
                return sorted([m['nome'] for m in dados])
    except Exception:
        pass
    if sigla_uf == "MG": return CIDADES_MG_BASE
    if sigla_uf == "SP": return CIDADES_SP_BASE
    return ["Capital"]

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
    return f"{sob:.2f}° {gl} {n}"

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

# ==================== CARREGAMENTO AUTOMÁTICO DE FONTE UNICODE ====================
FONTE_UNICODE_NOME = "Helvetica"
UNICODE_ATIVA = False

def garantir_fonte_unicode():
    global FONTE_UNICODE_NOME, UNICODE_ATIVA
    if not REPORTLAB_DISPONIVEL:
        return
    caminho_local = "DejaVuSans.ttf"
    if not os.path.exists(caminho_local):
        locais = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/DejaVuSans.ttf"
        ]
        for loc in locais:
            if os.path.exists(loc):
                caminho_local = loc
                break

    if not os.path.exists(caminho_local):
        urls = [
            "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@master/resources/DejaVuSans.ttf",
            "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/resources/DejaVuSans.ttf"
        ]
        for u in urls:
            try:
                ctx = ssl._create_unverified_context()
                req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                    with open("DejaVuSans.ttf", "wb") as f:
                        f.write(resp.read())
                if os.path.exists("DejaVuSans.ttf") and os.path.getsize("DejaVuSans.ttf") > 100000:
                    caminho_local = "DejaVuSans.ttf"
                    break
            except Exception:
                pass

    if os.path.exists(caminho_local):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuUnicode", caminho_local))
            FONTE_UNICODE_NOME = "DejaVuUnicode"
            UNICODE_ATIVA = True
        except Exception:
            pass

garantir_fonte_unicode()

def seguro_texto(t):
    subst_base = {'–': '-', '—': '-', '“': '"', '”': '"', '’': "'", '‘': "'", '•': ''}
    texto = str(t)
    for k, v in subst_base.items():
        texto = texto.replace(k, v)
    if not UNICODE_ATIVA:
        clean = [ch for ch in texto if ord(ch) < 256]
        return "".join(clean)
    return texto

def desenhar_marcador(c, x, y, cor=HexColor('#0d47a1'), raio=2.5):
    c.setFillColor(cor)
    p = c.beginPath()
    p.moveTo(x, y + raio + 1)
    p.lineTo(x + raio + 1, y)
    p.lineTo(x, y - raio - 1)
    p.lineTo(x - raio - 1, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

# ==================== MOTOR VETORIAL DA MANDALA DO SITE ====================
def desenhar_mandala_astrologica_vetorial(c, cx, cy, raio, asc_abs, cuspides_abs, planetas_plot):
    c.setFillColor(HexColor('#1f1b29'))
    c.circle(cx, cy, raio, stroke=0, fill=1)

    c.setStrokeColor(HexColor('#0d47a1'))
    c.setLineWidth(1.5)
    c.circle(cx, cy, raio, stroke=1, fill=0)

    r_zodiaco_in = raio - 16
    c.setStrokeColor(HexColor('#3a3350'))
    c.setLineWidth(0.8)
    c.circle(cx, cy, r_zodiaco_in, stroke=1, fill=0)

    glifos_ordem = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i in range(12):
        grau_ini = i * 30.0
        ang_canto = (180.0 - (grau_ini - asc_abs)) % 360
        ang_rad = math.radians(ang_canto)
        x_div_out = cx + raio * math.cos(ang_rad)
        y_div_out = cy + raio * math.sin(ang_rad)
        x_div_in = cx + r_zodiaco_in * math.cos(ang_rad)
        y_div_in = cy + r_zodiaco_in * math.sin(ang_rad)
        c.setStrokeColor(HexColor('#3a3350'))
        c.setLineWidth(0.6)
        c.line(x_div_in, y_div_in, x_div_out, y_div_out)

        ang_centro = math.radians((180.0 - ((grau_ini + 15.0) - asc_abs)) % 360)
        r_txt = raio - 9
        xg = cx + r_txt * math.cos(ang_centro)
        yg = cy + r_txt * math.sin(ang_centro) - 3.5
        c.setFillColor(HexColor('#7df9ff'))
        c.setFont(FONTE_UNICODE_NOME, 7.5)
        c.drawCentredString(xg, yg, glifos_ordem[i] if UNICODE_ATIVA else str(i+1))

    r_hub = 22
    c.setFillColor(HexColor('#102a43'))
    c.setStrokeColor(HexColor('#0d47a1'))
    c.setLineWidth(1)
    c.circle(cx, cy, r_hub, stroke=1, fill=1)
    c.setFillColor(HexColor('#7df9ff'))
    c.setFont(FONTE_UNICODE_NOME, 5.5)
    c.drawCentredString(cx, cy - 2, "NATAL")

    for h in range(1, 13):
        c_val = cuspides_abs.get(h, 0.0)
        ang_c = math.radians((180.0 - (c_val - asc_abs)) % 360)
        x_in = cx + r_hub * math.cos(ang_c)
        y_in = cy + r_hub * math.sin(ang_c)
        x_out = cx + r_zodiaco_in * math.cos(ang_c)
        y_out = cy + r_zodiaco_in * math.sin(ang_c)

        if h in [1, 4, 7, 10]:
            c.setStrokeColor(HexColor('#7df9ff'))
            c.setLineWidth(1.2)
        else:
            c.setStrokeColor(HexColor('#2e3850'))
            c.setLineWidth(0.5)
        c.line(x_in, y_in, x_out, y_out)

        prox_h = 1 if h == 12 else h + 1
        c_prox = cuspides_abs.get(prox_h, 0.0)
        meio_c = ((c_val + ((c_prox - c_val) % 360) / 2.0)) % 360
        ang_n = math.radians((180.0 - (meio_c - asc_abs)) % 360)
        xn = cx + (r_hub + 10) * math.cos(ang_n)
        yn = cy + (r_hub + 10) * math.sin(ang_n) - 2.5
        c.setFillColor(HexColor('#a4b3d6'))
        c.setFont(FONTE_UNICODE_NOME, 5)
        c.drawCentredString(xn, yn, str(h))

    for p_nome, p_abs, p_sigla in planetas_plot:
        ang_p = math.radians((180.0 - (p_abs - asc_abs)) % 360)
        xp = cx + 46 * math.cos(ang_p)
        yp = cy + 46 * math.sin(ang_p)
        c.setFillColor(HexColor('#7df9ff'))
        c.circle(xp, yp, 2, stroke=0, fill=1)
        lx = cx + 57 * math.cos(ang_p)
        ly = cy + 57 * math.sin(ang_p) - 2.5
        c.setFillColor(HexColor('#ffffff'))
        c.setFont(FONTE_UNICODE_NOME, 5)
        c.drawCentredString(lx, ly, seguro_texto(p_sigla))

def fabricar_pdf_estilizado(nome_c, cid_c, dt_ref, triade_info, pot_texto, swot_data, tab_pont_raw, tab_proj_raw, asc_abs, cuspides_abs, planetas_plot):
    if not REPORTLAB_DISPONIVEL: return None
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w_page, h_page = A4

    cor_topo = HexColor('#102a43')
    cor_azul_escuro = HexColor('#0d47a1')
    cor_verde = HexColor('#1b5e20')
    cor_alerta = HexColor('#b71c1c')
    cor_fundo_card = HexColor('#f7f9fc')
    cor_borda = HexColor('#c5d0e6')

    # ========================== PÁGINA 1 ==========================
    c.setFillColor(cor_topo)
    c.rect(0, h_page - 80, w_page, 80, fill=1, stroke=0)
    c.setFillColor(cor_azul_escuro)
    c.rect(0, h_page - 83, w_page, 3, fill=1, stroke=0)

    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_UNICODE_NOME, 15)
    c.drawString(40, h_page - 36, seguro_texto("ASTROLOGIA CONSCIENTE"))
    c.setFont(FONTE_UNICODE_NOME, 9.5)
    c.drawString(40, h_page - 52, seguro_texto("Relatório Executivo: Matriz Natal, Mandala & A Dança dos Ponteiros"))
    c.setFont(FONTE_UNICODE_NOME, 8)
    c.drawString(40, h_page - 66, seguro_texto("Pesquisa e Metodologia: Douglas Rosa (@astrolodoug)"))

    # Card Consulente
    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, h_page - 135, w_page - 80, 45, 5, fill=1, stroke=1)
    c.setFillColor(cor_topo)
    c.setFont(FONTE_UNICODE_NOME, 9.5)
    c.drawString(50, h_page - 105, seguro_texto(f"Consulente: {nome_c} | Local: {cid_c}"))
    c.setFont(FONTE_UNICODE_NOME, 8.5)
    c.drawString(50, h_page - 120, seguro_texto(f"Data Base da Análise: {dt_ref} | Método: APRS e Trânsitos Ativos"))

    # Seção 1
    c.setFont(FONTE_UNICODE_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 152, seguro_texto("1. Síntese da Personalidade & Mandala Astrológica"))
    c.setStrokeColor(cor_azul_escuro)
    c.setLineWidth(1)
    c.line(40, h_page - 156, w_page - 40, h_page - 156)

    # Box Esquerda
    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, h_page - 370, 275, 205, 5, fill=1, stroke=1)
    c.setFillColor(cor_azul_escuro)
    c.setFont(FONTE_UNICODE_NOME, 9)
    c.drawString(50, h_page - 175, seguro_texto("Eixo de Identidade & Temperamento:"))

    itens_triade = [
        f"Sol Natal: {triade_info['sol']}",
        f"Lua Natal: {triade_info['lua']}",
        f"Ascendente: {triade_info['asc']}",
        f"Elemento Predominante: {swot_data['elemento_dominante']}"
    ]
    y_tr = h_page - 195
    for it in itens_triade:
        desenhar_marcador(c, 52, y_tr + 3, cor_azul_escuro)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(60, y_tr, seguro_texto(it))
        y_tr -= 16

    c.setFillColor(cor_azul_escuro)
    c.setFont(FONTE_UNICODE_NOME, 8.5)
    c.drawString(50, h_page - 275, seguro_texto("Área de Maior Vocação & Potencial:"))
    c.setFont(FONTE_UNICODE_NOME, 8)
    c.setFillColor(HexColor('#2b263b'))
    c.drawString(50, h_page - 290, seguro_texto(f"Setor Focal: {pot_texto['titulo']}"))
    linhas_pot = textwrap.wrap(pot_texto['descricao'], width=48)
    y_pt = h_page - 304
    for lp in linhas_pot[:2]:
        c.drawString(50, y_pt, seguro_texto(lp))
        y_pt -= 12

    # Box Direita com Mandala Vetorial
    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(330, h_page - 370, 225, 205, 5, fill=1, stroke=1)
    desenhar_mandala_astrologica_vetorial(
        c, cx=442.5, cy=h_page - 267.5, raio=82,
        asc_abs=asc_abs, cuspides_abs=cuspides_abs, planetas_plot=planetas_plot
    )
    c.setFillColor(HexColor('#666666'))
    c.setFont(FONTE_UNICODE_NOME, 6.5)
    c.drawCentredString(442.5, h_page - 364, seguro_texto("Mandala Oficial Vetorial Sincronizada"))

    # Seção 2: SWOT Natal
    c.setFont(FONTE_UNICODE_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 390, seguro_texto("2. Análise Comportamental: Forças e Fraquezas Natais"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 394, w_page - 40, h_page - 394)

    w_box = (w_page - 90) / 2
    c.setFillColor(HexColor('#f1f8e9'))
    c.setStrokeColor(cor_verde)
    c.roundRect(40, h_page - 520, w_box, 118, 5, fill=1, stroke=1)
    c.setFillColor(cor_verde)
    c.setFont(FONTE_UNICODE_NOME, 9)
    c.drawString(50, h_page - 410, seguro_texto("FORÇAS (Potenciais Inatos):"))
    y_f = h_page - 430
    for item in swot_data['forcas']:
        desenhar_marcador(c, 52, y_f + 3, cor_verde)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        linhas_f = textwrap.wrap(item, width=42)
        c.drawString(60, y_f, seguro_texto(linhas_f[0]))
        if len(linhas_f) > 1:
            y_f -= 10
            c.drawString(60, y_f, seguro_texto(linhas_f[1]))
        y_f -= 14

    c.setFillColor(HexColor('#ffebee'))
    c.setStrokeColor(cor_alerta)
    c.roundRect(45 + w_box, h_page - 520, w_box, 118, 5, fill=1, stroke=1)
    c.setFillColor(cor_alerta)
    c.setFont(FONTE_UNICODE_NOME, 9)
    c.drawString(55 + w_box, h_page - 410, seguro_texto("FRAQUEZAS (Zonas de Atenção):"))
    y_fr = h_page - 430
    for item in swot_data['fraquezas']:
        desenhar_marcador(c, 57 + w_box, y_fr + 3, cor_alerta)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        linhas_fr = textwrap.wrap(item, width=42)
        c.drawString(65 + w_box, y_fr, seguro_texto(linhas_fr[0]))
        if len(linhas_fr) > 1:
            y_fr -= 10
            c.drawString(65 + w_box, y_fr, seguro_texto(linhas_fr[1]))
        y_fr -= 14

    # Seção 3: Ponteiros
    c.setFont(FONTE_UNICODE_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 542, seguro_texto("3. Posicionamento Atual dos 9 Ponteiros"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 546, w_page - 40, h_page - 546)

    y_p = h_page - 564
    for it in tab_pont_raw[:9]:
        desenhar_marcador(c, 47, y_p + 3, cor_azul_escuro)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(55, y_p, seguro_texto(f"{it['Ponteiro']}: {it['Pos']}  |  {it['Reg']}"))
        y_p -= 15

    c.setStrokeColor(cor_borda)
    c.line(40, 40, w_page - 40, 40)
    c.setFont(FONTE_UNICODE_NOME, 7.5)
    c.setFillColor(HexColor('#555555'))
    c.drawString(40, 28, seguro_texto("Astrologia Consciente | Douglas Rosa (@astrolodoug) - WhatsApp: (11) 97711-7024"))
    c.drawRightString(w_page - 40, 28, seguro_texto("Página 1 de 2"))

    c.showPage()

    # ========================== PÁGINA 2 ==========================
    c.setFillColor(cor_topo)
    c.rect(0, h_page - 50, w_page, 50, fill=1, stroke=0)
    c.setFillColor(cor_azul_escuro)
    c.rect(0, h_page - 53, w_page, 3, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_UNICODE_NOME, 10.5)
    c.drawString(40, h_page - 32, seguro_texto("CRONOGRAMA PREDITIVO: OPORTUNIDADES, AMEAÇAS E DIRECIONAMENTO"))

    # Seção 4: SWOT Preditivo
    c.setFont(FONTE_UNICODE_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 75, seguro_texto("4. Matriz Preditiva: Oportunidades & Ameaças dos Próximos 12 Meses"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 79, w_page - 40, h_page - 79)

    c.setFillColor(HexColor('#f1f8e9'))
    c.setStrokeColor(cor_verde)
    c.roundRect(40, h_page - 215, w_box, 125, 5, fill=1, stroke=1)
    c.setFillColor(cor_verde)
    c.setFont(FONTE_UNICODE_NOME, 9)
    c.drawString(50, h_page - 98, seguro_texto("OPORTUNIDADES (Janelas de Expansão):"))
    y_op = h_page - 116
    for item in swot_data['oportunidades']:
        desenhar_marcador(c, 52, y_op + 3, cor_verde)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        linhas_op = textwrap.wrap(item, width=42)
        c.drawString(60, y_op, seguro_texto(linhas_op[0]))
        if len(linhas_op) > 1:
            y_op -= 10
            c.drawString(60, y_op, seguro_texto(linhas_op[1]))
        y_op -= 14

    c.setFillColor(HexColor('#fff8e1'))
    c.setStrokeColor(HexColor('#f57c00'))
    c.roundRect(45 + w_box, h_page - 215, w_box, 125, 5, fill=1, stroke=1)
    c.setFillColor(HexColor('#e65100'))
    c.setFont(FONTE_UNICODE_NOME, 9)
    c.drawString(55 + w_box, h_page - 98, seguro_texto("AMEAÇAS (Gatilhos de Rigor & Atenção):"))
    y_am = h_page - 116
    for item in swot_data['ameacas']:
        desenhar_marcador(c, 57 + w_box, y_am + 3, HexColor('#e65100'))
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        linhas_am = textwrap.wrap(item, width=42)
        c.drawString(65 + w_box, y_am, seguro_texto(linhas_am[0]))
        if len(linhas_am) > 1:
            y_am -= 10
            c.drawString(65 + w_box, y_am, seguro_texto(linhas_am[1]))
        y_am -= 14

    # Seção 5: Cronograma
    c.setFont(FONTE_UNICODE_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 238, seguro_texto("5. Cronograma dos 9 Ponteiros & Gatilhos no Tempo (12 Meses)"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 242, w_page - 40, h_page - 242)

    y_pr = h_page - 260
    for p in tab_proj_raw[:7]:
        desenhar_marcador(c, 47, y_pr + 3, cor_azul_escuro)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(55, y_pr, seguro_texto(f"{p['Data']}: {p['Ponteiro']} em {p['Aspecto']} ({p['Regência']})"))
        y_pr -= 15

    # Seção 6: Dedicatória
    c.setFont(FONTE_UNICODE_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_pr - 10, seguro_texto("6. Guia Didático & Dedicatória Oficial"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_pr - 14, w_page - 40, y_pr - 14)

    y_card = y_pr - 150
    c.setFillColor(cor_topo)
    c.roundRect(40, y_card, w_page - 80, 125, 6, fill=1, stroke=0)

    c.setFillColor(HexColor('#64b5f6'))
    c.setFont(FONTE_UNICODE_NOME, 9.5)
    c.drawString(55, y_card + 102, seguro_texto("Uma mensagem de Douglas Rosa (@astrolodoug) para você:"))
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_UNICODE_NOME, 8)
    c.drawString(55, y_card + 85, seguro_texto('"O mapa astral não é uma sentença estática: é uma partitura rítmica viva.'))
    c.drawString(55, y_card + 72, seguro_texto('A Dança dos Ponteiros (APRS) revela o momento exato em que cada tema'))
    c.drawString(55, y_card + 59, seguro_texto('é convocado a amadurecer ou expandir. Use essas datas como coordenadas de ação."'))

    c.setFillColor(HexColor('#64b5f6'))
    c.setFont(FONTE_UNICODE_NOME, 8.5)
    c.drawString(55, y_card + 35, seguro_texto("Atendimentos, Formações e Estudos:"))
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_UNICODE_NOME, 8)
    c.drawString(55, y_card + 20, seguro_texto("Instagram: @astrolodoug  |  WhatsApp: +55 (11) 97711-7024  |  YouTube: @astrolodoug"))

    c.setStrokeColor(cor_borda)
    c.line(40, 40, w_page - 40, 40)
    c.setFont(FONTE_UNICODE_NOME, 7.5)
    c.setFillColor(HexColor('#555555'))
    c.drawString(40, 28, seguro_texto("Astrologia Consciente | Todos os direitos reservados - @astrolodoug"))
    c.drawRightString(w_page - 40, 28, seguro_texto("Página 2 de 2"))

    c.save()
    buf.seek(0)
    return buf.getvalue()

st.title("✨ Astrologia Consciente")
st.markdown("### A Dança dos Ponteiros: Relatório Preditivo e Mandala")

st.sidebar.header("Dados do Consulente")
nome = st.sidebar.text_input("Nome Completo", "Douglas Rosa")

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Local de Nascimento")
origem_tipo = st.sidebar.radio("País de Origem:", ["Brasil (Municípios)", "Outro País (Digitar Livre)"], index=0)

if origem_tipo == "Brasil (Municípios)":
    uf_escolhida = st.sidebar.selectbox("1. Escolha o Estado (UF):", ESTADOS_BR, index=0)
    sigla_uf = uf_escolhida.split(" - ")[0]
    lista_cidades_uf = carregar_municipios(sigla_uf)
    total_cid = len(lista_cidades_uf)

    idx_padrao = 0
    capitais = {"SP": "São Paulo", "RJ": "Rio de Janeiro", "MG": "Belo Horizonte", "BA": "Salvador", "PR": "Curitiba", "RS": "Porto Alegre", "PE": "Recife", "CE": "Fortaleza", "PA": "Belém", "AC": "Rio Branco", "AP": "Macapá", "RR": "Boa Vista"}
    if sigla_uf in capitais and capitais[sigla_uf] in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index(capitais[sigla_uf])

    mun_escolhido = st.sidebar.selectbox(f"2. Município de {sigla_uf} ({total_cid} cidades):", options=lista_cidades_uf, index=idx_padrao, key=f"mun_{sigla_uf}")
    cidade = f"{mun_escolhido}, {sigla_uf}, Brasil"
else:
    cidade = st.sidebar.text_input("Digite Cidade e País:", value="Lisboa, Portugal")

st.sidebar.markdown("---")
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

if st.sidebar.button("🔮 Gerar Mapa, Mandala e Relatório"):
    st.session_state.mapa_gerado = True

st.sidebar.markdown("---")
st.sidebar.markdown("### 📲 Conecte-se com Douglas Rosa")
st.sidebar.link_button("💬 Conversar no WhatsApp", "https://wa.me/5511977117024", use_container_width=True)
st.sidebar.link_button("📸 Seguir no Instagram", "https://instagram.com/astrolodoug?dlrf=MWMyd2ZsendvemtnMQ%3D%3D", use_container_width=True)
st.sidebar.link_button("▶️ Acessar Canal no YouTube", "https://youtube.com/@astrolodoug?si=YimzRQs7yL1jJMSO", use_container_width=True)

if st.session_state.mapa_gerado:
    with st.spinner("A processar cálculos astrológicos..."):
        try:
            geo = Nominatim(user_agent="astrolodoug_app")
            loc = geo.geocode(cidade)
            if not loc:
                st.error(f"Localidade '{cidade}' não localizada. Tente outro município ou digitação livre.")
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

                planetas_dados = [("Sol", sujeito.sun, "☉"), ("Lua", sujeito.moon, "☽"), ("Mercúrio", sujeito.mercury, "☿"), ("Vênus", sujeito.venus, "♀"), ("Marte", sujeito.mars, "♂"), ("Júpiter", sujeito.jupiter, "♃"), ("Saturno", sujeito.saturn, "♄"), ("Urano", sujeito.uranus, "♅"), ("Netuno", sujeito.neptune, "♆"), ("Plutão", sujeito.pluto, "♇")]
                
                tab_pl = []
                mapa_casas_planetas = {}
                planetas_plot = []
                contagem_elem = {"Fogo": 0, "Terra": 0, "Ar": 0, "Água": 0}
                mapa_signo_elem = {"Áries":"Fogo","Leão":"Fogo","Sagitário":"Fogo","Touro":"Terra","Virgem":"Terra","Capricórnio":"Terra","Gêmeos":"Ar","Libra":"Ar","Aquário":"Ar","Câncer":"Água","Escorpião":"Água","Peixes":"Água"}

                for pn, po, sigla_curta in planetas_dados:
                    p_abs = float(obter_dado(po, 'abs_pos', 0.0))
                    num_casa, por_orbe, orbe_val = calc_casa_orbe(p_abs, cuspides_abs)
                    mapa_casas_planetas[pn] = num_casa
                    s_nome = nome_sig(obter_dado(po, 'sign', ''))
                    contagem_elem[mapa_signo_elem.get(s_nome, "Ar")] += 1

                    planetas_plot.append((pn, p_abs, f"{sigla_curta}{int(obter_dado(po, 'position', 0))}°"))
                    rotulo_casa = f"{num_casa}ª Casa (orbe de {int(orbe_val)}°)" if por_orbe else f"{num_casa}ª Casa"
                    pos_p = float(obter_dado(po, 'position', 0.0))
                    tab_pl.append({
                        "Planeta": pn,
                        "Posição": f"{pos_p:.2f}° {fmt_sig(obter_dado(po, 'sign', ''))}",
                        "Casa Natal (com Orbe)": rotulo_casa,
                        "Regente": REG_TXT.get(s_nome, "Desconhecido")
                    })

                st.markdown("---")
                st.markdown("### 🪐 Posicionamentos Natais nas Casas (com Orbes de Cúspides)")
                st.caption("ℹ️ Orbes aplicadas: 10° antes das Casas Angulares (1, 4, 7, 10) | 5° antes das Sucedentes (2, 5, 8, 11) | 3° antes das Cadentes (3, 6, 9, 12).")
                st.table(tab_pl)

                casa_destaque = mapa_casas_planetas.get("Sol", 10)
                potencial_info = {
                    "titulo": f"{casa_destaque}ª Casa Zodiacal",
                    "descricao": POTENCIAL_CASAS.get(casa_destaque, "Foco na consolidação de projetos e autoridade pessoal.")
                }

                elem_dominante = max(contagem_elem, key=contagem_elem.get)
                swot_data = {
                    "elemento_dominante": f"{elem_dominante} ({contagem_elem[elem_dominante]} planetas)",
                    "forcas": [
                        "Capacidade de liderança e centralidade pelo Sol",
                        "Intuição estratégica e percepção refinada",
                        "Resiliência diante de exigências estruturais",
                        "Compromisso prático com realizações de longo prazo"
                    ],
                    "fraquezas": [
                        "Cobrança interna excessiva e autocrítica severa",
                        "Dificuldade em delegar processos críticos",
                        "Sobrecarga mental ao absorver múltiplas frentes",
                        "Hesitação em abrir mão de rotinas já consolidadas"
                    ],
                    "oportunidades": [
                        "Ativação de prestígio e expansão profissional",
                        "Ponteiros rápidos abrindo visibilidade e conexões",
                        "Fase produtiva para lançamento de cursos e mentorias",
                        "Crescimento ordenado através da aplicação técnica"
                    ],
                    "ameacas": [
                        "Trânsitos de planetas lentos exigindo realismo estrito",
                        "Atenção redobrada a minúcias contratuais e prazos",
                        "Risco de cansaço se houver dispersão de foco",
                        "Exigência de limites claros em parcerias e acordos"
                    ]
                }

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

                st.markdown("---")
                st.markdown("## 🔒 Desbloqueie a Projeção de 12 Meses & Receba o seu Resumo")
                st.info("Insira o seu WhatsApp ou E-mail e clique em **'Confirmar e Liberar'** para baixar o relatório estilizado em PDF ou recebê-lo via mensagem:")

                c_lead1, c_lead2 = st.columns([3, 1])
                contato_in = c_lead1.text_input("WhatsApp (com DDD) ou E-mail:", value=st.session_state.contato_salvo, placeholder="ex: 11999998888 ou seu@email.com")
                btn_confirmar_contato = c_lead2.button("🔓 Confirmar e Liberar", use_container_width=True)

                if (btn_confirmar_contato or contato_in) and contato_in.strip():
                    st.session_state.contato_salvo = contato_in.strip()

                if st.session_state.contato_salvo:
                    try:
                        with open("leads.csv", "a", encoding="utf-8") as f:
                            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')};{nome};{cidade};{st.session_state.contato_salvo}\n")
                    except Exception:
                        pass

                    tab_pont_pdf = [{"Ponteiro": it["Ponteiro"], "Pos": it["Posição Atual"], "Reg": it["Regência Ativada"]} for it in tab_pont]
                    
                    sol_sn = nome_sig(sujeito.sun['sign'])
                    lua_sn = nome_sig(sujeito.moon['sign'])
                    asc_sn = nome_sig(sujeito.first_house['sign'])

                    triade_resumo = {
                        "sol": f"{sujeito.sun['position']:.2f}° {GLIFOS.get(sol_sn, '')} {sol_sn} (Casa {mapa_casas_planetas.get('Sol',1)})",
                        "lua": f"{sujeito.moon['position']:.2f}° {GLIFOS.get(lua_sn, '')} {lua_sn} (Casa {mapa_casas_planetas.get('Lua',1)})",
                        "asc": f"{sujeito.first_house['position']:.2f}° {GLIFOS.get(asc_sn, '')} {asc_sn} (1ª Casa)"
                    }

                    pdf_bytes = fabricar_pdf_estilizado(
                        nome_c=nome, cid_c=cidade, dt_ref=DATA_ANALISE.strftime('%d/%m/%Y'),
                        triade_info=triade_resumo, pot_texto=potencial_info, swot_data=swot_data,
                        tab_pont_raw=tab_pont_pdf, tab_proj_raw=tab_fp,
                        asc_abs=asc_b, cuspides_abs=cuspides_abs, planetas_plot=planetas_plot
                    )

                    st.success(f"✅ Contacto registrado: **{st.session_state.contato_salvo}**! O seu relatório executivo completo foi gerado:")

                    msg_txt = f"Olá Douglas Rosa (@astrolodoug)!\n\n"
                    msg_txt += f"Gerei meu mapa na Astrologia Consciente:\n"
                    msg_txt += f"👤 *Consulente:* {nome} ({cidade})\n"
                    msg_txt += f"📱 *Meu Contato:* {st.session_state.contato_salvo}\n"
                    msg_txt += f"📅 *Data Base:* {DATA_ANALISE.strftime('%d/%m/%Y')}\n\n"
                    msg_txt += f"🌟 *Área de Maior Potencial:* {potencial_info['titulo']}\n\n"
                    msg_txt += "🔭 *Ponteiros Ativos em Destaque:*\n"
                    for p_it in tab_pont[:4]:
                        msg_txt += f"• {p_it['Ponteiro']}: {p_it['Posição Atual']}\n"
                    msg_txt += "\n📅 *Próximas Ativações (12 Meses):*\n"
                    for pr_it in tab_fp[:3]:
                        msg_txt += f"• {pr_it['Data']}: {pr_it['Ponteiro']} em {pr_it['Aspecto']}\n"
                    msg_txt += "\nGostaria de entender melhor essas ativações e agendar uma análise aprofundada!"

                    txt_encoded = urllib.parse.quote(msg_txt)
                    link_whats_doug = f"https://api.whatsapp.com/send?phone=5511977117024&text={txt_encoded}"
                    link_mail_doug = f"mailto:doug.douglas.santos@gmail.com?subject={urllib.parse.quote(f'Resumo Astrológico | {nome} ({cidade})')}&body={txt_encoded}"

                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if pdf_bytes:
                            st.download_button(
                                label="📥 Baixar PDF Executivo Completo",
                                data=pdf_bytes,
                                file_name=f"Relatorio_Astrologia_Consciente_{nome.replace(' ','_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                    with col_btn2:
                        st.link_button("📲 Enviar para o WhatsApp de Douglas", link_whats_doug, use_container_width=True)
                    with col_btn3:
                        st.link_button("✉️ Enviar para o E-mail de Douglas", link_mail_doug, use_container_width=True)

                    st.markdown("---")
                    st.markdown(f"### 📅 Projeção dos 9 Ponteiros (12 Meses a partir de {DATA_ANALISE.strftime('%d/%m/%Y')})")
                    st.table(tab_fp)

                    proj_len = [(30,"Saturno em Trânsito","Sextil","Sol Natal","Sol"),(90,"Urano em Trânsito","Trígono","Lua Natal","Lua"),(160,"Júpiter em Trânsito","Conjunção","Ascendente","Marte"),(220,"Netuno em Trânsito","Oposição","Mercúrio Natal","Mercúrio"),(300,"Plutão em Trânsito","Sextil","Meio do Céu","Sol"),(355,"Saturno em Trânsito","Trígono","Vênus Natal","Vênus")]
                    tab_fl = [{"Data": (DATA_ANALISE + timedelta(days=d)).strftime('%d/%m/%Y'), "Planeta Lento": t, "Aspecto": f"{asp} com {alvo}", "Regência": reg_de(p)} for d, t, asp, alvo, p in proj_len]
                    st.markdown("---")
                    st.markdown(f"### 📅 Projeção de Trânsitos Lentos (12 Meses a partir de {DATA_ANALISE.strftime('%d/%m/%Y')})")
                    st.table(tab_fl)

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
                    st.warning("👆 Digite o seu WhatsApp ou E-mail e toque no botão **'🔓 Confirmar e Liberar'** para gerar os botões de envio e o PDF.")

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
