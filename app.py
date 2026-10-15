import os, json, ssl, math, base64, textwrap, urllib.request, urllib.parse
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

# ==================== FUNDO COM SÍMBOLOS ASTROLÓGICOS ====================
SVG_FUNDO_ASTRO = """<svg xmlns="http://www.w3.org/2000/svg" width="440" height="440" viewBox="0 0 440 440">
  <g fill="none" stroke="#7df9ff" stroke-opacity="0.06">
    <circle cx="220" cy="220" r="165" stroke-width="1" stroke-dasharray="4 6"/>
    <circle cx="220" cy="220" r="125" stroke-width="0.8"/>
    <circle cx="220" cy="220" r="55" stroke-width="0.7" stroke-dasharray="2 4"/>
    <line x1="40" y1="220" x2="400" y2="220" stroke-width="0.6" stroke-dasharray="3 6"/>
    <line x1="220" y1="40" x2="220" y2="400" stroke-width="0.6" stroke-dasharray="3 6"/>
    <line x1="92" y1="92" x2="348" y2="348" stroke-width="0.4" stroke-dasharray="2 8"/>
    <line x1="348" y1="92" x2="92" y2="348" stroke-width="0.4" stroke-dasharray="2 8"/>
    <polyline points="35,60 75,40 115,68 140,35" stroke-width="0.7" stroke-opacity="0.08"/>
    <polyline points="310,385 355,365 395,390 420,360" stroke-width="0.7" stroke-opacity="0.08"/>
  </g>
  <g fill="#7df9ff" fill-opacity="0.085" font-family="DejaVu Sans, Segoe UI Symbol, sans-serif" text-anchor="middle">
    <text x="220" y="45" font-size="20">♈</text>
    <text x="308" y="68" font-size="18">♉</text>
    <text x="372" y="132" font-size="19">♊</text>
    <text x="395" y="226" font-size="20">♋</text>
    <text x="372" y="315" font-size="19">♌</text>
    <text x="308" y="378" font-size="18">♍</text>
    <text x="220" y="402" font-size="20">♎</text>
    <text x="132" y="378" font-size="18">♏</text>
    <text x="68" y="315" font-size="19">♐</text>
    <text x="45" y="226" font-size="20">♑</text>
    <text x="68" y="132" font-size="19">♒</text>
    <text x="132" y="68" font-size="18">♓</text>
  </g>
  <g fill="#dcd6f7" fill-opacity="0.075" font-family="DejaVu Sans, Segoe UI Symbol, sans-serif" text-anchor="middle">
    <text x="220" y="145" font-size="17">☉</text>
    <text x="295" y="185" font-size="16">☽</text>
    <text x="285" y="270" font-size="16">☿</text>
    <text x="220" y="305" font-size="17">♀</text>
    <text x="155" y="270" font-size="16">♂</text>
    <text x="145" y="185" font-size="16">♃</text>
    <text x="38" y="38" font-size="18">♄</text>
    <text x="402" y="38" font-size="18">♅</text>
    <text x="38" y="410" font-size="18">♆</text>
    <text x="402" y="410" font-size="18">♇</text>
    <text x="190" y="225" font-size="13">✦</text>
    <text x="250" y="225" font-size="13">✧</text>
    <circle cx="35" cy="60" r="1.8" fill="#7df9ff" fill-opacity="0.15"/>
    <circle cx="75" cy="40" r="2.2" fill="#7df9ff" fill-opacity="0.18"/>
    <circle cx="115" cy="68" r="1.8" fill="#7df9ff" fill-opacity="0.15"/>
    <circle cx="355" cy="365" r="2.2" fill="#7df9ff" fill-opacity="0.18"/>
    <circle cx="395" cy="390" r="1.8" fill="#7df9ff" fill-opacity="0.15"/>
  </g>
</svg>"""

B64_FUNDO_ASTRO = base64.b64encode(SVG_FUNDO_ASTRO.encode("utf-8")).decode("utf-8")

