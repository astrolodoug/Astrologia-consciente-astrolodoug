import os, json, ssl, math, textwrap, urllib.request, urllib.parse
from io import BytesIO
from datetime import datetime, timedelta
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
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
header[data-testid="stHeader"] {
    background-color: #1f1b29 !important;
    border-bottom: 1px solid rgba(125, 249, 255, 0.2) !important;
}
[data-testid="stSidebarCollapsedControl"] {
    background-color: #1f1b29 !important;
    border: 1.5px solid #7df9ff !important;
    border-radius: 8px !important;
    padding: 3px 8px !important;
    box-shadow: 0 0 12px rgba(125, 249, 255, 0.35) !important;
}
[data-testid="stSidebarCollapsedControl"]:hover { background-color: #2b263b !important; }
[data-testid="stSidebarCollapsedControl"] svg { fill: #7df9ff !important; stroke: #7df9ff !important; }
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

# ==================== BANCO ARQUETÍPICO PARA ANÁLISE DINÂMICA ====================
FORCAS_SIGNOS = {
    "Áries": "Pioneirismo, assertividade nas decisões e coragem para abrir novos caminhos.",
    "Touro": "Capacidade de sustentação material, persistência e fidelidade a valores práticos.",
    "Gêmeos": "Versatilidade mental, rapidez de articulação lógica e talento para conectar saberes.",
    "Câncer": "Faro intuitivo aguçado, empatia protetora e poder de mobilização emocional genuína.",
    "Leão": "Magnetismo pessoal radiante, generosidade autoral e autoridade natural na liderança.",
    "Virgem": "Discernimento analítico cirúrgico, domínio técnico impecável e constante busca por excelência.",
    "Libra": "Senso estético refinado, habilidade diplomática nata e visão equilibrada em negociações.",
    "Escorpião": "Percepção psicológica profunda, poder regenerativo perante crises e foco inabalável.",
    "Sagitário": "Visão ampla de longo prazo, entusiasmo expansivo e habilidade natural para ensinar e inspirar.",
    "Capricórnio": "Maturidade exemplar, visão de legado profissional e disciplina na gestão do tempo.",
    "Aquário": "Inovação visionária, independência intelectual e facilidade em articular projetos coletivos.",
    "Peixes": "Sensibilidade psíquica refinada, capacidade de síntese simbólica e empatia desinteressada."
}

FRAQUEZAS_SIGNOS = {
    "Áries": "Impaciência com processos lentos, tendência a ações impulsivas e reatividade imediata.",
    "Touro": "Resistência teimosa a mudanças de cenário e apego excessivo a rotinas consolidadas.",
    "Gêmeos": "Dispersão do foco por excesso de estímulos simultâneos e dificuldade em aprofundar um único tema.",
    "Câncer": "Hipersensibilidade a oscilações alheias e tendência a se fechar em defesas emocionais.",
    "Leão": "Vulnerabilidade ao orgulho pessoal, necessidade de validação e relutância em atuar nos bastidores.",
    "Virgem": "Autocobrança implacável, tendência ao perfeccionismo paralisante e apego crítico a minúcias.",
    "Libra": "Hesitação no momento de confrontos necessários e adiamento de decisões para agradar a terceiros.",
    "Escorpião": "Desconfiança instintiva prévia, dificuldade em delegar e propensão a guardar tensões não ditas.",
    "Sagitário": "Otimismo desmedido com prazos operacionais, impaciência com detalhes e dispersão teórica.",
    "Capricórnio": "Rigor excessivo consigo e com outros, pessimismo cautelar e dificuldade em desfrutar o presente.",
    "Aquário": "Distanciamento afetivo sob pressão, rebeldia contra métodos tradicionais e excesso de teoria.",
    "Peixes": "Dificuldade em delimitar fronteiras claras, tendência à sobrecarga psíquica e fuga da rotina prática."
}

FORCAS_CASAS = {
    1: "Iniciativa individual soberana e forte presença pessoal.",
    2: "Talento pragmático para construir lastro e monetizar habilidades.",
    3: "Excelente didática comunicativa e agilidade no trânsito de informações.",
    4: "Construção de alicerces sólidos e resguardo consciente da intimidade.",
    5: "Autenticidade criativa, liderança autoral e poder de expressão contagiante.",
    6: "Aperfeiçoamento diário do método, eficiência prática e gestão apurada da rotina.",
    7: "Habilidade de aliança com parceiros de alto nível e pactuação estratégica.",
    8: "Capacidade de gerir recursos partilhados e transformar adversidades em poder.",
    9: "Facilidade de expansão acadêmica, internacionalização e visão filosófica.",
    10: "Construção sólida de reputação, autoridade pública e ascensão consistente.",
    11: "Articulação de grupos estratégicos e rede de apoio qualificada.",
    12: "Sabedoria de bastidores, leitura das entrelinhas e proteção intuitiva."
}

FRAQUEZAS_CASAS = {
    1: "Sobrecarga física por assumir todas as frentes sem pedir auxílio.",
    2: "Ansiedade quanto à estabilidade material gerando cautela desmedida nos passos.",
    3: "Sobrecarga de estímulos e comunicações fragmentadas que consomem o foco principal.",
    4: "Apego a padrões do passado e hesitação em desbravar novos territórios profissionais.",
    5: "Risco de frustração caso as criações autorais não recebam reconhecimento imediato.",
    6: "Esgotamento por excesso de demandas diárias e dificuldade de relaxar o controle.",
    7: "Dependência excessiva da anuência ou concordância de parceiros para agir.",
    8: "Tensão silenciosa com partilhas, investimentos de risco e desgaste de controle.",
    9: "Inquietação constante que dificulta a ancoragem no trabalho prático do momento.",
    10: "Cobrança extrema por status e medo de errar perante o público ou superiores.",
    11: "Desgaste de energia em causas ou projetos coletivos sem contrapartida justa.",
    12: "Tendência a isolamento autoprotetor quando surgem pressões externas mais duras."
}

ESTADOS_BR = [
    "SP - São Paulo", "RJ - Rio de Janeiro", "MG - Minas Gerais", "BA - Bahia",
    "PR - Paraná", "RS - Rio Grande do Sul", "PE - Pernambuco", "CE - Ceará", "PA - Pará",
    "AC - Acre", "AP - Amapá", "RR - Roraima", "SC - Santa Catarina", "GO - Goiás",
    "MA - Maranhão", "AM - Amazonas", "ES - Espírito Santo", "PB - Paraíba",
    "RN - Rio Grande do Norte", "MT - Mato Grosso", "AL - Alagoas", "PI - Piauí",
    "DF - Distrito Federal", "MS - Mato Grosso do Sul", "SE - Sergipe", "RO - Rondônia", "TO - Tocantins"
]

COODS_CAPITAIS = {
    "SP": (-23.5505, -46.6333, "America/Sao_Paulo"),
    "RJ": (-22.9068, -43.1729, "America/Sao_Paulo"),
    "MG": (-19.9167, -43.9345, "America/Sao_Paulo"),
    "BA": (-12.9777, -38.5016, "America/Bahia"),
    "PR": (-25.4284, -49.2733, "America/Sao_Paulo"),
    "RS": (-30.0346, -51.2177, "America/Sao_Paulo"),
    "PE": (-8.0476, -34.8770, "America/Recife"),
    "CE": (-3.7172, -38.5433, "America/Fortaleza"),
    "PA": (-1.4558, -48.4902, "America/Belem"),
    "AC": (-9.9753, -67.8249, "America/Rio_Branco"),
    "AP": (0.0355, -51.0705, "America/Belem"),
    "RR": (2.8235, -60.6758, "America/Boa_Vista"),
    "SC": (-27.5954, -48.5480, "America/Sao_Paulo"),
    "GO": (-16.6869, -49.2648, "America/Sao_Paulo"),
    "MA": (-2.5307, -44.3068, "America/Fortaleza"),
    "AM": (-3.1190, -60.0217, "America/Manaus"),
    "ES": (-20.3155, -40.3128, "America/Sao_Paulo"),
    "PB": (-7.1195, -34.8450, "America/Fortaleza"),
    "RN": (-5.7945, -35.2110, "America/Fortaleza"),
    "MT": (-15.6014, -56.0979, "America/Cuiaba"),
    "AL": (-9.6658, -35.7351, "America/Maceio"),
    "PI": (-5.0920, -42.8038, "America/Fortaleza"),
    "DF": (-15.7975, -47.8919, "America/Sao_Paulo"),
    "MS": (-20.4697, -54.6201, "America/Campo_Grande"),
    "SE": (-10.9472, -37.0731, "America/Maceio"),
    "RO": (-8.7619, -63.9039, "America/Porto_Velho"),
    "TO": (-10.1844, -48.3336, "America/Araguaina")
}

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
    if sigla_uf in mapa_direto: return mapa_direto[sigla_uf]
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

@st.cache_data(ttl=86400, show_spinner=False)
def obter_geolocalizacao_segura(cidade_str, sigla_uf=""):
    nome_puro = cidade_str.split(",")[0].strip().lower()
    capitais_nomes = {
        "são paulo": "SP", "sao paulo": "SP", "rio de janeiro": "RJ", "belo horizonte": "MG",
        "salvador": "BA", "curitiba": "PR", "porto alegre": "RS", "recife": "PE",
        "fortaleza": "CE", "belém": "PA", "belem": "PA", "rio branco": "AC",
        "macapá": "AP", "macapa": "AP", "boa vista": "RR", "florianópolis": "SC",
        "goiânia": "GO", "são luís": "MA", "manaus": "AM", "vitória": "ES",
        "joão pessoa": "PB", "natal": "RN", "cuiabá": "MT", "maceió": "AL",
        "teresina": "PI", "brasília": "DF", "brasilia": "DF", "campo grande": "MS",
        "aracaju": "SE", "porto velho": "RO", "palmas": "TO"
    }
    if nome_puro in capitais_nomes:
        uf_ref = capitais_nomes[nome_puro]
        if uf_ref in COODS_CAPITAIS:
            lat, lng, tz = COODS_CAPITAIS[uf_ref]
            return float(lat), float(lng), tz

    try:
        geo = Nominatim(user_agent="astrologia_consciente_douglas_v3", timeout=12)
        loc = geo.geocode(cidade_str)
        if loc:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude) or "America/Sao_Paulo"
            return float(loc.latitude), float(loc.longitude), tz_str
    except Exception:
        pass

    if sigla_uf in COODS_CAPITAIS:
        lat, lng, tz = COODS_CAPITAIS[sigla_uf]
        return float(lat), float(lng), tz

    return -23.5505, -46.6333, "America/Sao_Paulo"

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

# ==================== CARREGAMENTO LOCAL DA FONTE DEJAVU ====================
FONTE_UNICODE_NOME = "Helvetica"
FONTE_BOLD_NOME = "Helvetica-Bold"
FONTE_OBLIQUE_NOME = "Helvetica-Oblique"
FONTE_REGULAR = "Helvetica"
FONTE_BOLD = "Helvetica-Bold"
FONTE_OBLIQUE = "Helvetica-Oblique"
UNICODE_ATIVA = False

def inicializar_fonte_dejavu():
    global FONTE_UNICODE_NOME, FONTE_BOLD_NOME, FONTE_OBLIQUE_NOME
    global FONTE_REGULAR, FONTE_BOLD, FONTE_OBLIQUE, UNICODE_ATIVA
    if not REPORTLAB_DISPONIVEL:
        return
    try:
        font_path = fm.findfont('DejaVu Sans')
        if font_path and os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("DejaVuLocal", font_path))
            FONTE_UNICODE_NOME = "DejaVuLocal"
            FONTE_REGULAR = "DejaVuLocal"
            UNICODE_ATIVA = True

        bold_path = fm.findfont('DejaVu Sans:weight=bold')
        if bold_path and os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("DejaVuLocal-Bold", bold_path))
            FONTE_BOLD_NOME = "DejaVuLocal-Bold"
            FONTE_BOLD = "DejaVuLocal-Bold"
        elif UNICODE_ATIVA:
            FONTE_BOLD_NOME = "DejaVuLocal"
            FONTE_BOLD = "DejaVuLocal"

        oblique_path = fm.findfont('DejaVu Sans:style=oblique')
        if oblique_path and os.path.exists(oblique_path):
            pdfmetrics.registerFont(TTFont("DejaVuLocal-Oblique", oblique_path))
            FONTE_OBLIQUE_NOME = "DejaVuLocal-Oblique"
            FONTE_OBLIQUE = "DejaVuLocal-Oblique"
        elif UNICODE_ATIVA:
            FONTE_OBLIQUE_NOME = "DejaVuLocal"
            FONTE_OBLIQUE = "DejaVuLocal"
    except Exception:
        pass