st.markdown(f"""
<style>
.stApp {{
    background-color: #2b263b !important;
    background-image: url("data:image/svg+xml;base64,{B64_FUNDO_ASTRO}") !important;
    background-repeat: repeat !important;
    background-size: 420px 420px !important;
    background-attachment: fixed !important;
    color: #f0f0f0;
}}
header[data-testid="stHeader"] {{
    background-color: #1f1b29 !important;
    border-bottom: 1px solid rgba(125, 249, 255, 0.2) !important;
}}
[data-testid="stSidebarCollapsedControl"] {{
    background-color: #1f1b29 !important;
    border: 1.5px solid #7df9ff !important;
    border-radius: 8px !important;
    padding: 3px 8px !important;
    box-shadow: 0 0 12px rgba(125, 249, 255, 0.35) !important;
}}
[data-testid="stSidebarCollapsedControl"]:hover {{ background-color: #2b263b !important; }}
[data-testid="stSidebarCollapsedControl"] svg {{ fill: #7df9ff !important; stroke: #7df9ff !important; }}
[data-testid="stSidebar"] {{
    background-color: #1f1b29 !important;
    background-image: url("data:image/svg+xml;base64,{B64_FUNDO_ASTRO}") !important;
    background-repeat: repeat !important;
    background-size: 360px 360px !important;
    color: #f0f0f0;
}}
h1, h2, h3 {{ color: #7df9ff !important; }}
p, label, span {{ color: #dcd6f7 !important; }}

.stButton > button {{
    background: linear-gradient(135deg, #7df9ff 0%, #48cae4 100%) !important;
    border: 1px solid #7df9ff !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 4px 14px rgba(125, 249, 255, 0.35) !important;
    width: 100% !important;
}}
.stButton > button p, .stButton > button span {{
    color: #0e0b16 !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
}}

[data-testid="stLinkButton"] > a {{
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.4px !important;
    border-radius: 10px !important;
    transition: all 0.25s ease-in-out !important;
    text-align: center !important;
    padding: 0.65rem 1rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
}}
[data-testid="stLinkButton"] > a:hover {{
    transform: translateY(-2px) scale(1.015) !important;
}}
[data-testid="stLinkButton"] > a p, [data-testid="stLinkButton"] > a span {{
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 1.02rem !important;
}}
[data-testid="stLinkButton"] > a[href*="wa.me"], [data-testid="stLinkButton"] > a[href*="whatsapp.com"] {{
    background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important;
    border: 1.5px solid #25D366 !important;
    box-shadow: 0 4px 16px rgba(37, 211, 102, 0.45) !important;
}}
[data-testid="stLinkButton"] > a[href*="instagram.com"] {{
    background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%) !important;
    border: 1.5px solid #f09433 !important;
    box-shadow: 0 4px 16px rgba(220, 39, 67, 0.45) !important;
}}
[data-testid="stLinkButton"] > a[href*="youtube.com"] {{
    background: linear-gradient(135deg, #FF0000 0%, #b20710 100%) !important;
    border: 1.5px solid #FF0000 !important;
    box-shadow: 0 4px 16px rgba(255, 0, 0, 0.45) !important;
}}
.stSuccess, .stInfo, .stWarning {{
    background: rgba(31, 27, 41, 0.92) !important;
    color: #7df9ff !important;
    border: 1px solid #7df9ff;
}}
[data-testid="stTable"] {{
    background: rgba(31, 27, 41, 0.82) !important;
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

SIGNOS = [("Áries","♈"),("Touro","♉"),("Gêmeos","♊"),("Câncer","♋"),("Leão","♌"),("Virgem","♍"),("Libra","♎"),("Escorpião","♏"),("Sagitário","♐"),("Capricórnio","♑"),("Aquário","♒"),("Peixes","♓")]
SIGLAS = {"Ari":"Áries","Tau":"Touro","Gem":"Gêmeos","Can":"Câncer","Leo":"Leão","Vir":"Virgem","Lib":"Libra","Sco":"Escorpião","Sag":"Sagitário","Cap":"Capricórnio","Aqu":"Aquário","Pis":"Peixes"}
GLIFOS = dict(SIGNOS)
REGENTES = {"Áries":["Marte"],"Touro":["Vênus"],"Gêmeos":["Mercúrio"],"Câncer":["Lua"],"Leão":["Sol"],"Virgem":["Mercúrio"],"Libra":["Vênus"],"Escorpião":["Marte","Plutão"],"Sagitário":["Júpiter"],"Capricórnio":["Saturno"],"Aquário":["Saturno","Urano"],"Peixes":["Júpiter","Netuno"]}
REG_TXT = {"Áries":"Marte","Touro":"Vênus","Gêmeos":"Mercúrio","Câncer":"Lua","Leão":"Sol","Virgem":"Mercúrio","Libra":"Vênus","Escorpião":"Marte e Plutão","Sagitário":"Júpiter","Capricórnio":"Saturno","Aquário":"Saturno e Urano","Peixes":"Júpiter e Netuno"}

def dec_para_graus_minutos(val):
    val = float(val) % 30.0
    graus = int(val)
    minutos = int(round((val - graus) * 60))
    if minutos == 60:
        graus += 1
        minutos = 0
    if graus == 30:
        graus = 0
    return graus, minutos

def fmt_g(g):
    g = float(g) % 360.0
    idx = int(g // 30)
    sob = g % 30.0
    graus, minutos = dec_para_graus_minutos(sob)
    n, gl = SIGNOS[idx]
    return f"{graus}° {minutos:02d}' {gl} {n}"

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

FORCAS_SIGNOS = {
    "Áries": "Pioneirismo, assertividade nas decisões e coragem para abrir novos caminhos.",
    "Touro": "Capacidade de sustentação material, persistência e fidelidade a valores práticos.",
    "Gêmeos": "Versatilidade mental, rapidez de articulação lógica e talento para conectar saberes.",
    "Câncer": "Faro intuitivo aguçado, empatia protetora e poder de mobilização emocional genuína.",
    "Leão": "Magnetismo pessoal radiante, generosidade autoral e autoridade natural na liderança.",
    "Virgem": "Discernimento analítico cirúrgico, domínio técnico impecável e busca por excelência.",
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

# ==================== TODAS AS 27 UNIDADES FEDERATIVAS (ESTADOS + DF) ====================
ESTADOS_BR = [
    "AC - Acre", "AL - Alagoas", "AP - Amapá", "AM - Amazonas", "BA - Bahia",
    "CE - Ceará", "DF - Distrito Federal (Brasília)", "ES - Espírito Santo", "GO - Goiás (Goiânia)",
    "MA - Maranhão", "MT - Mato Grosso", "MS - Mato Grosso do Sul", "MG - Minas Gerais",
    "PA - Pará", "PB - Paraíba", "PR - Paraná", "PE - Pernambuco", "PI - Piauí",
    "RJ - Rio de Janeiro", "RN - Rio Grande do Norte", "RS - Rio Grande do Sul",
    "RO - Rondônia", "RR - Roraima", "SC - Santa Catarina", "SP - São Paulo",
    "SE - Sergipe", "TO - Tocantins"
]

CAPITAIS_BR = {
    "AC": "Rio Branco", "AL": "Maceió", "AP": "Macapá", "AM": "Manaus",
    "BA": "Salvador", "CE": "Fortaleza", "DF": "Brasília", "ES": "Vitória",
    "GO": "Goiânia", "MA": "São Luís", "MT": "Cuiabá", "MS": "Campo Grande",
    "MG": "Belo Horizonte", "PA": "Belém", "PB": "João Pessoa", "PR": "Curitiba",
    "PE": "Recife", "PI": "Teresina", "RJ": "Rio de Janeiro", "RN": "Natal",
    "RS": "Porto Alegre", "RO": "Porto Velho", "RR": "Boa Vista",
    "SC": "Florianópolis", "SP": "São Paulo", "SE": "Aracaju", "TO": "Palmas"
}

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

# ==================== BASE LOCAL CURADA PARA TODOS OS 27 ESTADOS ====================
CIDADES_BASE_POR_UF = {
    "AC": ["Acrelândia", "Assis Brasil", "Brasiléia", "Bujari", "Capixaba", "Cruzeiro do Sul", "Epitaciolândia", "Feijó", "Jordão", "Mâncio Lima", "Manoel Urbano", "Marechal Thaumaturgo", "Plácido de Castro", "Porto Acre", "Porto Walter", "Rio Branco", "Rodrigues Alves", "Santa Rosa do Purus", "Sena Madureira", "Senador Guiomard", "Tarauacá", "Xapuri"],
    "AL": ["Maceió", "Arapiraca", "Palmeira dos Índios", "Rio Largo", "Penedo", "União dos Palmares", "São Miguel dos Campos", "Campo Alegre", "Coruripe", "Delmiro Gouveia", "Marechal Deodoro", "Santana do Ipanema", "Atalaia", "Teotônio Vilela", "Pilar", "Girau do Ponciano", "São Sebastião", "Maragogi", "São José da Tapera", "Murici", "Boca da Mata", "Ibateguara", "Viçosa", "Porto Real do Colégio", "Igreja Nova", "Piranhas", "Mata Grande", "Capela", "Joaquim Gomes", "Traipu", "Messias", "Barra de Santo Antônio", "Paripueira"],
    "AP": ["Amapá", "Calçoene", "Cutias", "Ferreira Gomes", "Itaubal", "Laranjal do Jari", "Macapá", "Mazagão", "Oiapoque", "Pedra Branca do Amapari", "Porto Grande", "Pracuúba", "Santana", "Serra do Navio", "Tartarugalzinho", "Vitória do Jari"],
    "AM": ["Manaus", "Parintins", "Itacoatiara", "Manacapuru", "Coari", "Tabatinga", "Maués", "Tefé", "Manicoré", "Humaitá", "Iranduba", "São Gabriel da Cachoeira", "Benjamin Constant", "Borba", "Autazes", "Nova Olinda do Norte", "Careiro", "Lábrea", "Presidente Figueiredo", "Boca do Acre", "Eirunepé", "Carauari", "Barcelos", "Novo Aripuanã", "Santo Antônio do Içá", "Uarini", "Jutaí", "Fonte Boa", "Envira"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Juazeiro", "Itabuna", "Lauro de Freitas", "Ilhéus", "Jequié", "Teixeira de Freitas", "Barreiras", "Alagoinhas", "Porto Seguro", "Simões Filho", "Paulo Afonso", "Eunápolis", "Santo Antônio de Jesus", "Valença", "Candeias", "Guanambi", "Jacobina", "Serrinha", "Senhor do Bonfim", "Dias d'Ávila", "Luís Eduardo Magalhães", "Itapetinga", "Irecê", "Campo Formoso", "Casa Nova", "Bom Jesus da Lapa", "Brumado", "Conceição do Coité", "Itaberaba", "Cruz das Almas", "Euclides da Cunha", "Ipirá", "Santo Amaro", "Ribeira do Pombal", "Tucano", "Mata de São João", "Caetité", "Poções", "Livramento de Nossa Senhora", "Seabra", "Itacaré", "Lençóis", "Morro de São Paulo"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral", "Crato", "Itapipoca", "Maranguape", "Iguatu", "Quixadá", "Pacatuba", "Aquiraz", "Quixeramobim", "Canindé", "Russas", "Tianguá", "Crateús", "Aracati", "Cascavel", "Pacajus", "Icó", "Horizonte", "Camocim", "Morada Nova", "Acaraú", "Viçosa do Ceará", "Barbalha", "Limoeiro do Norte", "Tauá", "Trairi", "Granja", "Boa Viagem", "São Gonçalo do Amarante", "Brejo Santo", "Eusébio", "Baturité", "Jijoca de Jericoacoara", "Guaramiranga"],
    "DF": ["Brasília", "Ceilândia", "Samambaia", "Taguatinga", "Plano Piloto", "Planaltina", "Águas Claras", "Guará", "Gama", "Recanto das Emas", "Santa Maria", "Sobradinho", "São Sebastião", "Vicente Pires", "Paranoá", "Itapoã", "Sudoeste/Octogonal", "Brazlândia", "Riacho Fundo", "Candangolândia", "Núcleo Bandeirante", "Cruzeiro", "Lago Sul", "Lago Norte", "Park Way"],
    "ES": ["Vitória", "Vila Velha", "Serra", "Cariacica", "Cachoeiro de Itapemirim", "Linhares", "São Mateus", "Colatina", "Guarapari", "Aracruz", "Viana", "Nova Venécia", "Barra de São Francisco", "Marataízes", "Castelo", "Santa Maria de Jetibá", "Domingos Martins", "Itapemirim", "Afonso Cláudio", "Anchieta", "Alegre", "Iúna", "Pinheiros", "Conceição da Barra", "Jaguaré", "Ecoporanga", "Guaçuí"],
    "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Águas Lindas de Goiás", "Luziânia", "Valparaíso de Goiás", "Trindade", "Formosa", "Novo Gama", "Senador Canedo", "Itumbiara", "Catalão", "Jataí", "Planaltina", "Caldas Novas", "Santo Antônio do Descoberto", "Cidade Ocidental", "Goianésia", "Cristalina", "Mineiros", "Morrinhos", "Inhumas", "Quirinópolis", "Jaraguá", "Porangatu", "Uruaçu", "Pires do Rio", "Goiás Velho", "Pirenópolis", "Niquelândia", "Goiatuba", "Posse"],
    "MA": ["São Luís", "Imperatriz", "São José de Ribamar", "Timon", "Caxias", "Codó", "Paço do Lumiar", "Açailândia", "Bacabal", "Balsas", "Santa Inês", "Barra do Corda", "Pinheiro", "Chapadinha", "Santa Luzia", "Buriticupu", "Grajaú", "Itapecuru Mirim", "Coroatá", "Barreirinhas", "Tutóia", "Viana", "Zé Doca", "Coelho Neto", "Presidente Dutra", "Lago da Pedra", "Araioses", "São Bento", "Rosário", "Carolina", "Pedreiras", "Cururupu", "Estreito"],
    "MT": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Tangará da Serra", "Sorriso", "Lucas do Rio Verde", "Primavera do Leste", "Barra do Garças", "Alta Floresta", "Cáceres", "Pontes e Lacerda", "Nova Mutum", "Juína", "Campo Verde", "Juara", "Barra do Bugres", "Peixoto de Azevedo", "Colíder", "Campo Novo do Parecis", "Guarantã do Norte", "Poconé", "Chapada dos Guimarães", "Jaciara", "Água Boa"],
    "MS": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá", "Ponta Porã", "Sidrolândia", "Naviraí", "Nova Andradina", "Aquidauana", "Maracaju", "Paranaíba", "Amambai", "Rio Brilhante", "Coxim", "Caarapó", "Miranda", "São Gabriel do Oeste", "Jardim", "Anastácio", "Bonito", "Aparecida do Taboado", "Bataguassu", "Ribas do Rio Pardo", "Ladário", "Cassilândia"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Ribeirão das Neves", "Uberaba", "Governador Valadares", "Ipatinga", "Sete Lagoas", "Divinópolis", "Santa Luzia", "Ibirité", "Poços de Caldas", "Patos de Minas", "Pouso Alegre", "Teófilo Otoni", "Barbacena", "Sabará", "Varginha", "Vespasiano", "Conselheiro Lafaiete", "Itabira", "Araguari", "Ubá", "Passos", "Coronel Fabriciano", "Muriaé", "Ituiutaba", "Lavras", "Itajubá", "Nova Serrana", "Itaúna", "Pará de Minas", "Paracatu", "Caratinga", "Nova Lima", "São João del-Rei", "Patrocínio", "Timóteo", "Manhuaçu", "Unaí", "Curvelo", "Alfenas", "João Monlevade", "Três Corações", "Viçosa", "Cataguases", "Ouro Preto", "Janaúba", "São Sebastião do Paraíso", "Januária", "Formiga", "Esmeraldas", "Pedro Leopoldo", "Ponte Nova", "Mariana", "Diamantina", "São Lourenço", "Tiradentes", "Caxambu", "Guaxupé", "Frutal", "Lagoa Santa"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá", "Parauapebas", "Castanhal", "Abaetetuba", "Cametá", "Marituba", "Bragança", "São Félix do Xingu", "Barcarena", "Altamira", "Tucuruí", "Paragominas", "Tailândia", "Breves", "Itaituba", "Redenção", "Moju", "Novo Repartimento", "Oriximiná", "Santana do Araguaia", "Santa Izabel do Pará", "Capanema", "Tomé-Açu", "Igarapé-Miri", "Benevides", "Portel", "Viseu", "Dom Eliseu", "Ulianópolis", "Alenquer", "Almeirim", "Salinópolis", "Soure", "Monte Alegre"],
    "PB": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos", "Bayeux", "Sousa", "Cajazeiras", "Cabedelo", "Guarabira", "Mamanguape", "Queimadas", "São Bento", "Monteiro", "Esperança", "Pombal", "Catolé do Rocha", "Alagoa Grande", "Conde", "Princesa Isabel", "Solânea", "Rio Tinto", "Itabaiana", "Sapé", "Lagoa Seca", "Bananeiras", "Picuí", "Ingá", "Areia"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel", "São José dos Pinhais", "Foz do Iguaçu", "Colombo", "Guarapuava", "Paranaguá", "Araucária", "Toledo", "Apucarana", "Pinhais", "Campo Largo", "Arapongas", "Almirante Tamandaré", "Umuarama", "Piraquara", "Cambé", "Fazenda Rio Grande", "Sarandi", "Campo Mourão", "Francisco Beltrão", "Paranavaí", "Pato Branco", "Cianorte", "Telêmaco Borba", "Castro", "Rolândia", "Irati", "União da Vitória", "Ibiporã", "Prudentópolis", "Marechal Cândido Rondon", "Cornélio Procópio", "Medianeira", "Palmas", "Matinhos", "Guaratuba", "Morretes", "Antonina"],
    "PE": ["Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina", "Paulista", "Cabo de Santo Agostinho", "Camaragibe", "Garanhuns", "Vitória de Santo Antão", "Igarassu", "São Lourenço da Mata", "Santa Cruz do Capibaribe", "Abreu e Lima", "Ipojuca", "Serra Talhada", "Araripina", "Gravatá", "Carpina", "Goiana", "Belo Jardim", "Arcoverde", "Ouricuri", "Escada", "Pesqueira", "Surubim", "Palmares", "Bezerros", "Salgueiro", "Paudalho", "Limoeiro", "Buíque", "Toritama", "Fernando de Noronha", "Porto de Galinhas", "Tamandaré", "Triunfo"],
    "PI": ["Teresina", "Parnaíba", "Picos", "Piripiri", "Floriano", "Barras", "Campo Maior", "União", "Altos", "Esperantina", "Pedro II", "Oeiras", "José de Freitas", "São Raimundo Nonato", "Miguel Alves", "Luís Correia", "Piracuruca", "Cocal", "Batalha", "Corrente", "Valença do Piauí", "Paulistana", "Bom Jesus", "Uruçuí", "São João do Piauí", "Castelo do Piauí"],
    "RJ": ["Rio de Janeiro", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Niterói", "Belford Roxo", "Campos dos Goytacazes", "São João de Meriti", "Petrópolis", "Volta Redonda", "Magé", "Macaé", "Itaboraí", "Cabo Frio", "Angra dos Reis", "Nova Friburgo", "Barra Mansa", "Teresópolis", "Mesquita", "Maricá", "Rio das Ostras", "Nilópolis", "Queimados", "Itaguaí", "Araruama", "Resende", "São Pedro da Aldeia", "Itaperuna", "Barra do Piraí", "Saquarema", "Seropédica", "Três Rios", "Valença", "Paracambi", "Guapimirim", "Casimiro de Abreu", "Armação dos Búzios", "Paraty", "Arraial do Cabo", "Mangaratiba", "Miguel Pereira", "Vassouras", "Piraí"],
    "RN": ["Natal", "Mossoró", "Parnamirim", "São Gonçalo do Amarante", "Ceará-Mirim", "Macaíba", "Caicó", "Açu", "Currais Novos", "São José de Mipibu", "Santa Cruz", "Nova Cruz", "Apodi", "João Câmara", "Canguaretama", "Touros", "Macau", "Pau dos Ferros", "Areia Branca", "Extremoz", "Baraúna", "Nísia Floresta", "Goianinha", "Santo Antônio", "Tibau do Sul", "Pipa", "São Miguel do Gostoso"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Canoas", "Pelotas", "Santa Maria", "Gravataí", "Viamão", "Novo Hamburgo", "São Leopoldo", "Rio Grande", "Alvorada", "Passo Fundo", "Sapucaia do Sul", "Uruguaiana", "Santa Cruz do Sul", "Cachoeirinha", "Bagé", "Bento Gonçalves", "Erechim", "Guaíba", "Carazinho", "Santana do Livramento", "Ijuí", "Santa Rosa", "Esteio", "Campo Bom", "Santo Ângelo", "Alegrete", "Lajeado", "Farroupilha", "Montenegro", "Vacaria", "São Borja", "Cruz Alta", "Sapiranga", "Torres", "Gramado", "Canela", "Tramandaí", "Capão da Canoa", "Osório", "Taquara", "Venâncio Aires", "São Gabriel"],
    "RO": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Vilhena", "Cacoal", "Jaru", "Rolim de Moura", "Guajará-Mirim", "Ouro Preto do Oeste", "Pimenta Bueno", "Buritis", "Machadinho d'Oeste", "Espigão d'Oeste", "Alta Floresta d'Oeste", "Nova Mamoré", "Candeias do Jamari", "São Miguel do Guaporé", "Cerejeiras", "Colorado do Oeste"],
    "RR": ["Alto Alegre", "Amajari", "Boa Vista", "Bonfim", "Cantá", "Caracaraí", "Caroebe", "Iracema", "Mucajaí", "Normandia", "Pacaraima", "Rorainópolis", "São João da Baliza", "São Luiz", "Uiramutã"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "São José", "Chapecó", "Criciúma", "Itajaí", "Jaraguá do Sul", "Palhoça", "Lages", "Balneário Camboriú", "Brusque", "Tubarão", "São Bento do Sul", "Caçador", "Camboriú", "Navegantes", "Concórdia", "Rio do Sul", "Araranguá", "Gaspar", "Biguaçu", "Indaial", "Itapema", "Mafra", "Canoinhas", "Içara", "Videira", "São Francisco do Sul", "Xanxerê", "Imbituba", "Laguna", "Timbó", "São Miguel do Oeste", "Fraiburgo", "Porto Belo", "Garopaba", "Bombinhas"],
    "SP": ["São Paulo", "Guarulhos", "Campinas", "São Bernardo do Campo", "Santo André", "São José dos Campos", "Osasco", "Ribeirão Preto", "Sorocaba", "Santos", "Mauá", "São José do Rio Preto", "Mogi das Cruzes", "Diadema", "Jundiaí", "Piracicaba", "Carapicuíba", "Bauru", "Itaquaquecetuba", "São Vicente", "Franca", "Praia Grande", "Guarujá", "Taubaté", "Limeira", "Suzano", "Taboão da Serra", "Sumaré", "Barueri", "Embu das Artes", "Indaiatuba", "Cotia", "Americana", "Marília", "Araraquara", "Jacareí", "Presidente Prudente", "Itapevi", "Hortolândia", "Rio Claro", "Araçatuba", "Santa Bárbara d'Oeste", "Ferraz de Vasconcelos", "Francisco Morato", "Itapecerica da Serra", "Itu", "Bragança Paulista", "Pindamonhangaba", "São Caetano do Sul", "Itapetininga", "Mogi Guaçu", "Jaú", "Botucatu", "Atibaia", "Santana de Parnaíba", "Araras", "Valinhos", "Sertãozinho", "Votorantim", "Barretos", "Catanduva", "Guaratinguetá", "Birigui", "Jandira", "Poá", "Salto", "Várzea Paulista", "Tatuí", "Caraguatatuba", "Itatiba", "Ourinhos", "Assis", "Lins", "Paulínia", "Ubatuba", "São Sebastião", "Ilhabela", "Águas de Lindóia", "Campos do Jordão", "Bertioga", "Avaré", "Bebedouro", "Mogi Mirim", "Votuporanga"],
    "SE": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto", "Itabaiana", "São Cristóvão", "Estância", "Tobias Barreto", "Simão Dias", "Itabaianinha", "Poço Redondo", "Nossa Senhora da Glória", "Propriá", "Itaporanga d'Ajuda", "Capela", "Laranjeiras", "Boquim", "Barra dos Coqueiros", "Umbaúba", "Poço Verde", "Canindé de São Francisco", "Maruim", "Neópolis", "Carmópolis"],
    "TO": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional", "Paraíso do Tocantins", "Colinas do Tocantins", "Guaraí", "Araguatins", "Tocantinópolis", "Miracema do Tocantins", "Dianópolis", "Formoso do Araguaia", "Taguatinga", "Augustinópolis", "Pedro Afonso", "Lagoa da Confusão", "Xambioá", "Natividade", "Paranã"]
}

@st.cache_data(ttl=86400, show_spinner=False)
def carregar_municipios(sigla_uf):
    # 1. Tenta carregar a lista completa oficial do IBGE (100% de todos os municípios do estado)
    try:
        url_ibge = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{sigla_uf}/municipios"
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url_ibge, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            if dados and isinstance(dados, list):
                nomes = [m['nome'] for m in dados if isinstance(m, dict) and 'nome' in m]
                if nomes and len(nomes) > 5:
                    return sorted(list(set(nomes)))
    except Exception:
        pass

    # 2. Tenta alternativa BrasilAPI
    try:
        url_bapi = f"https://brasilapi.com.br/api/ibge/municipios/v1/{sigla_uf}"
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url_bapi, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            if dados and isinstance(dados, list):
                nomes = [m['nome'] for m in dados if isinstance(m, dict) and 'nome' in m]
                if nomes and len(nomes) > 5:
                    return sorted(list(set(nomes)))
    except Exception:
        pass

    # 3. Base local curada garantida para todos os 27 estados
    if sigla_uf in CIDADES_BASE_POR_UF:
        return sorted(list(set(CIDADES_BASE_POR_UF[sigla_uf])))

    capital_padrao = CAPITAIS_BR.get(sigla_uf, "Capital")
    return [capital_padrao]

@st.cache_data(ttl=86400, show_spinner=False)
def obter_geolocalizacao_segura(cidade_str, sigla_uf=""):
    nome_puro = cidade_str.split(",")[0].strip().lower()
    capitais_nomes = {
        "são paulo": "SP", "sao paulo": "SP", "rio de janeiro": "RJ", "belo horizonte": "MG",
        "salvador": "BA", "curitiba": "PR", "porto alegre": "RS", "recife": "PE",
        "fortaleza": "CE", "belém": "PA", "belem": "PA", "rio branco": "AC",
        "macapá": "AP", "macapa": "AP", "boa vista": "RR", "florianópolis": "SC",
        "goiânia": "GO", "goiania": "GO", "são luís": "MA", "sao luis": "MA",
        "manaus": "AM", "vitória": "ES", "vitoria": "ES", "joão pessoa": "PB",
        "joao pessoa": "PB", "natal": "RN", "cuiabá": "MT", "cuiaba": "MT",
        "maceió": "AL", "maceio": "AL", "teresina": "PI", "brasília": "DF",
        "brasilia": "DF", "campo grande": "MS", "aracaju": "SE", "porto velho": "RO", "palmas": "TO"
    }
    if nome_puro in capitais_nomes:
        uf_ref = capitais_nomes[nome_puro]
        if uf_ref in COODS_CAPITAIS:
            lat, lng, tz = COODS_CAPITAIS[uf_ref]
            return float(lat), float(lng), tz

    try:
        geo = Nominatim(user_agent="astrologia_consciente_douglas_v7", timeout=12)
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

# ==================== CARREGAMENTO DA FONTE DEJAVU ====================
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

# ==================== CARDS DINÂMICOS NO PDF ====================
def calcular_altura_necessaria(items, char_width=44, line_spacing=10.0, item_spacing=5.0):
    total_linhas = 0
    for it in items:
        linhas = textwrap.wrap(it, width=char_width)
        total_linhas += max(len(linhas), 1)
    return 10.0 + 18.0 + (total_linhas * line_spacing) + (len(items) * item_spacing) + 8.0

def desenhar_card_dinamico(c, x, y_top, width, title, items, font_name, font_bold_name,
                           bg_color, border_color, title_color, bullet_color,
                           char_width=44, font_size=7.8, line_spacing=10.0, item_spacing=5.0, force_height=None):
    wrapped_items = []
    total_text_lines = 0
    for it in items:
        lines = textwrap.wrap(it, width=char_width)
        if not lines: lines = [""]
        wrapped_items.append(lines)
        total_text_lines += len(lines)

    title_height = 18.0
    padding_top = 10.0
    padding_bottom = 8.0

    calc_h = padding_top + title_height + (total_text_lines * line_spacing) + (len(items) * item_spacing) + padding_bottom
    card_height = max(calc_h, force_height) if force_height else calc_h
    y_bottom = y_top - card_height

    c.setFillColor(bg_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(1)
    c.roundRect(x, y_bottom, width, card_height, 6, fill=1, stroke=1)

    c.setFillColor(title_color)
    c.setFont(font_bold_name, 9)
    c.drawString(x + 12, y_top - padding_top - 9, seguro_texto(title))

    cur_y = y_top - padding_top - title_height
    for lines in wrapped_items:
        desenhar_marcador(c, x + 12, cur_y + 3, bullet_color, raio=2.2)
        c.setFont(font_name, font_size)
        c.setFillColor(HexColor('#1f1b29'))
        for line in lines:
            c.drawString(x + 20, cur_y, seguro_texto(line))
            cur_y -= line_spacing
        cur_y -= item_spacing

    return card_height, y_bottom

# ==================== PROJEÇÕES REAIS DOS PONTEIROS ====================
def calcular_projecoes_reais(dt_analise, dt_nasc, asc_b, planetas_natal, casas_p, FATORES):
    dias_base = (dt_analise - dt_nasc).days
    eventos_futuros = []
    angulos = [(0, "Conjunção", "neutra"), (60, "Sextil", "harmonica"), (90, "Quadratura", "tensao"), (120, "Trígono", "harmonica"), (180, "Oposição", "tensao")]

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

# ==================== SWOT DINÂMICO ====================
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

# ==================== BÚSSOLA CONSCIENTE DO DIA ====================
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
        gp, mp = dec_para_graus_minutos(deg_in_sign)
        label = f"{p_glifo}\n{gp}°{mp:02d}'"
        ax.text(p_rad, 0.98, label, ha='center', va='center', fontsize=7.5, color='#102a43', fontproperties=font_prop, zorder=5)

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)
    ax.spines['polar'].set_visible(False)

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=220, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    return buf.getvalue()

# ==================== GERAÇÃO DO PDF ADAPTATIVO ====================
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
    c.rect(0, h_page - 75, w_page, 75, fill=1, stroke=0)
    c.setFillColor(cor_azul_escuro)
    c.rect(0, h_page - 78, w_page, 3, fill=1, stroke=0)

    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_BOLD_NOME, 15)
    c.drawString(40, h_page - 34, seguro_texto("ASTROLOGIA CONSCIENTE"))
    c.setFont(FONTE_UNICODE_NOME, 9.5)
    c.drawString(40, h_page - 49, seguro_texto("Relatório Executivo: Matriz Natal, Mandala & A Dança dos Ponteiros"))
    c.setFont(FONTE_OBLIQUE_NOME, 8)
    c.drawString(40, h_page - 63, seguro_texto("Pesquisa e Metodologia: Douglas Rosa (@astrolodoug)"))

    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, h_page - 130, w_page - 80, 44, 5, fill=1, stroke=1)
    c.setFillColor(cor_topo)
    c.setFont(FONTE_BOLD_NOME, 9.5)
    c.drawString(50, h_page - 102, seguro_texto(f"Consulente: {nome_c} | Local: {cid_c}"))
    c.setFont(FONTE_UNICODE_NOME, 8.5)
    c.drawString(50, h_page - 117, seguro_texto(f"Data Base da Análise: {dt_ref} | Método: APRS e Trânsitos Ativos"))

    y_sec1_title = h_page - 146
    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_sec1_title, seguro_texto("1. Síntese da Personalidade & Mandala Astrológica"))
    c.setStrokeColor(cor_azul_escuro)
    c.setLineWidth(1)
    c.line(40, y_sec1_title - 4, w_page - 40, y_sec1_title - 4)

    y_sec1_box_top = y_sec1_title - 14
    h_sec1 = 205.0

    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, y_sec1_box_top - h_sec1, 275, h_sec1, 5, fill=1, stroke=1)
    c.setFillColor(cor_azul_escuro)
    c.setFont(FONTE_BOLD_NOME, 9)
    c.drawString(50, y_sec1_box_top - 18, seguro_texto("Eixo de Identidade & Temperamento:"))

    itens_triade = [
        f"Sol Natal: {triade_info['sol']}",
        f"Lua Natal: {triade_info['lua']}",
        f"Ascendente: {triade_info['asc']}",
        f"Elemento Predominante: {swot_data['elemento_dominante']}"
    ]
    y_tr = y_sec1_box_top - 35
    for it in itens_triade:
        desenhar_marcador(c, 52, y_tr + 3, cor_azul_escuro)
        c.setFont(FONTE_UNICODE_NOME, 8.5)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(60, y_tr, seguro_texto(it))
        y_tr -= 15

    c.setFillColor(cor_azul_escuro)
    c.setFont(FONTE_BOLD_NOME, 8.5)
    c.drawString(50, y_tr - 5, seguro_texto("Área de Maior Vocação & Potencial:"))
    c.setFont(FONTE_OBLIQUE_NOME, 8)
    c.setFillColor(HexColor('#2b263b'))
    c.drawString(50, y_tr - 18, seguro_texto(f"Setor Focal: {pot_texto['titulo']}"))

    linhas_pot = textwrap.wrap(pot_texto['descricao'], width=46)
    y_pt = y_tr - 30
    for lp in linhas_pot:
        c.drawString(50, y_pt, seguro_texto(lp))
        y_pt -= 10.5

    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(cor_borda)
    c.roundRect(330, y_sec1_box_top - h_sec1, 225, h_sec1, 5, fill=1, stroke=1)
    try:
        png_mandala = gerar_mandala_astrologica_png(planetas_pos, cuspides_pos, asc_grau)
        c.drawImage(ImageReader(BytesIO(png_mandala)), 333, y_sec1_box_top - h_sec1 + 3, width=219, height=199, mask='auto')
    except Exception:
        c.setFillColor(cor_azul_escuro)
        c.setFont(FONTE_BOLD_NOME, 8.5)
        c.drawCentredString(442.5, y_sec1_box_top - (h_sec1 / 2), seguro_texto("Mandala Astrológica Natal"))

    y_sec2_title = y_sec1_box_top - h_sec1 - 16
    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_sec2_title, seguro_texto("2. Análise Comportamental: Forças e Fraquezas Natais"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_sec2_title - 4, w_page - 40, y_sec2_title - 4)

    y_sec2_top = y_sec2_title - 14
    w_card = (w_page - 80 - 15) / 2

    h_f_req = calcular_altura_necessaria(swot_data['forcas'], char_width=44, line_spacing=10.0, item_spacing=5.0)
    h_fr_req = calcular_altura_necessaria(swot_data['fraquezas'], char_width=44, line_spacing=10.0, item_spacing=5.0)
    h_swot1 = max(h_f_req, h_fr_req)

    _, y_bot_sec2 = desenhar_card_dinamico(
        c, 40, y_sec2_top, w_card, "FORÇAS (Potenciais Inatos):", swot_data['forcas'],
        FONTE_UNICODE_NOME, FONTE_BOLD_NOME,
        HexColor('#f1f8e9'), HexColor('#1b5e20'), HexColor('#1b5e20'), HexColor('#1b5e20'),
        char_width=44, font_size=7.8, line_spacing=10.0, item_spacing=5.0, force_height=h_swot1
    )

    desenhar_card_dinamico(
        c, 40 + w_card + 15, y_sec2_top, w_card, "FRAQUEZAS (Zonas de Atenção):", swot_data['fraquezas'],
        FONTE_UNICODE_NOME, FONTE_BOLD_NOME,
        HexColor('#ffebee'), HexColor('#b71c1c'), HexColor('#b71c1c'), HexColor('#b71c1c'),
        char_width=44, font_size=7.8, line_spacing=10.0, item_spacing=5.0, force_height=h_swot1
    )

    y_sec3_title = y_bot_sec2 - 15
    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_sec3_title, seguro_texto("3. Posicionamento Atual dos 9 Ponteiros"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_sec3_title - 4, w_page - 40, y_sec3_title - 4)

    y_p_left = y_sec3_title - 16
    col1_items = tab_pont_raw[:5]
    for it in col1_items:
        desenhar_marcador(c, 44, y_p_left + 3, cor_azul_escuro, raio=2.0)
        c.setFont(FONTE_UNICODE_NOME, 7.8)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(52, y_p_left, seguro_texto(f"{it['Ponteiro']}: {it['Pos']} | {it['Reg']}"))
        y_p_left -= 12.5

    y_p_right = y_sec3_title - 16
    col2_items = tab_pont_raw[5:9]
    for it in col2_items:
        desenhar_marcador(c, 310, y_p_right + 3, cor_azul_escuro, raio=2.0)
        c.setFont(FONTE_UNICODE_NOME, 7.8)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(318, y_p_right, seguro_texto(f"{it['Ponteiro']}: {it['Pos']} | {it['Reg']}"))
        y_p_right -= 12.5

    c.setStrokeColor(cor_borda)
    c.line(40, 36, w_page - 40, 36)
    c.setFont(FONTE_UNICODE_NOME, 7.5)
    c.setFillColor(HexColor('#555555'))
    c.drawString(40, 24, seguro_texto("Astrologia Consciente | Douglas Rosa (@astrolodoug) - WhatsApp: (11) 97711-7024"))
    c.drawRightString(w_page - 40, 24, seguro_texto("Página 1 de 2"))

    c.showPage()

    # ========================== PÁGINA 2 ==========================
    c.setFillColor(cor_topo)
    c.rect(0, h_page - 48, w_page, 48, fill=1, stroke=0)
    c.setFillColor(cor_azul_escuro)
    c.rect(0, h_page - 51, w_page, 3, fill=1, stroke=0)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_BOLD_NOME, 10.5)
    c.drawString(40, h_page - 30, seguro_texto("CRONOGRAMA PREDITIVO: OPORTUNIDADES, AMEAÇAS E DIRECIONAMENTO"))

    y_sec4_title = h_page - 72
    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_sec4_title, seguro_texto("4. Matriz Preditiva: Oportunidades & Ameaças dos Próximos 12 Meses"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_sec4_title - 4, w_page - 40, y_sec4_title - 4)

    y_sec4_top = y_sec4_title - 14

    h_op_req = calcular_altura_necessaria(swot_data['oportunidades'], char_width=44, line_spacing=10.0, item_spacing=5.0)
    h_am_req = calcular_altura_necessaria(swot_data['ameacas'], char_width=44, line_spacing=10.0, item_spacing=5.0)
    h_swot2 = max(h_op_req, h_am_req)

    _, y_bot_sec4 = desenhar_card_dinamico(
        c, 40, y_sec4_top, w_card, "OPORTUNIDADES (Janelas de Expansão):", swot_data['oportunidades'],
        FONTE_UNICODE_NOME, FONTE_BOLD_NOME,
        HexColor('#f1f8e9'), HexColor('#1b5e20'), HexColor('#1b5e20'), HexColor('#1b5e20'),
        char_width=44, font_size=7.8, line_spacing=10.0, item_spacing=5.0, force_height=h_swot2
    )

    desenhar_card_dinamico(
        c, 40 + w_card + 15, y_sec4_top, w_card, "AMEAÇAS (Gatilhos de Rigor & Atenção):", swot_data['ameacas'],
        FONTE_UNICODE_NOME, FONTE_BOLD_NOME,
        HexColor('#fff8e1'), HexColor('#f57c00'), HexColor('#e65100'), HexColor('#e65100'),
        char_width=44, font_size=7.8, line_spacing=10.0, item_spacing=5.0, force_height=h_swot2
    )

    y_sec5_title = y_bot_sec4 - 16
    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_sec5_title, seguro_texto("5. Cronograma dos 9 Ponteiros & Gatilhos no Tempo (12 Meses)"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_sec5_title - 4, w_page - 40, y_sec5_title - 4)

    y_pr = y_sec5_title - 16
    for p in tab_proj_raw[:7]:
        desenhar_marcador(c, 44, y_pr + 3, cor_azul_escuro, raio=2.0)
        c.setFont(FONTE_UNICODE_NOME, 8)
        c.setFillColor(HexColor('#1f1b29'))
        c.drawString(54, y_pr, seguro_texto(f"{p['Data']}: {p['Ponteiro']} em {p['Aspecto']} ({p['Regência']})"))
        y_pr -= 14

    y_sec6_title = y_pr - 8
    c.setFont(FONTE_BOLD_NOME, 11)
    c.setFillColor(cor_azul_escuro)
    c.drawString(40, y_sec6_title, seguro_texto("6. Guia Didático & Dedicatória Oficial"))
    c.setStrokeColor(cor_azul_escuro)
    c.line(40, y_sec6_title - 4, w_page - 40, y_sec6_title - 4)

    y_card = y_sec6_title - 130
    c.setFillColor(cor_topo)
    c.roundRect(40, y_card, w_page - 80, 116, 6, fill=1, stroke=0)

    c.setFillColor(HexColor('#64b5f6'))
    c.setFont(FONTE_BOLD_NOME, 9.5)
    c.drawString(55, y_card + 94, seguro_texto("Uma mensagem de Douglas Rosa (@astrolodoug) para você:"))
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_OBLIQUE_NOME, 8)
    c.drawString(55, y_card + 78, seguro_texto('"O mapa astral não é uma sentença estática: é uma partitura rítmica viva.'))
    c.drawString(55, y_card + 65, seguro_texto('A Dança dos Ponteiros (APRS) revela o momento exato em que cada tema'))
    c.drawString(55, y_card + 52, seguro_texto('é convocado a amadurecer ou expandir. Use essas datas como coordenadas de ação."'))

    c.setFillColor(HexColor('#64b5f6'))
    c.setFont(FONTE_BOLD_NOME, 8.5)
    c.drawString(55, y_card + 32, seguro_texto("Atendimentos, Formações e Estudos:"))
    c.setFillColor(HexColor('#ffffff'))
    c.setFont(FONTE_UNICODE_NOME, 8)
    c.drawString(55, y_card + 18, seguro_texto("Instagram: @astrolodoug  |  WhatsApp: +55 (11) 97711-7024  |  YouTube: @astrolodoug"))

    c.setStrokeColor(cor_borda)
    c.line(40, 36, w_page - 40, 36)
    c.setFont(FONTE_UNICODE_NOME, 7.5)
    c.setFillColor(HexColor('#555555'))
    c.drawString(40, 24, seguro_texto("Astrologia Consciente | Todos os direitos reservados - @astrolodoug"))
    c.drawRightString(w_page - 40, 24, seguro_texto("Página 2 de 2"))

    c.save()
    buf.seek(0)
    return buf.getvalue()

# ==================== INTERFACE WEB ====================
if not st.session_state.mapa_gerado:
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
origem_tipo = st.sidebar.radio("Local de Origem:", ["Brasil (Lista de Municípios)", "Digitar Livremente (Brasil ou Exterior)"], index=0)

if origem_tipo == "Brasil (Lista de Municípios)":
    uf_escolhida = st.sidebar.selectbox("1. Escolha o Estado (UF):", ESTADOS_BR, index=24) # Padrão SP
    sigla_uf = uf_escolhida.split(" - ")[0]
    lista_cidades_uf = carregar_municipios(sigla_uf)
    total_cid = len(lista_cidades_uf)

    idx_padrao = 0
    if sigla_uf in CAPITAIS_BR and CAPITAIS_BR[sigla_uf] in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index(CAPITAIS_BR[sigla_uf])

    mun_escolhido = st.sidebar.selectbox(f"2. Município de {sigla_uf} ({total_cid} disponíveis):", options=lista_cidades_uf, index=idx_padrao, key=f"mun_{sigla_uf}")
    cidade = f"{mun_escolhido}, {sigla_uf}, Brasil"
else:
    cidade = st.sidebar.text_input("Digite Cidade, Estado e País:", value="São Paulo, SP, Brasil")
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
    st.rerun()

if st.session_state.mapa_gerado:
    st.sidebar.markdown("---")
    st.sidebar.success("✅ Mapa e Previsões em Exibição!")
    if st.sidebar.button("👁️ Fechar Painel e Ver Mapa", use_container_width=True):
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📲 Conecte-se com Douglas Rosa")
st.sidebar.link_button("💬 Conversar no WhatsApp", "https://wa.me/5511977117024", use_container_width=True)
st.sidebar.link_button("📸 Seguir no Instagram", "https://instagram.com/astrolodoug?dlrf=MWMyd2ZsendvemtnMQ%3D%3D", use_container_width=True)
st.sidebar.link_button("▶️ Acessar Canal no YouTube", "https://youtube.com/@astrolodoug?si=YimzRQs7yL1jJMSO", use_container_width=True)

if st.session_state.mapa_gerado:
    st.components.v1.html("""
    <script>
    function autoFecharSidebarMobile() {
        try {
            const pDoc = window.parent.document;
            if (!pDoc) return;
            const isMobile = window.parent.innerWidth <= 992;
            const collapseBtn = pDoc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                pDoc.querySelector('[data-testid="stSidebar"] button[kind="header"]') ||
                                pDoc.querySelector('button[aria-label="Close sidebar"]') ||
                                pDoc.querySelector('button[aria-label="Fechar barra lateral"]') ||
                                pDoc.querySelector('[data-testid="stSidebarCollapseButton"]');
            const backdrop = pDoc.querySelector('[data-testid="stSidebarBackdrop"]');
            if (isMobile) {
                if (backdrop && window.getComputedStyle(backdrop).display !== 'none') {
                    backdrop.click();
                } else if (collapseBtn) {
                    collapseBtn.click();
                }
            }
        } catch(err) {}
    }
    autoFecharSidebarMobile();
    setTimeout(autoFecharSidebarMobile, 150);
    setTimeout(autoFecharSidebarMobile, 450);
    </script>
    """, height=0)

    c_top_info, c_top_btn = st.columns([3, 1])
    with c_top_info:
        st.success(f"✅ **Mapa Ativo:** {nome} ({cidade}) | Data base: {DATA_ANALISE.strftime('%d/%m/%Y')}")
    with c_top_btn:
        if st.button("✏️ Alterar Dados", use_container_width=True):
            st.session_state.mapa_gerado = False
            st.rerun()

    with st.spinner("A processar cálculos astrológicos personalizados..."):
        try:
            lat, lng, tz_str = obter_geolocalizacao_segura(cidade, sigla_uf)

            sujeito = AstrologicalSubjectFactory.from_birth_data(name=nome, year=int(ano), month=int(mes), day=int(dia), hour=int(hora), minute=int(minuto), lat=float(lat), lng=float(lng), tz_str=tz_str)

            casas_ref = [("1ª Casa (Ascendente)", sujeito.first_house, 1), ("2ª Casa", sujeito.second_house, 2), ("3ª Casa", sujeito.third_house, 3), ("4ª Casa (Fundo do Céu)", sujeito.fourth_house, 4), ("5ª Casa", sujeito.fifth_house, 5), ("6ª Casa", sujeito.sixth_house, 6), ("7ª Casa (Descendente)", sujeito.seventh_house, 7), ("8ª Casa", sujeito.eighth_house, 8), ("9ª Casa", sujeito.ninth_house, 9), ("10ª Casa (Meio do Céu)", sujeito.tenth_house, 10), ("11ª Casa", sujeito.eleventh_house, 11), ("12ª Casa", sujeito.twelfth_house, 12)]
            cuspides_abs = {num: float(obter_dado(oc, 'abs_pos', 0.0)) for _, oc, num in casas_ref}
            casas_p = {p: [] for p in ["Sol","Lua","Mercúrio","Vênus","Marte","Júpiter","Saturno","Urano","Netuno","Plutão"]}

            tab_c = []
            for nc, oc, num in casas_ref:
                sn = nome_sig(obter_dado(oc, 'sign', ''))
                for r in REGENTES.get(sn, []):
                    if r in casas_p: casas_p[r].append(f"Casa {num}")
                pos_c = float(obter_dado(oc, 'position', 0.0))
                g_c, m_c = dec_para_graus_minutos(pos_c)
                tab_c.append({"Casa Astrológica": nc, "Cúspide": f"{g_c}° {m_c:02d}' {fmt_sig(sn)}", "Regentes": REG_TXT.get(sn, "Desconhecido")})

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
                g_p, m_p = dec_para_graus_minutos(pos_p)
                tab_pl.append({
                    "Planeta": pn,
                    "Posição": f"{g_p}° {m_p:02d}' {fmt_sig(obter_dado(po, 'sign', ''))}",
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

            eventos_todos = calcular_projecoes_reais(DATA_ANALISE, dt_nasc, asc_b, natal_para_aspeto, casas_p, FATORES)
            cronograma_12m = selecionar_cronograma_equilibrado(eventos_todos, 8)
            tab_fp = [{"Data": ev['data_str'], "Ponteiro": ev['ponteiro'], "Aspecto": ev['aspecto'], "Regência": ev['regencia']} for ev in cronograma_12m]

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

            sol_dict_info = {"signo": nome_sig(obter_dado(sujeito.sun, 'sign', '')), "casa": mapa_casas_planetas.get("Sol", 10)}
            lua_dict_info = {"signo": nome_sig(obter_dado(sujeito.moon, 'sign', '')), "casa": mapa_casas_planetas.get("Lua", 4)}
            asc_dict_info = {"signo": nome_sig(obter_dado(sujeito.first_house, 'sign', '')), "casa": 1}

            swot_data = gerar_swot_dinamico(sol_dict_info, lua_dict_info, asc_dict_info, elem_dominante, contagem_elem, eventos_todos)

            # BÚSSOLA CONSCIENTE DO DIA
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

                g_sol, m_sol = dec_para_graus_minutos(sol_pos)
                g_lua, m_lua = dec_para_graus_minutos(lua_pos)
                g_asc, m_asc = dec_para_graus_minutos(asc_pos)

                triade_resumo = {
                    "sol": f"{g_sol}° {m_sol:02d}' {GLIFOS.get(sol_sn, '')} {sol_sn} (Casa {mapa_casas_planetas.get('Sol',1)})",
                    "lua": f"{g_lua}° {m_lua:02d}' {GLIFOS.get(lua_sn, '')} {lua_sn} (Casa {mapa_casas_planetas.get('Lua',1)})",
                    "asc": f"{g_asc}° {m_asc:02d}' {GLIFOS.get(asc_sn, '')} {asc_sn} (1ª Casa)"
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