inicializar_fonte_dejavu()

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

# ==================== CÁLCULO PREDITIVO REAL (12 MESES) ====================
def calcular_projecoes_reais(dt_analise, dt_nasc, asc_b, planetas_natal, casas_p, FATORES):
    dias_base = (dt_analise - dt_nasc).days
    eventos_futuros = []
    angulos = [
        (0, "Conjunção", "neutra"),
        (60, "Sextil", "harmonica"),
        (90, "Quadratura", "tensao"),
        (120, "Trígono", "harmonica"),
        (180, "Oposição", "tensao")
    ]

    for p_nome, ft, pb in FATORES:
        vel = 4.0 / ft
        pos_atual = (asc_b + (dias_base * vel)) % 360

        for pn, gn, sn, cn in planetas_natal:
            for ang, asp_nome, tipo in angulos:
                alvos = [(gn + ang) % 360] if ang in [0, 180] else [(gn + ang) % 360, (gn - ang) % 360]
                for alvo in alvos:
                    dist = (alvo - pos_atual) % 360
                    dias_ate = dist / vel
                    if 1 <= dias_ate <= 365:
                        dt_evento = dt_analise + timedelta(days=round(dias_ate))
                        reg_lista = casas_p.get(pb, [])
                        reg_txt = f"Regente das {', '.join(reg_lista)}" if reg_lista else f"Ativação de {pb}"
                        eventos_futuros.append({
                            "dias": dias_ate,
                            "data_dt": dt_evento,
                            "data_str": dt_evento.strftime('%d/%m/%Y'),
                            "ponteiro": p_nome,
                            "planeta_base": pb,
                            "aspecto": f"{asp_nome} com {pn} Natal",
                            "alvo_nome": pn,
                            "alvo_casa": cn,
                            "tipo_asp": tipo,
                            "regencia": reg_txt
                        })

    eventos_futuros.sort(key=lambda x: x['dias'])
    return eventos_futuros

def selecionar_cronograma_equilibrado(eventos_futuros, total=8):
    if not eventos_futuros: return []
    if len(eventos_futuros) <= total: return eventos_futuros
    selecionados = []
    ultimo_dia = -30
    for ev in eventos_futuros:
        if ev['dias'] - ultimo_dia >= 25:
            selecionados.append(ev)
            ultimo_dia = ev['dias']
            if len(selecionados) == total: break
    if len(selecionados) < total:
        for ev in eventos_futuros:
            if ev not in selecionados:
                selecionados.append(ev)
                if len(selecionados) == total: break
    selecionados.sort(key=lambda x: x['dias'])
    return selecionados

# ==================== GERADOR DINÂMICO DE SWOT ====================
def gerar_swot_dinamico(sol_info, lua_info, asc_info, elem_dominante, contagem_elem, eventos_futuros):
    sol_signo = sol_info['signo']
    sol_casa = sol_info['casa']
    lua_signo = lua_info['signo']
    lua_casa = lua_info['casa']
    asc_signo = asc_info['signo']

    FORCAS_ELEM = {
        "Fogo": "Vitalidade contagiante, entusiasmo inesgotável e coragem pioneira para agir.",
        "Terra": "Lastro prático incomparável, capacidade de sustentação e disciplina na execução.",
        "Ar": "Agilidade lógica, facilidade em criar pontes e visão estratégica articulada.",
        "Água": "Profundidade intuitiva, leitura empática do ambiente e força de adaptação psíquica."
    }

    FRAQUEZAS_ELEM = {
        "Fogo": "Risco de estresse por excesso de velocidade e impaciência com a rotina comum.",
        "Terra": "Resistência excessiva a desapegar de rotinas conhecidas e lentidão na mudança.",
        "Ar": "Sobrecarga mental por excesso de ideias simultâneas e dispersão de foco prático.",
        "Água": "Hipersensibilidade psíquica às oscilações do ambiente e vulnerabilidade emocional."
    }

    forcas = [
        f"Identidade Solar ({sol_signo} na Casa {sol_casa}): {FORCAS_SIGNOS.get(sol_signo, '')} {FORCAS_CASAS.get(sol_casa, '')}",
        f"Inteligência Emocional ({lua_signo} na Casa {lua_casa}): {FORCAS_SIGNOS.get(lua_signo, '')} {FORCAS_CASAS.get(lua_casa, '')}",
        f"Presença e Expressão (Ascendente em {asc_signo}): {FORCAS_SIGNOS.get(asc_signo, '')}",
        f"Temperamento ({elem_dominante}): {FORCAS_ELEM.get(elem_dominante, '')}"
    ]

    fraquezas = [
        f"Ponto Cego de Liderança ({sol_signo}): {FRAQUEZAS_SIGNOS.get(sol_signo, '')}",
        f"Vulnerabilidade Emocional ({lua_signo} na Casa {lua_casa}): {FRAQUEZAS_SIGNOS.get(lua_signo, '')} {FRAQUEZAS_CASAS.get(lua_casa, '')}",
        f"Atrito de Expressão (Ascendente em {asc_signo}): {FRAQUEZAS_SIGNOS.get(asc_signo, '')}",
        f"Gestão de Energia ({elem_dominante}): {FRAQUEZAS_ELEM.get(elem_dominante, '')}"
    ]

    oportunidades = []
    for ev in eventos_futuros:
        if ev['tipo_asp'] in ['harmonica', 'neutra'] or any(p in ev['ponteiro'] for p in ['Júpiter', 'Vênus', 'Solar']):
            txt = f"{ev['data_str']} ({ev['ponteiro']} em {ev['aspecto']}): Janela propícia para avanço em assuntos da Casa {ev['alvo_casa']} ({ev['regencia']})."
            if txt not in oportunidades:
                oportunidades.append(txt)
        if len(oportunidades) >= 4: break

    while len(oportunidades) < 4:
        oportunidades.append("Ciclo favorável para expansão estratégica, difusão do trabalho e consolidação de novas alianças.")

    ameacas = []
    for ev in eventos_futuros:
        if ev['tipo_asp'] == 'tensao' or any(p in ev['ponteiro'] for p in ['Saturno', 'Plutão', 'Marte']):
            txt = f"{ev['data_str']} ({ev['ponteiro']} em {ev['aspecto']}): Exigência de disciplina e rigor; evite impulsividade e blinde acordos na Casa {ev['alvo_casa']}."
            if txt not in ameacas:
                ameacas.append(txt)
        if len(ameacas) >= 4: break

    while len(ameacas) < 4:
        ameacas.append("Atenção à sobrecarga de responsabilidades; mantenha critérios claros de foco e paciência.")

    return {
        "elemento_dominante": f"{elem_dominante} ({contagem_elem[elem_dominante]} planetas)",
        "forcas": forcas,
        "fraquezas": fraquezas,
        "oportunidades": oportunidades,
        "ameacas": ameacas
    }

# ==================== GERADOR DA DICA DO DIA ====================
def calcular_bussola_do_dia(dt_analise, aspetos_hoje, tab_pont):
    TEMAS_CASAS = {
        1: ("afirmação pessoal, vitalidade e pioneirismo", "Tome as rédeas de uma decisão pessoal sem delegar a sua autoridade."),
        2: ("gestão de recursos, valores e segurança material", "Organize prioridades financeiras e precifique o seu trabalho com clareza."),
        3: ("comunicação estratégica, negociações e intercâmbio", "Envie propostas, esclareça pendências e foque na clareza do discurso."),
        4: ("segurança emocional, intimidade e alicerces estruturais", "Proteja o seu espaço íntimo e fortaleça as bases de apoio pessoal."),
        5: ("expressão criativa, magnetismo autoral e projetos", "Coloque a sua assinatura criativa em tudo o que produzir hoje."),
        6: ("organização do método diário, eficiência prática e rotina", "Aperfeiçoe o seu método de rotina e elimine gargalos que consomem tempo."),
        7: ("parcerias estratégicas, contratos e diálogo a dois", "Alinhe expectativas em acordos e busque equilíbrio diplomático consciente."),
        8: ("transformações profundas, discernimento e gestão de crises", "Desapegue do que já não agrega valor e assuma o controle emocional sob pressão."),
        9: ("expansão de visão, novos estudos e horizontes a longo prazo", "Dedique tempo a leituras profundas e ao planeamento estratégico futuro."),
        10: ("reputação profissional, carreira e consolidação de legado", "Posicione-se com firmeza perante clientes ou líderes; a sua competência fala alto."),
        11: ("projetos coletivos, impacto comunitário e visão de futuro", "Articule conexões com pessoas que partilham dos seus valores e projetos."),
        12: ("recolhimento estratégico, intuição psíquica e bastidores", "Trabalhe nos bastidores, desacelere o ritmo e confie na sua intuição técnica.")
    }

    if aspetos_hoje:
        focal = aspetos_hoje[0]
        p_nome = focal['ponteiro']
        alvo = focal['alvo_nome']
        asp = focal['aspeto']
        casa = focal['casa_ponteiro']
        tipo = focal['tipo']
        tema_txt, dica_acao = TEMAS_CASAS.get(casa, ("direcionamento consciente", "Foque na prioridade prática do seu dia."))

        if tipo == "tensao":
            frase = f"O {p_nome} ativa hoje por {asp} o seu {alvo} Natal, incidindo sobre a sua {casa}ª Casa ({tema_txt}). Este compasso traz um filtro de maturidade: não reaja por impulso; conduza a pressão com estratégia e paciência."
            dica = f"{dica_acao} Evite confrontos desnecessários e estabeleça limites seguros no setor da Casa {casa}."
        else:
            frase = f"O {p_nome} conecta-se harmonicamente por {asp} ao seu {alvo} Natal na sua {casa}ª Casa ({tema_txt}). A matriz do dia abre fluidez e respaldo para estruturar passos sólidos e visibilidade."
            dica = f"{dica_acao} Aproveite a janela favorável para avançar em iniciativas estratégicas da Casa {casa}."
        return frase, dica
    else:
        p_focal = tab_pont[0] if tab_pont else {"nome": "Ponteiro Solar", "casa": 1}
        casa = p_focal.get('casa', 1)
        p_nome = p_focal.get('Ponteiro', 'Ponteiro Solar')
        tema_txt, dica_acao = TEMAS_CASAS.get(casa, ("consolidação de objetivos", "Dedique energia à sua meta principal."))
        frase = f"O {p_nome} transita hoje pela sua {casa}ª Casa ({tema_txt}). O tempo convida a direcionar a sua força consciente para estruturar este território de vida."
        dica = f"{dica_acao} Defina uma meta clara para a sua {casa}ª Casa e conclua-a com método."
        return frase, dica

# ==================== MANDALA ASTROLÓGICA OFICIAL DO SITE ====================
def gerar_mandala_astrologica_png(planetas_pos, cuspides_pos, asc_grau):
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    signos_dados = [
        ("Áries", "♈", "#e63946"), ("Touro", "♉", "#2a9d8f"), ("Gêmeos", "♊", "#e9c46a"),
        ("Câncer", "♋", "#457b9d"), ("Leão", "♌", "#e63946"), ("Virgem", "♍", "#2a9d8f"),
        ("Libra", "♎", "#e9c46a"), ("Escorpião", "♏", "#457b9d"), ("Sagitário", "♐", "#e63946"),
        ("Capricórnio", "♑", "#2a9d8f"), ("Aquário", "♒", "#e9c46a"), ("Peixes", "♓", "#457b9d")
    ]

    offset_rad = np.radians(180 - asc_grau)
    font_path = fm.findfont('DejaVu Sans')
    font_prop = fm.FontProperties(fname=font_path) if font_path else None

    for i, (nome, glifo, cor) in enumerate(signos_dados):
        mid_deg = i * 30 + 15
        mid_rad = np.radians(mid_deg) + offset_rad
        ax.bar(mid_rad, 0.28, width=np.radians(30), bottom=1.12, color=cor, alpha=0.45, edgecolor='#102a43', linewidth=1)
        ax.text(mid_rad, 1.25, glifo, ha='center', va='center', fontsize=14, color='#102a43', fontproperties=font_prop)

    for h in range(1, 13):
        c_deg = cuspides_pos.get(h, (h - 1) * 30)
        c_rad = np.radians(c_deg) + offset_rad
        is_angular = h in [1, 4, 7, 10]
        lw = 2.0 if is_angular else 0.8
        col = '#0d47a1' if is_angular else '#b0bec5'
        ax.plot([c_rad, c_rad], [0.45, 1.12], color=col, linewidth=lw, zorder=3)

        prox_h = 1 if h == 12 else h + 1
        c_prox = cuspides_pos.get(prox_h, h * 30)
        mid_h = (c_deg + ((c_prox - c_deg) % 360) / 2) % 360
        mid_h_rad = np.radians(mid_h) + offset_rad
        ax.text(mid_h_rad, 0.55, str(h), ha='center', va='center', fontsize=8, color='#0d47a1', fontweight='bold')

    theta_circ = np.linspace(0, 2 * np.pi, 200)
    ax.plot(theta_circ, [0.45] * 200, color='#0d47a1', linewidth=1.5)
    ax.plot(theta_circ, [1.12] * 200, color='#102a43', linewidth=1.5)
    ax.plot(theta_circ, [1.40] * 200, color='#102a43', linewidth=1.5)
    ax.text(0, 0, "MAPA\nNATAL", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#102a43')

    for i, (p1, g1, _) in enumerate(planetas_pos):
        for j, (p2, g2, _) in enumerate(planetas_pos):
            if i >= j: continue
            diff = abs(g1 - g2) % 360
            if diff > 180: diff = 360 - diff
            r1 = np.radians(g1) + offset_rad
            r2 = np.radians(g2) + offset_rad

            cor_asp, lw_asp = None, 0.8
            if abs(diff - 120) <= 6: cor_asp = '#2a9d8f'
            elif abs(diff - 60) <= 5: cor_asp = '#457b9d'
            elif abs(diff - 90) <= 6: cor_asp = '#e63946'
            elif abs(diff - 180) <= 7: cor_asp, lw_asp = '#d62828', 1.3

            if cor_asp:
                ax.plot([r1, r2], [0.44, 0.44], color=cor_asp, linewidth=lw_asp, alpha=0.7, zorder=2)

    for p_nome, p_grau, p_glifo in planetas_pos:
        p_rad = np.radians(p_grau) + offset_rad
        ax.plot(p_rad, 0.85, 'o', color='#0d47a1', markersize=5, zorder=4)
        deg_in_sign = p_grau % 30
        label = f"{p_glifo}\n{deg_in_sign:.0f}°"
        ax.text(p_rad, 0.98, label, ha='center', va='center', fontsize=8, color='#102a43', fontproperties=font_prop, zorder=5)

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)
    ax.spines['polar'].set_visible(False)

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=220, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    return buf.getvalue()

def fabricar_pdf_estilizado(nome_c, cid_c, dt_ref, triade_info, pot_texto, swot_data, tab_pont_raw, tab_proj_raw, planetas_pos, cuspides_pos, asc_grau):
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
    c.setFont(FONTE_BOLD_NOME, 15)
    c.drawString(40, h_page - 36, seguro_texto("ASTROLOGIA CONSCIENTE"))
    c.setFont(FONTE_UNICODE_NOME, 9.5)
    c.drawString(40, h_page - 52, seguro_texto("Relatório Executivo: Matriz Natal, Mandala & A Dança dos Ponteiros"))
    c.setFont(FONTE_OBLIQUE_NOME, 8)
    c.drawString(40, h_page - 66, seguro_texto("Pesquisa e Metodologia: Douglas Rosa (@astrolodoug)"))

    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, h_page - 135, w_page - 80, 45, 5, fill=1, stroke=1)
    c.setFillColor(cor_topo)
    c.setFont(FONTE_BOLD_NOME, 9.5)
    c.drawString(50, h_page - 105, seguro_texto(f"Consulente: {nome_c} | Local: {cid_c}"))
    c.setFont(FONTE_UNICODE_NOME, 8.5)
    c.drawString(50, h_page - 120, seguro_texto(f"Data Base da Análise: {dt_ref} | Método: APRS e Trânsitos Ativos"))

    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 152, seguro_texto("1. Síntese da Personalidade & Mandala Astrológica"))
    c.setStrokeColor(cor_azul_escuro)
    c.setLineWidth(1)
    c.line(40, h_page - 156, w_page - 40, h_page - 156)

    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, h_page - 370, 275, 205, 5, fill=1, stroke=1)
    c.setFillColor(cor_azul_escuro)
    c.setFont(FONTE_BOLD_NOME, 9)
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
        c.setFont(FONTE_UNICODE_NOME, 8.5)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(60, y_tr, seguro_texto(it))
        y_tr -= 16

    c.setFillColor(cor_azul_escuro)
    c.setFont(FONTE_BOLD_NOME, 8.5)
    c.drawString(50, h_page - 275, seguro_texto("Área de Maior Vocação & Potencial:"))
    c.setFont(FONTE_OBLIQUE_NOME, 8)
    c.setFillColor(HexColor('#2b263b'))
    c.drawString(50, h_page - 290, seguro_texto(f"Setor Focal: {pot_texto['titulo']}"))
    linhas_pot = textwrap.wrap(pot_texto['descricao'], width=48)
    y_pt = h_page - 304
    for lp in linhas_pot[:2]:
        c.drawString(50, y_pt, seguro_texto(lp))
        y_pt -= 12

    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(cor_borda)
    c.roundRect(330, h_page - 370, 225, 205, 5, fill=1, stroke=1)

    try:
        png_mandala = gerar_mandala_astrologica_png(planetas_pos, cuspides_pos, asc_grau)
        c.drawImage(ImageReader(BytesIO(png_mandala)), 333, h_page - 367, width=219, height=200, mask='auto')
    except Exception:
        c.setFillColor(cor_azul_escuro)
        c.setFont(FONTE_BOLD_NOME, 8.5)
        c.drawCentredString(442.5, h_page - 270, seguro_texto("Mandala Astrológica Natal"))

    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 390, seguro_texto("2. Análise Comportamental: Forças e Fraquezas Natais"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 394, w_page - 40, h_page - 394)

    w_box = (w_page - 90) / 2
    c.setFillColor(HexColor('#f1f8e9'))
    c.setStrokeColor(cor_verde)
    c.roundRect(40, h_page - 520, w_box, 118, 5, fill=1, stroke=1)
    c.setFillColor(cor_verde)
    c.setFont(FONTE_BOLD_NOME, 9)
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
    c.setFont(FONTE_BOLD_NOME, 9)
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

    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 542, seguro_texto("3. Posicionamento Atual dos 9 Ponteiros"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 546, w_page - 40, h_page - 546)

    y_p = h_page - 564
    for it in tab_pont_raw[:9]:
        desenhar_marcador(c, 47, y_p + 3, cor_azul_escuro)
        c.setFont(FONTE_UNICODE_NOME, 8.5)
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
    c.setFont(FONTE_BOLD_NOME, 10.5)
    c.drawString(40, h_page - 32, seguro_texto("CRONOGRAMA PREDITIVO: OPORTUNIDADES, AMEAÇAS E DIRECIONAMENTO"))

    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, h_page - 75, seguro_texto("4. Matriz Preditiva: Oportunidades & Ameaças dos Próximos 12 Meses"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, h_page - 79, w_page - 40, h_page - 79)

    c.setFillColor(HexColor('#f1f8e9'))
    c.setStrokeColor(cor_verde)
    c.roundRect(40, h_page - 215, w_box, 125, 5, fill=1, stroke=1)
    c.setFillColor(cor_verde)
    c.setFont(FONTE_BOLD_NOME, 9)
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
    c.setFont(FONTE_BOLD_NOME, 9)
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

    c.setFont(FONTE_BOLD_NOME, 11)
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

    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_pr - 10, seguro_texto("6. Guia Didático & Dedicatória Oficial"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_pr - 14, w_page - 40, y_pr - 14)

    y_card = y_pr - 150
    c.setFillColor(cor_topo)
    c.roundRect(40, y_card, w_page - 80, 125, 6, fill=1, stroke=0)

    c.setFillColor(HexColor('#64b5f6'))
    c.setFont(FONTE_BOLD_NOME, 9.5)
    c.drawString(55, y_card + 102, seguro_texto("Uma mensagem de Douglas Rosa (@astrolodoug) para você:"))
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_OBLIQUE_NOME, 8)
    c.drawString(55, y_card + 85, seguro_texto('"O mapa astral não é uma sentença estática: é uma partitura rítmica viva.'))
    c.drawString(55, y_card + 72, seguro_texto('A Dança dos Ponteiros (APRS) revela o momento exato em que cada tema'))
    c.drawString(55, y_card + 59, seguro_texto('é convocado a amadurecer ou expandir. Use essas datas como coordenadas de ação."'))

    c.setFillColor(HexColor('#64b5f6'))
    c.setFont(FONTE_BOLD_NOME, 8.5)
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

# ==================== INTERFACE WEB STREAMLIT ====================
st.markdown("""
<div style="background: rgba(31, 27, 41, 0.95); border: 1.5px solid #7df9ff; border-radius: 10px; padding: 10px 16px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;">
    <span style="color: #7df9ff; font-weight: 700; font-size: 0.98rem;">
        👉 <b>Acesso aos Dados de Nascimento:</b> Toque na seta no canto superior esquerdo (<b>&gt;</b>) para abrir o painel lateral e inserir os seus dados.
    </span>
</div>
""", unsafe_allow_html=True)

st.title("✨ Astrologia Consciente")
st.markdown("### A Dança dos Ponteiros: Relatório Preditivo e Mandala")

st.sidebar.header("⚙️ Painel de Dados do Consulente")

nome_input = st.sidebar.text_input("Nome Completo", value="", placeholder="Inserir nome")
nome = nome_input.strip() if nome_input.strip() else "Consulente"

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
    sigla_uf = ""

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
    with st.spinner("A processar cálculos astrológicos personalizados..."):
        try:
            lat, lng, tz_str = obter_geolocalizacao_segura(cidade, sigla_uf)

            sujeito = AstrologicalSubjectFactory.from_birth_data(name=nome, year=int(ano), month=int(mes), day=int(dia), hour=int(hora), minute=int(minuto), lat=float(lat), lng=float(lng), tz_str=tz_str)
            st.success(f"Mapa gerado: {nome} ({cidade}) | Data base: {DATA_ANALISE.strftime('%d/%m/%Y')}")

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

            planetas_dados = [("Sol", sujeito.sun, "☉"), ("Lua", sujeito.moon, "☽"), ("Mercúrio", sujeito.mercury, "☿"), ("Vênus", sujeito.venus, "♀"), ("Marte", sujeito.mars, "♂"), ("Júpiter", sujeito.jupiter, "♃"), ("Saturno", sujeito.saturn, "♄"), ("Urano", sujeito.uranus, "♅"), ("Netuno", sujeito.neptune, "♆"), ("Plutão", sujeito.pluto, "♇")]

            tab_pl = []
            mapa_casas_planetas = {}
            planetas_mandala = []
            natal_para_aspeto = []
            contagem_elem = {"Fogo": 0, "Terra": 0, "Ar": 0, "Água": 0}
            mapa_signo_elem = {"Áries":"Fogo","Leão":"Fogo","Sagitário":"Fogo","Touro":"Terra","Virgem":"Terra","Capricórnio":"Terra","Gêmeos":"Ar","Libra":"Ar","Aquário":"Ar","Câncer":"Água","Escorpião":"Água","Peixes":"Água"}

            for pn, po, sigla_glifo in planetas_dados:
                p_abs = float(obter_dado(po, 'abs_pos', 0.0))
                num_casa, por_orbe, orbe_val = calc_casa_orbe(p_abs, cuspides_abs)
                mapa_casas_planetas[pn] = num_casa
                s_nome = nome_sig(obter_dado(po, 'sign', ''))
                contagem_elem[mapa_signo_elem.get(s_nome, "Ar")] += 1

                planetas_mandala.append((pn, p_abs, sigla_glifo))
                natal_para_aspeto.append((pn, p_abs, s_nome, num_casa))

                rotulo_casa = f"{num_casa}ª Casa (orbe de {int(orbe_val)}°)" if por_orbe else f"{num_casa}ª Casa"
                pos_p = float(obter_dado(po, 'position', 0.0))
                tab_pl.append({
                    "Planeta": pn,
                    "Posição": f"{pos_p:.2f}° {fmt_sig(obter_dado(po, 'sign', ''))}",
                    "Casa Natal (com Orbe)": rotulo_casa,
                    "Regente": REG_TXT.get(s_nome, "Desconhecido")
                })

            casa_destaque = mapa_casas_planetas.get("Sol", 10)
            potencial_info = {
                "titulo": f"{casa_destaque}ª Casa Zodiacal",
                "descricao": POTENCIAL_CASAS.get(casa_destaque, "Foco na consolidação de projetos e autoridade pessoal.")
            }

            elem_dominante = max(contagem_elem, key=contagem_elem.get)

            def reg_de(p):
                c = casas_p.get(p, [])
                return f"Regente das {', '.join(c)}" if c else "Eixo Angular"

            dt_nasc = datetime(int(ano), int(mes), int(dia), int(hora), int(minuto))
            dias_v = (DATA_ANALISE - dt_nasc).days
            asc_b = float(obter_dado(sujeito.first_house, 'abs_pos', 0.0))

            # POSIÇÕES REAIS DOS PONTEIROS HOJE
            tab_pont = []
            ponteiros_calculados = []
            for pn, ft, pb in FATORES:
                pos_p_abs = (asc_b + (dias_v / 0.25 / ft)) % 360
                casa_pt, _, _ = calc_casa_orbe(pos_p_abs, cuspides_abs)
                item_pont = {
                    "Ponteiro": pn,
                    "Posição Atual": fmt_g(pos_p_abs),
                    "Fator": f"{ft:.3f}",
                    "Regência Ativada": reg_de(pb),
                    "pos_abs": pos_p_abs,
                    "casa": casa_pt,
                    "planeta_base": pb
                }
                tab_pont.append(item_pont)
                ponteiros_calculados.append(item_pont)

            # CÁLCULO DE ASPETOS REAIS DOS PONTEIROS HOJE
            ASPETOS_HOJE_DEF = [(0,"Conjunção","neutra",5.0),(60,"Sextil","harmonica",4.0),(90,"Quadratura","tensao",4.5),(120,"Trígono","harmonica",4.5),(180,"Oposição","tensao",5.0)]
            aspetos_hoje = []
            for pt in ponteiros_calculados:
                for pn_alvo, g_alvo, s_alvo, c_alvo in natal_para_aspeto:
                    diff = abs(pt['pos_abs'] - g_alvo) % 360
                    if diff > 180: diff = 360 - diff
                    for ang, nome_asp, tipo_asp, orbe_asp in ASPETOS_HOJE_DEF:
                        if abs(diff - ang) <= orbe_asp:
                            aspetos_hoje.append({
                                "ponteiro": pt['Ponteiro'],
                                "casa_ponteiro": pt['casa'],
                                "alvo_nome": pn_alvo,
                                "alvo_casa": c_alvo,
                                "aspeto": nome_asp,
                                "tipo": tipo_asp,
                                "orbe": abs(diff - ang)
                            })
            aspetos_hoje.sort(key=lambda x: x['orbe'])

            # PROJEÇÃO DINÂMICA REAL DOS PRÓXIMOS 12 MESES
            eventos_todos = calcular_projecoes_reais(DATA_ANALISE, dt_nasc, asc_b, natal_para_aspeto, casas_p, FATORES)
            cronograma_12m = selecionar_cronograma_equilibrado(eventos_todos, 8)
            tab_fp = [{"Data": ev['data_str'], "Ponteiro": ev['ponteiro'], "Aspecto": ev['aspecto'], "Regência": ev['regencia']} for ev in cronograma_12m]

            # TRÂNSITOS REAIS DE PLANETAS LENTOS
            try:
                sujeito_tr = AstrologicalSubjectFactory.from_birth_data(name="Trânsitos", year=int(DATA_ANALISE.year), month=int(DATA_ANALISE.month), day=int(DATA_ANALISE.day), hour=12, minute=0, lat=float(lat), lng=float(lng), tz_str=tz_str)
                pos_lentos_hoje = {
                    "Júpiter": float(obter_dado(sujeito_tr.jupiter, 'abs_pos', 0.0)),
                    "Saturno": float(obter_dado(sujeito_tr.saturn, 'abs_pos', 0.0)),
                    "Urano": float(obter_dado(sujeito_tr.uranus, 'abs_pos', 0.0)),
                    "Netuno": float(obter_dado(sujeito_tr.neptune, 'abs_pos', 0.0)),
                    "Plutão": float(obter_dado(sujeito_tr.pluto, 'abs_pos', 0.0))
                }
            except Exception:
                pos_lentos_hoje = {"Júpiter": 125.0, "Saturno": 28.0, "Urano": 65.0, "Netuno": 3.0, "Plutão": 303.0}

            tab_ta = []
            for p_lento, g_lento in pos_lentos_hoje.items():
                for pn_alvo, g_alvo, s_alvo, c_alvo in natal_para_aspeto[:5]:
                    diff = abs(g_lento - g_alvo) % 360
                    if diff > 180: diff = 360 - diff
                    for ang, nome_asp, _, orbe_asp in ASPETOS_HOJE_DEF:
                        if abs(diff - ang) <= orbe_asp + 1.5:
                            tab_ta.append({
                                "Trânsito": p_lento,
                                "Aspecto": nome_asp,
                                "Natal Alvo": f"{pn_alvo} Natal",
                                "Regência Ativada": f"{p_lento} {reg_de(p_lento)}",
                                "orbe": abs(diff - ang)
                            })
            tab_ta.sort(key=lambda x: x['orbe'])
            if not tab_ta:
                tab_ta = [{"Trânsito": "Saturno", "Aspecto": "Trânsito Angular", "Natal Alvo": "Eixo Cardinal", "Regência Ativada": "Saturno"}]

            # SWOT 100% DINÂMICO BASEADO NO MAPA NATAL E PROJEÇÕES
            sol_dict_info = {"signo": nome_sig(obter_dado(sujeito.sun, 'sign', '')), "casa": mapa_casas_planetas.get("Sol", 10)}
            lua_dict_info = {"signo": nome_sig(obter_dado(sujeito.moon, 'sign', '')), "casa": mapa_casas_planetas.get("Lua", 4)}
            asc_dict_info = {"signo": nome_sig(obter_dado(sujeito.first_house, 'sign', '')), "casa": 1}

            swot_data = gerar_swot_dinamico(sol_dict_info, lua_dict_info, asc_dict_info, elem_dominante, contagem_elem, eventos_todos)

            # BÚSSOLA CONSCIENTE DO DIA (PERSONALIZADA)
            frase_dia, dica_pratica = calcular_bussola_do_dia(DATA_ANALISE, aspetos_hoje, tab_pont)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1f1b29 0%, #2b263b 100%);
                        border: 1.5px solid #7df9ff; border-radius: 12px; padding: 18px; margin: 15px 0 25px 0;
                        box-shadow: 0 4px 20px rgba(125, 249, 255, 0.18);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span style="font-size: 1.4rem;">🧭</span>
                    <span style="color: #7df9ff; font-weight: 700; font-size: 1.15rem; letter-spacing: 0.5px;">BÚSSOLA DO DIA & DIRECIONAMENTO CONSCIENTE ({DATA_ANALISE.strftime('%d/%m/%Y')})</span>
                </div>
                <p style="color: #ffffff; font-size: 1.05rem; line-height: 1.5; font-weight: 500; margin: 0 0 10px 0;">
                    <i>"{frase_dia}"</i>
                </p>
                <div style="background: rgba(125, 249, 255, 0.08); border-left: 3px solid #7df9ff; padding: 8px 12px; border-radius: 4px;">
                    <p style="color: #dcd6f7; font-size: 0.92rem; margin: 0;">
                        <b>Dica Prática para Hoje:</b> {dica_pratica}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🔵 Mandala Astrológica (Roda do Mapa Natal)")
            svg = svg_mandala(sujeito)
            if svg: st.components.v1.html(svg, height=650, scrolling=True)

            st.markdown("---")
            st.markdown("### 🏛️ Cúspides e Regências das Casas Natais")
            st.table(tab_c)

            st.markdown("---")
            st.markdown("### 🪐 Posicionamentos Natais nas Casas (com Orbes de Cúspides)")
            st.caption("ℹ️ Orbes aplicadas: 10° antes das Casas Angulares (1, 4, 7, 10) | 5° antes das Sucedentes (2, 5, 8, 11) | 3° antes das Cadentes (3, 6, 9, 12).")
            st.table(tab_pl)

            st.markdown("---")
            st.markdown(f"### 🔭 Os 9 Ponteiros Ativos em {DATA_ANALISE.strftime('%d/%m/%Y')}")
            st.table(tab_pont)

            st.markdown("---")
            st.markdown(f"### ⚡ Trânsitos de Planetas Lentos Ativos ({DATA_ANALISE.strftime('%d/%m/%Y')})")
            st.table([{"Trânsito": it["Trânsito"], "Aspecto": it["Aspecto"], "Natal Alvo": it["Natal Alvo"], "Regência": it["Regência Ativada"]} for it in tab_ta[:4]])

            st.markdown("---")
            st.markdown("## 🔒 Desbloqueie a Projeção de 12 Meses & Receba o seu Resumo")
            st.info("Insira o seu WhatsApp ou E-mail e clique em **'Confirmar e Liberar'** para baixar o relatório executivo em PDF ou recebê-lo via mensagem:")

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

                sol_sn = nome_sig(obter_dado(sujeito.sun, 'sign', ''))
                lua_sn = nome_sig(obter_dado(sujeito.moon, 'sign', ''))
                asc_sn = nome_sig(obter_dado(sujeito.first_house, 'sign', ''))

                sol_pos = float(obter_dado(sujeito.sun, 'position', 0.0))
                lua_pos = float(obter_dado(sujeito.moon, 'position', 0.0))
                asc_pos = float(obter_dado(sujeito.first_house, 'position', 0.0))

                triade_resumo = {
                    "sol": f"{sol_pos:.2f}° {GLIFOS.get(sol_sn, '')} {sol_sn} (Casa {mapa_casas_planetas.get('Sol',1)})",
                    "lua": f"{lua_pos:.2f}° {GLIFOS.get(lua_sn, '')} {lua_sn} (Casa {mapa_casas_planetas.get('Lua',1)})",
                    "asc": f"{asc_pos:.2f}° {GLIFOS.get(asc_sn, '')} {asc_sn} (1ª Casa)"
                }

                pdf_bytes = fabricar_pdf_estilizado(
                    nome_c=nome, cid_c=cidade, dt_ref=DATA_ANALISE.strftime('%d/%m/%Y'),
                    triade_info=triade_resumo, pot_texto=potencial_info, swot_data=swot_data,
                    tab_pont_raw=tab_pont_pdf, tab_proj_raw=tab_fp,
                    planetas_pos=planetas_mandala, cuspides_pos=cuspides_abs, asc_grau=asc_b
                )

                st.success(f"✅ Contacto registado: **{st.session_state.contato_salvo}**! O seu relatório executivo completo foi gerado:")

                msg_txt = f"Olá Douglas Rosa (@astrolodoug)!\n\n"
                msg_txt += f"Gerei meu mapa na Astrologia Consciente:\n"
                msg_txt += f"👤 *Consulente:* {nome} ({cidade})\n"
                msg_txt += f"📱 *Meu Contato:* {st.session_state.contato_salvo}\n"
                msg_txt += f"📅 *Data Base:* {DATA_ANALISE.strftime('%d/%m/%Y')}\n\n"
                msg_txt += f"🌟 *Área de Maior Potencial:* {potencial_info['titulo']}\n\n"
                msg_txt += "🔭 *Ponteiros Ativos em Destaque:*\n"
                for p_it in tab_pont[:4]:
                    msg_txt += f"• {p_it['Ponteiro']}: {p_it['Posição Atual']}\n"
                msg_txt += "\n📅 *Próximas Ativações Calculadas (12 Meses):*\n"
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
                st.markdown(f"### 📅 Projeção Real dos 9 Ponteiros (12 Meses a partir de {DATA_ANALISE.strftime('%d/%m/%Y')})")
                st.table(tab_fp)

                st.markdown("## 🧠 Síntese Interpretativa e Direcionamento Consciente")
                ce, cd = st.columns(2)
                with ce:
                    st.markdown("### ⚠️ Setores de Tensão & Rigor Construtivo")
                    for am in swot_data['ameacas'][:2]:
                        st.warning(am)
                    st.info("Orientação Consciente: A tensão preditiva não é fatalidade, mas sim um filtro de método e maturidade.")
                with cd:
                    st.markdown("### ✨ Setores de Fluxo & Oportunidade")
                    for op in swot_data['oportunidades'][:2]:
                        st.success(op)
                    st.info("Orientação Consciente: Aproveite as janelas de harmonia para iniciar projetos e firmar acordos sólidos.")
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
