import os, json, ssl, urllib.request, urllib.parse
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
    "PE - Pernambuco", "CE - Ceará", "PA - Pará", "SP - São Paulo", "RJ - Rio de Janeiro",
    "MG - Minas Gerais", "BA - Bahia", "PR - Paraná", "RS - Rio Grande do Sul",
    "SC - Santa Catarina", "GO - Goiás", "MA - Maranhão", "AM - Amazonas",
    "ES - Espírito Santo", "PB - Paraíba", "RN - Rio Grande do Norte", "MT - Mato Grosso",
    "AL - Alagoas", "PI - Piauí", "DF - Distrito Federal", "MS - Mato Grosso do Sul",
    "SE - Sergipe", "RO - Rondônia", "TO - Tocantins", "AC - Acre", "AP - Amapá", "RR - Roraima"
]

# PERNAMBUCO (185 CIDADES)
CIDADES_PE = sorted(list(set([
    "Abreu e Lima", "Afogados da Ingazeira", "Afrânio", "Agrestina", "Água Preta", "Águas Belas",
    "Alagoinha", "Aliança", "Altinho", "Amaraji", "Angelim", "Araçoiaba", "Araripina", "Arcoverde",
    "Barra de Guabiraba", "Barreiros", "Belém de Maria", "Belém do São Francisco", "Belo Jardim",
    "Betânia", "Bezerros", "Bodocó", "Bom Conselho", "Bom Jardim", "Bonito", "Brejão", "Brejinho",
    "Brejo da Madre de Deus", "Buenos Aires", "Buíque", "Cabo de Santo Agostinho", "Cabrobó",
    "Cachoeirinha", "Caetés", "Calçado", "Calumbi", "Camaragibe", "Camocim de São Félix",
    "Camutanga", "Canhotinho", "Capoeiras", "Carnaíba", "Carnaubeira da Penha", "Carpina",
    "Caruaru", "Casinhas", "Catende", "Cedro", "Chã de Alegria", "Chã Grande", "Condado",
    "Correntes", "Cortês", "Cumaru", "Cupira", "Custódia", "Dormentes", "Escada", "Exu",
    "Feira Nova", "Fernando de Noronha", "Ferreiros", "Flores", "Floresta", "Frei Miguelinho",
    "Gameleira", "Garanhuns", "Glória do Goitá", "Goiana", "Granito", "Gravatá", "Iati",
    "Ibimirim", "Ibirajuba", "Igarassu", "Iguaracy", "Inajá", "Ingazeira", "Ipojuca", "Ipubi",
    "Itacuruba", "Itaíba", "Ilha de Itamaracá", "Itambé", "Itapetim", "Itapissuma", "Itaquitinga",
    "Jaboatão dos Guararapes", "Jaqueira", "Jataúba", "Jatobá", "João Alfredo", "Joaquim Nabuco",
    "Jucati", "Jupi", "Jurema", "Lagoa do Carro", "Lagoa de Itaenga", "Lagoa do Ouro",
    "Lagoa dos Gatos", "Lagoa Grande", "Lajedo", "Limoeiro", "Macaparana", "Machados", "Manari",
    "Maraial", "Mirandiba", "Moreno", "Nazaré da Mata", "Olinda", "Orobó", "Orocó", "Ouricuri",
    "Palmares", "Palmeirina", "Panelas", "Paranatama", "Parnamirim", "Passira", "Paudalho",
    "Paulista", "Pedra", "Pesqueira", "Petrolândia", "Petrolina", "Poção", "Pombos", "Primavera",
    "Quipapá", "Quixaba", "Recife", "Riacho das Almas", "Ribeirão", "Rio Formoso", "Sairé",
    "Salgadinho", "Salgueiro", "Saloá", "Sanharó", "Santa Cruz", "Santa Cruz da Baixa Verde",
    "Santa Cruz do Capibaribe", "Santa Filomena", "Santa Maria da Boa Vista", "Santa Maria do Cambucá",
    "Santa Terezinha", "São Benedito do Sul", "São Bento do Una", "São Caitano", "São João",
    "São Joaquim do Monte", "São José da Coroa Grande", "São José do Belmonte", "São José do Egito",
    "São Lourenço da Mata", "São Vicente Férrer", "Serra Talhada", "Serrita", "Sertânia",
    "Sirinhaém", "Solidão", "Surubim", "Tabira", "Tacaimbó", "Tacaratu", "Tamandaré",
    "Taquaritinga do Norte", "Terezinha", "Terra Nova", "Timbaúba", "Toritama", "Tracunhaém",
    "Trindade", "Triunfo", "Tupanatinga", "Tuparetama", "Venturosa", "Verdejante",
    "Vertente do Lério", "Vertentes", "Vicência", "Vitória de Santo Antão", "Xexéu"
])))

# CEARÁ (184 CIDADES)
CIDADES_CE = sorted(list(set([
    "Abaiara", "Acarape", "Acaraú", "Acopiara", "Aiuaba", "Alcântaras", "Altaneira", "Alto Santo",
    "Amontada", "Antonina do Norte", "Apuiarés", "Aquiraz", "Aracati", "Aracoiaba", "Ararendá",
    "Araripe", "Aratuba", "Arneiroz", "Assaré", "Aurora", "Baixio", "Banabuiú", "Barbalha",
    "Barreira", "Barro", "Barroquinha", "Baturité", "Beberibe", "Bela Cruz", "Boa Viagem",
    "Brejo Santo", "Camocim", "Campos Sales", "Canindé", "Capistrano", "Caridade", "Cariré",
    "Caririaçu", "Cariús", "Carnaubal", "Cascavel", "Catarina", "Catunda", "Caucaia", "Cedro",
    "Chaval", "Choró", "Chorozinho", "Coreaú", "Crateús", "Crato", "Croatá", "Cruz",
    "Deputado Irapuan Pinheiro", "Ereré", "Eusébio", "Farias Brito", "Forquilha", "Fortaleza",
    "Fortim", "Frecheirinha", "General Sampaio", "Graça", "Granja", "Granjeiro", "Groaíras",
    "Guaiúba", "Guaraciaba do Norte", "Guaramiranga", "Hidrolândia", "Horizonte", "Ibaretama",
    "Ibiapina", "Ibicuitinga", "Icapuí", "Icó", "Iguatu", "Independência", "Ipaumirim", "Ipu",
    "Ipueiras", "Iracema", "Irauçuba", "Itaiçaba", "Itaitinga", "Itapajé", "Itapipoca", "Itapiúna",
    "Itarema", "Itatira", "Jaguaretama", "Jaguaribara", "Jaguaribe", "Jaguaruana", "Jardim",
    "Jati", "Jijoca de Jericoacoara", "Juazeiro do Norte", "Jucás", "Lavras da Mangabeira",
    "Limoeiro do Norte", "Madalena", "Maracanaú", "Maranguape", "Marco", "Martinópole", "Massapê",
    "Mauriti", "Meruoca", "Milagres", "Milhã", "Miraíma", "Missão Velha", "Mombaça",
    "Monsenhor Tabosa", "Morada Nova", "Moraújo", "Morrinhos", "Mucambo", "Mulungu", "Nova Olinda",
    "Nova Russas", "Novo Oriente", "Ocara", "Orós", "Pacajus", "Pacatuba", "Pacoti", "Pacujá",
    "Palhano", "Palmácia", "Paracuru", "Paraipaba", "Parambu", "Paramoti", "Pedra Branca",
    "Penaforte", "Pentecoste", "Pereiro", "Pindoretama", "Piquet Carneiro", "Pires Ferreira",
    "Poranga", "Porteiras", "Potengi", "Potiretama", "Quiterianópolis", "Quixadá", "Quixelô",
    "Quixeramobim", "Quixeré", "Redenção", "Reriutaba", "Russas", "Saboeiro", "Salitre",
    "Santa Quitéria", "Santana do Acaraú", "Santana do Cariri", "São Benedito",
    "São Gonçalo do Amarante", "São João do Jaguaribe", "São Luís do Curu", "Senador Pompeu",
    "Senador Sá", "Sobral", "Solonópole", "Tabuleiro do Norte", "Tamboril", "Tarrafas", "Tauá",
    "Tejuçuoca", "Tianguá", "Trairi", "Tururu", "Ubajara", "Umari", "Umirim", "Uruburetama",
    "Uruoca", "Varjota", "Várzea Alegre", "Viçosa do Ceará"
])))

# PARÁ (144 CIDADES)
CIDADES_PA = sorted(list(set([
    "Abaetetuba", "Abel Figueiredo", "Acará", "Afuá", "Água Azul do Norte", "Alenquer", "Almeirim",
    "Altamira", "Anajás", "Ananindeua", "Anapu", "Augusto Corrêa", "Aurora do Pará", "Aveiro",
    "Bagre", "Baião", "Bannach", "Barcarena", "Belém", "Belterra", "Benevides", "Bom Jesus do Tocantins",
    "Bonito", "Bragança", "Brasil Novo", "Brejo Grande do Araguaia", "Breu Branco", "Breves",
    "Bujaru", "Cachoeira do Arari", "Cachoeira do Piriá", "Cametá", "Canaã dos Carajás", "Capanema",
    "Capitão Poço", "Castanhal", "Chaves", "Colares", "Conceição do Araguaia", "Concórdia do Pará",
    "Cumaru do Norte", "Curionópolis", "Curralinho", "Curuá", "Curuçá", "Dom Eliseu",
    "Eldorado do Carajás", "Faro", "Floresta do Araguaia", "Garrafão do Norte", "Goianésia do Pará",
    "Gurupá", "Igarapé-Açu", "Igarapé-Miri", "Inhangapi", "Ipixuna do Pará", "Irituia", "Itaituba",
    "Itupiranga", "Jacareacanga", "Jacundá", "Juruti", "Limoeiro do Ajuru", "Mãe do Rio",
    "Magalhães Barata", "Marabá", "Maracanã", "Marapanim", "Marituba", "Medicilândia", "Melgaço",
    "Mocajuba", "Moju", "Mojuí dos Campos", "Monte Alegre", "Muaná", "Nova Esperança do Piriá",
    "Nova Ipixuna", "Nova Timboteua", "Novo Progresso", "Novo Repartimento", "Óbidos", "Oeiras do Pará",
    "Oriximiná", "Ourém", "Ourilândia do Norte", "Pacajá", "Palestina do Pará", "Paragominas",
    "Parauapebas", "Pau D'Arco", "Peixe-Boi", "Piçarra", "Placas", "Ponta de Pedras", "Portel",
    "Porto de Moz", "Prainha", "Primavera", "Quatipuru", "Redenção", "Rio Maria", "Rondon do Pará",
    "Rurópolis", "Salinópolis", "Salvaterra", "Santa Bárbara do Pará", "Santa Cruz do Arari",
    "Santa Isabel do Pará", "Santa Luzia do Pará", "Santa Maria das Barreiras", "Santa Maria do Pará",
    "Santana do Araguaia", "Santarém", "Santarém Novo", "Santo Antônio do Tauá",
    "São Caetano de Odivelas", "São Domingos do Araguaia", "São Domingos do Capim",
    "São Félix do Xingu", "São Francisco do Pará", "São Geraldo do Araguaia", "São João da Ponta",
    "São João de Pirabas", "São João do Araguaia", "São Miguel do Guamá", "São Sebastião da Boa Vista",
    "Sapucaia", "Senador José Porfírio", "Soure", "Tailândia", "Terra Alta", "Terra Santa",
    "Tomé-Açu", "Tracuateua", "Trairão", "Tucumã", "Tucuruí", "Ulianópolis", "Uruará", "Vigia",
    "Viseu", "Vitória do Xingu", "Xinguara"
])))

CIDADES_RS = sorted([
    "Aceguá", "Água Santa", "Agudo", "Ajuricaba", "Alecrim", "Alegrete", "Alegria",
    "Almirante Tamandaré do Sul", "Alpestre", "Alto Alegre", "Alto Feliz", "Alvorada",
    "Amaral Ferrador", "Ametista do Sul", "André da Rocha", "Anta Gorda", "Antônio Prado",
    "Arambaré", "Araricá", "Aratiba", "Arroio do Meio", "Arroio do Padre", "Arroio do Sal",
    "Arroio do Tigre", "Arroio dos Ratos", "Arroio Grande", "Arvorezinha", "Augusto Pestana",
    "Áurea", "Bagé", "Balneário Pinhal", "Barão", "Barão de Cotegipe", "Barão do Triunfo",
    "Barra do Guarita", "Barra do Quaraí", "Barra do Ribeiro", "Barra do Rio Azul",
    "Barra Funda", "Barracão", "Barros Cassal", "Benjamin Constant do Sul", "Bento Gonçalves",
    "Boa Vista das Missões", "Boa Vista do Buricá", "Boa Vista do Cadeado", "Boa Vista do Incra",
    "Boa Vista do Sul", "Bom Jesus", "Bom Princípio", "Bom Progresso", "Bom Retiro do Sul",
    "Boqueirão do Leão", "Bossoroca", "Bozano", "Braga", "Brochier", "Butiá", "Caçapava do Sul",
    "Cacequi", "Cachoeira do Sul", "Cachoeirinha", "Cacique Doble", "Caibaté", "Caiçara",
    "Camaquã", "Camargo", "Cambará do Sul", "Campestre da Serra", "Campina das Missões",
    "Campinas do Sul", "Campo Bom", "Campo Novo", "Campos Borges", "Candelária", "Cândido Godói",
    "Candiota", "Canela", "Canguçu", "Canoas", "Canudos do Vale", "Capão Bonito do Sul",
    "Capão da Canoa", "Capão do Cipó", "Capão do Leão", "Capela de Santana", "Capitão",
    "Capivari do Sul", "Caraá", "Carazinho", "Carlos Barbosa", "Carlos Gomes", "Casca",
    "Caseiros", "Catuípe", "Caxias do Sul", "Centenário", "Cerrito", "Cerro Branco",
    "Cerro Grande", "Cerro Grande do Sul", "Cerro Largo", "Chapada", "Charqueadas",
    "Charrua", "Chiapetta", "Chuí", "Chuvisca", "Cidreira", "Ciríaco", "Colinas",
    "Colorado", "Condor", "Constantina", "Coqueiro Baixo", "Coqueiros do Sul",
    "Coronel Barros", "Coronel Bicaco", "Coronel Pilar", "Cotiporã", "Coxilha", "Crissiumal",
    "Cristal", "Cristal do Sul", "Cruz Alta", "Cruzaltense", "Cruzeiro do Sul",
    "David Canabarro", "Derrubadas", "Dezesseis de Novembro", "Dilermando de Aguiar",
    "Dois Irmãos", "Dois Irmãos das Missões", "Dois Lajeados", "Dom Feliciano",
    "Dom Pedro de Alcântara", "Dom Pedrito", "Dona Francisca", "Doutor Maurício Cardoso",
    "Doutor Ricardo", "Eldorado do Sul", "Encantado", "Encruzilhada do Sul", "Engenho Velho",
    "Entre Rios do Sul", "Entre-Ijuís", "Erebango", "Erechim", "Ernestina", "Erval Grande",
    "Erval Seco", "Esmeralda", "Esperança do Sul", "Espumoso", "Estação", "Estância Velha",
    "Esteio", "Estrela", "Estrela Velha", "Eugênio de Castro", "Fagundes Varela", "Farroupilha",
    "Faxinal do Soturno", "Faxinalzinho", "Fazenda Vilanova", "Feliz", "Flores da Cunha",
    "Floriano Peixoto", "Fontoura Xavier", "Formigueiro", "Forquetinha", "Fortaleza dos Valos",
    "Frederico Westphalen", "Garibaldi", "Garruchos", "Gaurama", "General Câmara", "Gentil",
    "Getúlio Vargas", "Giruá", "Glorinha", "Gramado", "Gramado dos Loureiros", "Gramado Xavier",
    "Gravataí", "Guabiju", "Guaíba", "Guaporé", "Guarani das Missões", "Harmonia", "Herval",
    "Herveiras", "Horizontina", "Hulha Negra", "Humaitá", "Ibarama", "Ibiaçá", "Ibiraiaras",
    "Ibirapuitã", "Ibirubá", "Igrejinha", "Ijuí", "Ilópolis", "Imbé", "Imigrante",
    "Independência", "Inhacorá", "Ipê", "Ipiranga do Sul", "Iraí", "Itaara", "Itacurubi",
    "Itapuca", "Itaqui", "Itati", "Itatiba do Sul", "Ivorá", "Ivoti", "Jaboticaba",
    "Jacuizinho", "Jacutinga", "Jaguarão", "Jaguari", "Jaquirana", "Jari", "Jóia",
    "Júlio de Castilhos", "Lagoa Bonita do Sul", "Lagoa dos Três Cantos", "Lagoa Vermelha",
    "Lagoão", "Lajeado", "Lajeado do Bugre", "Lavras do Sul", "Liberato Salzano",
    "Lindolfo Collor", "Linha Nova", "Maçambará", "Machadinho", "Mampituba", "Manoel Viana",
    "Maquiné", "Maratá", "Marau", "Marcelino Ramos", "Mariana Pimentel", "Mariano Moro",
    "Marques de Souza", "Mata", "Mato Castelhano", "Mato Leitão", "Mato Queimado",
    "Maximiliano de Almeida", "Minas do Leão", "Miraguaí", "Montauri", "Monte Alegre dos Campos",
    "Monte Belo do Sul", "Montenegro", "Mormaço", "Morrinhos do Sul", "Morro Redondo",
    "Morro Reuter", "Mostardas", "Muçum", "Muitos Capões", "Muliterno", "Não-Me-Toque",
    "Nicolau Vergueiro", "Nonoai", "Nova Alvorada", "Nova Araçá", "Nova Bassano",
    "Nova Boa Vista", "Nova Bréscia", "Nova Candelária", "Nova Esperança do Sul", "Nova Hartz",
    "Nova Pádua", "Nova Palma", "Nova Petrópolis", "Nova Prata", "Nova Ramada",
    "Nova Roma do Sul", "Nova Santa Rita", "Novo Barreiro", "Novo Cabrais", "Novo Hamburgo",
    "Novo Machado", "Novo Tiradentes", "Novo Xingu", "Olívio", "Osório", "Paim Filho",
    "Palmares do Sul", "Palmeira das Missões", "Palmitinho", "Panambi", "Pantano Grande",
    "Paraí", "Paraíso do Sul", "Pareci Novo", "Parobé", "Passa Sete", "Passo do Sobrado",
    "Passo Fundo", "Paulo Bento", "Paverama", "Pedras Altas", "Pedro Osório", "Pejuçara",
    "Pelotas", "Picada Café", "Pinhal", "Pinhal da Serra", "Pinhal Grande",
    "Pinheirinho do Vale", "Pinheiro Machado", "Pinto Bandeira", "Piratini", "Planalto",
    "Poço das Antas", "Pontão", "Ponte Preta", "Portão", "Porto Alegre", "Porto Lucena",
    "Porto Mauá", "Porto Vera Cruz", "Porto Xavier", "Pouso Novo", "Presidente Lucena",
    "Progresso", "Protásio Alves", "Quaraí", "Quatro Irmãos", "Quevedos", "Quinze de Novembro",
    "Redentora", "Relvado", "Restinga Sêca", "Rio dos Índios", "Rio Grande", "Rio Pardo",
    "Riozinho", "Roca Sales", "Rodeio Bonito", "Rolador", "Rolante", "Ronda Alta", "Rondinha",
    "Roque Gonzales", "Rosário do Sul", "Sagrada Família", "Saldanha Marinho", "Salto do Jacuí",
    "Salvador das Missões", "Salvador do Sul", "Sananduva", "Santa Bárbara do Sul",
    "Santa Cecília do Sul", "Santa Clara do Sul", "Santa Cruz do Sul", "Santa Margarida do Sul",
    "Santa Maria", "Santa Maria do Herval", "Santa Rosa", "Santa Tereza", "Santa Vitória do Palmar",
    "Santana da Boa Vista", "Sant'Ana do Livramento", "Santiago", "Santo Ângelo",
    "Santo Antônio da Patrulha", "Santo Antônio das Missões", "Santo Antônio do Palma",
    "Santo Antônio do Planalto", "Santo Augusto", "Santo Cristo", "Santo Expedito do Sul",
    "São Borja", "São Domingos do Sul", "São Francisco de Assis", "São Francisco de Paula",
    "São Gabriel", "São Jerônimo", "São João da Urtiga", "São João do Polêsine", "São Jorge",
    "São José das Missões", "São José do Herval", "São José do Hortêncio", "São José do Inhacorá",
    "São José do Norte", "São José do Ouro", "São José do Sul", "São José dos Ausentes",
    "São Leopoldo", "São Lourenço do Sul", "São Luiz Gonzaga", "São Marcos", "São Martinho",
    "São Martinho da Serra", "São Miguel das Missões", "São Nicolau", "São Paulo das Missões",
    "São Pedro da Serra", "São Pedro das Missões", "São Pedro do Butiá", "São Pedro do Sul",
    "São Sebastião do Caí", "São Sepé", "São Valentim", "São Valentim do Sul",
    "São Valério do Sul", "São Vendelino", "São Vicente do Sul", "Sapiranga", "Sapucaia do Sul",
    "Sarandi", "Seberi", "Sede Nova", "Segredo", "Selbach", "Senador Salgado Filho",
    "Sentinela do Sul", "Serafina Corrêa", "Sério", "Sertão", "Sertão Santana",
    "Sete de Setembro", "Severiano de Almeida", "Silveira Martins", "Sinimbu", "Sobradinho",
    "Soledade", "Tabaí", "Tapejara", "Tapera", "Tapes", "Taquara", "Taquari", "Taquaruçu do Sul",
    "Tavares", "Tenente Portela", "Terra de Areia", "Teutônia", "Tio Hugo", "Tiradentes do Sul",
    "Toropi", "Torres", "Tramandaí", "Travesseiro", "Três Arroios", "Três Cachoeiras",
    "Três Coroas", "Três de Maio", "Três Forquilhas", "Três Palmeiras", "Três Passos",
    "Trindade do Sul", "Triunfo", "Tucunduva", "Tunas", "Tupanci do Sul", "Tupanciretã",
    "Tupandi", "Tuparendi", "Turuçu", "Ubiretama", "União da Serra", "Uruguaiana", "Vacaria",
    "Vale do Sol", "Vale Real", "Vale Verde", "Vanini", "Venâncio Aires", "Vera Cruz",
    "Veranópolis", "Vespasiano Corrêa", "Viadutos", "Viamão", "Vicente Dutra", "Victor Graeff",
    "Vila Flores", "Vila Lângaro", "Vila Maria", "Vila Nova do Sul", "Vista Alegre",
    "Vista Alegre do Prata", "Vista Gaúcha", "Vitória das Missões", "Westfália", "Xangri-lá"
])

CIDADES_PR = sorted([
    "Abatiá", "Adrianópolis", "Agudos do Sul", "Almirante Tamandaré", "Altamira do Paraná",
    "Alto Paraíso", "Alto Paraná", "Alto Piquiri", "Altônia", "Alvorada do Sul", "Amaporã",
    "Ampére", "Anahy", "Andirá", "Ângulo", "Antonina", "Antônio Olinto", "Apucarana",
    "Arapongas", "Arapoti", "Arapuã", "Araruna", "Araucária", "Ariranha do Ivaí", "Assaí",
    "Assis Chateaubriand", "Astorga", "Atalaia", "Balsa Nova", "Bandeirantes", "Barbosa Ferraz",
    "Barra do Jacaré", "Barracão", "Bela Vista da Caroba", "Bela Vista do Paraíso", "Bituruna",
    "Boa Esperança", "Boa Esperança do Iguaçu", "Boa Ventura de São Roque", "Boa Vista da Aparecida",
    "Bocaiúva do Sul", "Bom Jesus do Sul", "Bom Sucesso", "Bom Sucesso do Sul", "Borrazópolis",
    "Braganey", "Brasilândia do Sul", "Cafeara", "Cafelândia", "Cafezal do Sul", "Califórnia",
    "Cambará", "Cambé", "Cambira", "Campina da Lagoa", "Campina do Simão", "Campina Grande do Sul",
    "Campo Bonito", "Campo do Tenente", "Campo Largo", "Campo Magro", "Campo Mourão",
    "Cândido de Abreu", "Candói", "Cantagalo", "Capanema", "Capitão Leônidas Marques",
    "Carambeí", "Carlópolis", "Cascavel", "Castro", "Catanduvas", "Centenário do Sul",
    "Cerro Azul", "Céu Azul", "Chopinzinho", "Cianorte", "Cidade Gaúcha", "Clevelândia",
    "Colombo", "Colorado", "Congonhinhas", "Conselheiro Mairinck", "Contenda", "Corbélia",
    "Cornélio Procópio", "Coronel Domingos Soares", "Coronel Vivida", "Corumbataí do Sul",
    "Cruz Machado", "Cruzeiro do Iguaçu", "Cruzeiro do Oeste", "Cruzeiro do Sul", "Cruzmaltina",
    "Curitiba", "Curiúva", "Diamante D'Oeste", "Diamante do Norte", "Diamante do Sul",
    "Dois Vizinhos", "Douradina", "Doutor Camargo", "Doutor Ulysses", "Enéas Marques",
    "Engenheiro Beltrão", "Entre Rios do Oeste", "Esperança Nova", "Espigão Alto do Iguaçu",
    "Farol", "Faxinal", "Fazenda Rio Grande", "Fênix", "Fernandes Pinheiro", "Figueira",
    "Flor da Serra do Sul", "Floraí", "Floresta", "Florestópolis", "Flórida", "Formosa do Oeste",
    "Foz do Iguaçu", "Foz do Jordão", "Francisco Alves", "Francisco Beltrão", "General Carneiro",
    "Godoy Moreira", "Goioerê", "Goioxim", "Grandes Rios", "Guaíra", "Guairaçá", "Guamiranga",
    "Guapirama", "Guaporema", "Guaraci", "Guaraniaçu", "Guarapuava", "Guaraqueçaba", "Guaratuba",
    "Honório Serpa", "Ibaiti", "Ibema", "Ibiporã", "Icaraíma", "Iguaraçu", "Iguatu", "Imbaú",
    "Imbituva", "Inácio Martins", "Inajá", "Indianópolis", "Ipiranga", "Iporã", "Iracema do Oeste",
    "Irati", "Iretama", "Itaguajé", "Itaipulândia", "Itambaracá", "Itambé", "Itapejara d'Oeste",
    "Itaperuçu", "Itaúna do Sul", "Ivaí", "Ivaiporã", "Ivaté", "Ivatuba", "Jaboti", "Jacarezinho",
    "Jaguapitã", "Jaguariaíva", "Jandaia do Sul", "Janiópolis", "Japira", "Japurá", "Jardim Alegre",
    "Jardim Olinda", "Jataizinho", "Jesuítas", "Joaquim Távora", "Jundiaí do Sul", "Juranda",
    "Jussara", "Kaloré", "Lapa", "Laranjal", "Laranjeiras do Sul", "Leópolis", "Lidianópolis",
    "Lindoeste", "Loanda", "Lobato", "Londrina", "Luiziana", "Lunardelli", "Lupionópolis",
    "Mallet", "Mamborê", "Mandaguaçu", "Mandaguari", "Mandirituba", "Manfrinópolis", "Mangueirinha",
    "Manoel Ribas", "Marechal Cândido Rondon", "Marialva", "Marilândia do Sul", "Marilena",
    "Mariluz", "Maringá", "Mariópolis", "Maripá", "Marmeleiro", "Marquinho", "Marumbi",
    "Matelândia", "Matinhos", "Mato Rico", "Mauá da Serra", "Medianeira", "Mercedes", "Mirador",
    "Miraselva", "Missal", "Moreira Sales", "Morretes", "Munhoz de Melo", "Nossa Senhora das Graças",
    "Nova Aliança do Ivaí", "Nova América da Colina", "Nova Aurora", "Nova Cantu", "Nova Esperança",
    "Nova Esperança do Sudoeste", "Nova Fátima", "Nova Laranjeiras", "Nova Londrina", "Nova Olímpia",
    "Nova Prata do Iguaçu", "Nova Santa Bárbara", "Nova Santa Rosa", "Nova Tebas", "Novo Itacolomi",
    "Ortigueira", "Ourizona", "Ouro Verde do Oeste", "Paiçandu", "Palmas", "Palmeira", "Palmital",
    "Palotina", "Paraíso do Norte", "Paranacity", "Paranaguá", "Paranapoema", "Paranavaí",
    "Pato Bragado", "Pato Branco", "Paula Freitas", "Paulo Frontin", "Peabiru", "Perobal",
    "Pérola", "Pérola d'Oeste", "Piên", "Pinhais", "Pinhal de São Bento", "Pinhalão", "Pinhão",
    "Piraí do Sul", "Piraquara", "Pitanga", "Pitangueiras", "Planaltina do Paraná", "Planalto",
    "Ponta Grossa", "Pontal do Paraná", "Porecatu", "Porto Amazonas", "Porto Barreiro", "Porto Rico",
    "Porto Vitória", "Prado Ferreira", "Pranchita", "Presidente Castelo Branco", "Primeiro de Maio",
    "Prudentópolis", "Quarto Centenário", "Quatiguá", "Quatro Barras", "Quatro Pontes",
    "Quedas do Iguaçu", "Querência do Norte", "Quinta do Sol", "Quitandinha", "Ramilândia",
    "Rancho Alegre", "Rancho Alegre D'Oeste", "Realeza", "Rebouças", "Renascença", "Reserva",
    "Reserva do Iguaçu", "Ribeirão Claro", "Ribeirão do Pinhal", "Rio Azul", "Rio Bom",
    "Rio Bonito do Iguaçu", "Rio Branco do Ivaí", "Rio Branco do Sul", "Rio Negro", "Rolândia",
    "Roncador", "Rondon", "Rosário do Ivaí", "Sabáudia", "Salgado Filho", "Salto do Itararé",
    "Salto do Lontra", "Santa Amélia", "Santa Cecília do Pavão", "Santa Cruz de Monte Castelo",
    "Santa Fé", "Santa Helena", "Santa Inês", "Santa Isabel do Ivaí", "Santa Izabel do Oeste",
    "Santa Lúcia", "Santa Maria do Oeste", "Santa Mariana", "Santa Mônica", "Santa Tereza do Oeste",
    "Santa Terezinha de Itaipu", "Santana do Itararé", "Santo Antônio da Platina",
    "Santo Antônio do Caiuá", "Santo Antônio do Paraíso", "Santo Antônio do Sudoeste",
    "Santo Inácio", "São Carlos do Ivaí", "São Jerônimo da Serra", "São João", "São João do Caiuá",
    "São João do Ivaí", "São João do Triunfo", "São Jorge d'Oeste", "São Jorge do Ivaí",
    "São Jorge do Patrocínio", "São José da Boa Vista", "São José das Palmeiras",
    "São José dos Pinhais", "São Manoel do Paraná", "São Mateus do Sul", "São Miguel do Iguaçu",
    "São Pedro do Iguaçu", "São Pedro do Ivaí", "São Pedro do Paraná", "São Sebastião da Amoreira",
    "São Tomé", "Sapopema", "Sarandi", "Saudade do Iguaçu", "Sengés", "Serranópolis do Iguaçu",
    "Sertaneja", "Sertanópolis", "Siqueira Campos", "Sulina", "Tamarana", "Tamboara", "Tapejara",
    "Tapira", "Teixeira Soares", "Telêmaco Borba", "Tibagi", "Tijucas do Sul", "Toledo", "Tomazina",
    "Três Barras do Paraná", "Tunas do Paraná", "Tuneiras do Oeste", "Tupãssi", "Turvo", "Ubiratã",
    "Umuarama", "União da Vitória", "Uniflor", "Uraí", "Ventania", "Vera Cruz do Oeste", "Verê",
    "Virmond", "Vitorino", "Wenceslau Braz", "Xambrê"
])

CIDADES_BA = sorted([
    "Abaíra", "Abaré", "Acajutiba", "Adustina", "Água Fria", "Aiquara", "Alagoinhas", "Alcobaça",
    "Almadina", "Amargosa", "Amélia Rodrigues", "América Dourada", "Anagé", "Andaraí", "Andorinha",
    "Angical", "Anguera", "Antas", "Antônio Cardoso", "Antônio Gonçalves", "Aporá", "Apuarema",
    "Araçás", "Aracatu", "Araci", "Aramari", "Arataca", "Aratuípe", "Aurelino Leal", "Baianópolis",
    "Baixa Grande", "Banzaê", "Barra", "Barra da Estiva", "Barra do Choça", "Barra do Mendes",
    "Barra do Rocha", "Barreiras", "Barro Alto", "Barro Preto", "Barrocas", "Belmonte", "Belo Campo",
    "Biritinga", "Boa Nova", "Boa Vista do Tupim", "Bom Jesus da Lapa", "Bom Jesus da Serra",
    "Boninal", "Bonito", "Boquira", "Botuporã", "Brejões", "Brejolândia", "Brotas de Macaúbas",
    "Brumado", "Buerarema", "Buritirama", "Caatiba", "Cabaceiras do Paraguaçu", "Cachoeira",
    "Caculé", "Caém", "Caetanos", "Caetité", "Cafarnaum", "Cairu", "Caldeirão Grande", "Camacan",
    "Camaçari", "Camamu", "Campo Alegre de Lourdes", "Campo Formoso", "Canápolis", "Canarana",
    "Canavieiras", "Candeal", "Candeias", "Candiba", "Cândido Sales", "Cansanção", "Canudos",
    "Capela do Alto Alegre", "Capim Grosso", "Caraíbas", "Caravelas", "Cardeal da Silva",
    "Carinhanha", "Casa Nova", "Castro Alves", "Catolândia", "Catu", "Caturama", "Central",
    "Chorrochó", "Cícero Dantas", "Cipó", "Coaraci", "Cocos", "Conceição da Feira",
    "Conceição do Almeida", "Conceição do Coité", "Conceição do Jacuípe", "Conde", "Condeúba",
    "Contendas do Sincorá", "Coração de Maria", "Cordeiros", "Coribe", "Coronel João Sá",
    "Correntina", "Cotegipe", "Cravolândia", "Crisópolis", "Cristópolis", "Cruz das Almas",
    "Curaçá", "Dário Meira", "Dias d'Ávila", "Dom Basílio", "Dom Macedo Costa", "Elísio Medrado",
    "Encruzilhada", "Entre Rios", "Érico Cardoso", "Esplanada", "Euclides da Cunha", "Eunápolis",
    "Fátima", "Feira da Mata", "Feira de Santana", "Filadélfia", "Firmino Alves", "Floresta Azul",
    "Formosa do Rio Preto", "Gandu", "Gavião", "Gentio do Ouro", "Glória", "Gongogi",
    "Governador Mangabeira", "Guajeru", "Guanambi", "Guaratinga", "Heliópolis", "Iaçu",
    "Ibiassucê", "Ibicaraí", "Ibicoara", "Ibicuí", "Ibipeba", "Ibipitanga", "Ibiquera",
    "Ibirapitanga", "Ibirapuã", "Ibirataia", "Ibitiara", "Ibititá", "Ibotirama", "Ichu",
    "Igaporã", "Igrapiúna", "Iguaí", "Ilhéus", "Inhambupe", "Ipecaetá", "Ipiaú", "Ipirá",
    "Ipupiara", "Irajuba", "Iramaia", "Iraquara", "Irará", "Irecê", "Itabela", "Itaberaba",
    "Itabuna", "Itacaré", "Itaeté", "Itagi", "Itagibá", "Itagimirim", "Itaguaçu da Bahia",
    "Itaju do Colônia", "Itajuípe", "Itamaraju", "Itamari", "Itambé", "Itanagra", "Itanhém",
    "Itaparica", "Itapé", "Itapebi", "Itapetinga", "Itapicuru", "Itapitanga", "Itaquara",
    "Itarantim", "Itatim", "Itiruçu", "Itiúba", "Itororó", "Ituaçu", "Ituberá", "Iuiú",
    "Jaborandi", "Jacaraci", "Jacobina", "Jaguaquara", "Jaguarari", "Jaguaripe", "Jandaíra",
    "Jequié", "Jeremoabo", "Jiquiriçá", "Jitaúna", "João Dourado", "Juazeiro", "Jucuruçu",
    "Jussara", "Jussari", "Jussiape", "Lafaiete Coutinho", "Lagoa Real", "Laje", "Lajedão",
    "Lajedinho", "Lajedo do Tabocal", "Lamarão", "Lapão", "Lauro de Freitas", "Lençóis",
    "Licínio de Almeida", "Livramento de Nossa Senhora", "Luís Eduardo Magalhães", "Macajuba",
    "Macarani", "Macaúbas", "Macururé", "Madre de Deus", "Maetinga", "Maiquinique", "Mairi",
    "Malhada", "Malhada de Pedras", "Manoel Vitorino", "Mansidão", "Maracás", "Maragogipe",
    "Maraú", "Marcionílio Souza", "Mascote", "Mata de São João", "Matina", "Medeiros Neto",
    "Miguel Calmon", "Milagres", "Mirangaba", "Mirante", "Monte Santo", "Morpará",
    "Morro do Chapéu", "Mortugaba", "Mucugê", "Mucuri", "Mulungu do Morro", "Mundo Novo",
    "Muniz Ferreira", "Muquém do São Francisco", "Muritiba", "Mutuípe", "Nilo Peçanha",
    "Nordestina", "Nova Canaã", "Nova Fátima", "Nova Ibiá", "Nova Itarana", "Nova Redenção",
    "Nova Soure", "Nova Viçosa", "Novo Horizonte", "Novo Triunfo", "Olindina",
    "Oliveira dos Brejinhos", "Ouriçangas", "Ourolândia", "Palmas de Monte Alto", "Palmeiras",
    "Paramirim", "Paratinga", "Paripiranga", "Pau Brasil", "Paulo Afonso", "Pé de Serra",
    "Pedrão", "Pedro Alexandre", "Piatã", "Pilão Arcado", "Pindaí", "Pindobaçu", "Pintadas",
    "Piraí do Norte", "Piripá", "Piritiba", "Planaltino", "Planalto", "Poções", "Pojuca",
    "Ponto Novo", "Porto Seguro", "Prado", "Presidente Dutra", "Presidente Jânio Quadros",
    "Presidente Tancredo Neves", "Queimadas", "Quijingue", "Quixabeira", "Rafael Jambeiro",
    "Remanso", "Retirolândia", "Riachão das Neves", "Riachão do Jacuípe", "Riacho de Santana",
    "Ribeira do Amparo", "Ribeira do Pombal", "Ribeirão do Largo", "Rio de Contas",
    "Rio do Antônio", "Rio do Pires", "Rio Real", "Rodelas", "Ruy Barbosa", "Salinas da Margarida",
    "Salvador", "Santa Bárbara", "Santa Brígida", "Santa Cruz Cabrália", "Santa Cruz da Vitória",
    "Santa Inês", "Santa Luzia", "Santa Maria da Vitória", "Santa Rita de Cássia", "Santa Teresinha",
    "Santaluz", "Santana", "Santanópolis", "Santo Amaro", "Santo Antônio de Jesus",
    "Santo Estêvão", "São Desidério", "São Domingos", "São Felipe", "São Félix",
    "São Félix do Coribe", "São Francisco do Conde", "São Gabriel", "São Gonçalo dos Campos",
    "São José da Vitória", "São José do Jacuípe", "São Miguel das Matas", "São Sebastião do Passé",
    "Sapeaçu", "Sátiro Dias", "Saubara", "Saúde", "Seabra", "Sebastião Laranjeiras",
    "Senhor do Bonfim", "Sento Sé", "Serra do Ramalho", "Serra Dourada", "Serra Preta",
    "Serrinha", "Serrolândia", "Simões Filho", "Sítio do Mato", "Sítio do Quinto", "Sobradinho",
    "Souto Soares", "Tabocas do Brejo Velho", "Tanhaçu", "Tanque Novo", "Tanquinho", "Taperoá",
    "Tapiramutá", "Teixeira de Freitas", "Teodoro Sampaio", "Teofilândia", "Teolândia",
    "Terra Nova", "Tremedal", "Tucano", "Uauá", "Ubaíra", "Ubaitaba", "Ubatã", "Uibaí",
    "Umburanas", "Una", "Urandi", "Uruçuca", "Utinga", "Valença", "Valente", "Várzea da Roça",
    "Várzea do Poço", "Várzea Nova", "Varzedo", "Vera Cruz", "Vereda", "Vitória da Conquista",
    "Wagner", "Wanderley", "Wenceslau Guimarães", "Xique-Xique"
])

CIDADES_RJ = sorted([
    "Angra dos Reis", "Aperibé", "Araruama", "Areal", "Armação dos Búzios",
    "Arraial do Cabo", "Barra do Piraí", "Barra Mansa", "Belford Roxo", "Bom Jardim",
    "Bom Jesus do Itabapoana", "Cabo Frio", "Cachoeiras de Macacu", "Cambuci",
    "Campos dos Goytacazes", "Cantagalo", "Carapebus", "Cardoso Moreira", "Carmo",
    "Casimiro de Abreu", "Comendador Levy Gasparian", "Conceição de Macabu", "Cordeiro",
    "Duas Barras", "Duque de Caxias", "Engenheiro Paulo de Frontin", "Guapimirim",
    "Iguaba Grande", "Itaboraí", "Itaguaí", "Italva", "Itaocara", "Itaperuna",
    "Itatiaia", "Japeri", "Laje do Muriaé", "Macaé", "Macuco", "Magé", "Mangaratiba",
    "Maricá", "Mendes", "Mesquita", "Miguel Pereira", "Miracema", "Natividade",
    "Nilópolis", "Niterói", "Nova Friburgo", "Nova Iguaçu", "Paracambi",
    "Paraíba do Sul", "Paraty", "Paty do Alferes", "Petrópolis", "Pinheiral",
    "Piraí", "Porciúncula", "Porto Real", "Quatis", "Queimados", "Quissamã",
    "Resende", "Rio Bonito", "Rio Claro", "Rio das Flores", "Rio das Ostras",
    "Rio de Janeiro", "Santa Maria Madalena", "Santo Antônio de Pádua", "São Fidélis",
    "São Francisco de Itabapoana", "São Gonçalo", "São João da Barra",
    "São João de Meriti", "São José de Ubá", "São José do Vale do Rio Preto",
    "São Pedro da Aldeia", "São Sebastião do Alto", "Saquarema", "Seropédica",
    "Silva Jardim", "Sumidouro", "Tanguá", "Teresópolis", "Trajano de Moraes",
    "Três Rios", "Valença", "Varre-Sai", "Vassouras", "Volta Redonda"
])

CIDADES_MG_BASE = sorted([
    "Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim",
    "Montes Claros", "Ribeirão das Neves", "Uberaba", "Governador Valadares",
    "Ipatinga", "Sete Lagoas", "Divinópolis", "Santa Luzia", "Ibirité",
    "Poços de Caldas", "Patos de Minas", "Pouso Alegre", "Teófilo Otoni",
    "Barbacena", "Sabará", "Varginha", "Vespasiano", "Conselheiro Lafaiete",
    "Itabira", "Araguari", "Ubá", "Passos", "Coronel Fabriciano", "Muriaé",
    "Ituiutaba", "Lavras", "Itajubá", "Nova Serrana", "Itaúna", "Pará de Minas",
    "Paracatu", "Caratinga", "Nova Lima", "São João del-Rei", "Patrocínio",
    "Timóteo", "Manhuaçu", "Unaí", "Curvelo", "Alfenas", "João Monlevade",
    "Três Corações", "Viçosa", "Cataguases", "Ouro Preto", "Janaúba",
    "São Sebastião do Paraíso", "Januária", "Formiga", "Esmeraldas",
    "Pedro Leopoldo", "Ponte Nova", "Mariana", "Diamantina", "São Lourenço"
])

CIDADES_SP_BASE = sorted([
    "São Paulo", "Guarulhos", "Campinas", "São Bernardo do Campo", "Santo André",
    "São José dos Campos", "Osasco", "Ribeirão Preto", "Sorocaba", "Santos",
    "Mauá", "São José do Rio Preto", "Mogi das Cruzes", "Diadema", "Jundiaí",
    "Piracicaba", "Carapicuíba", "Bauru", "Itaquaquecetuba", "São Vicente",
    "Franca", "Praia Grande", "Guarujá", "Taubaté", "Limeira", "Suzano",
    "Taboão da Serra", "Sumaré", "Barueri", "Embu das Artes", "Indaiatuba",
    "Cotia", "Americana", "Marília", "Araraquara", "Jacareí", "Presidente Prudente"
])

@st.cache_data(ttl=86400, show_spinner=False)
def carregar_municipios(sigla_uf):
    if sigla_uf == "PE":
        return CIDADES_PE
    if sigla_uf == "CE":
        return CIDADES_CE
    if sigla_uf == "PA":
        return CIDADES_PA
    if sigla_uf == "RS":
        return CIDADES_RS
    if sigla_uf == "PR":
        return CIDADES_PR
    if sigla_uf == "BA":
        return CIDADES_BA
    if sigla_uf == "RJ":
        return CIDADES_RJ
    try:
        url_bapi = f"https://brasilapi.com.br/api/ibge/municipios/v1/{sigla_uf}"
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url_bapi, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            if dados and isinstance(dados, list):
                return sorted([m['nome'] for m in dados])
    except Exception:
        pass
    try:
        url_ibge = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{sigla_uf}/municipios"
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url_ibge, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            dados = json.loads(resp.read().decode('utf-8'))
            if dados and isinstance(dados, list):
                return sorted([m['nome'] for m in dados])
    except Exception:
        pass
    if sigla_uf == "MG":
        return CIDADES_MG_BASE
    if sigla_uf == "SP":
        return CIDADES_SP_BASE
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
    subst = {
        'Á':'A','À':'A','Ã':'A','Â':'A','É':'E','Ê':'E','Í':'I','Ó':'O','Ô':'O','Õ':'O','Ú':'U',
        'á':'a','à':'a','ã':'a','â':'a','é':'e','ê':'e','í':'i','ó':'o','ô':'o','õ':'o','ú':'u',
        'ç':'c','Ç':'C','º':'o','ª':'a'
    }
    texto = str(t)
    for k, v in subst.items():
        texto = texto.replace(k, v)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def fabricar_pdf_estilizado(nome_c, cid_c, dt_ref, triade_info, pot_texto, tab_pont_raw, tab_proj_raw):
    if not REPORTLAB_DISPONIVEL: return None
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w_page, h_page = A4

    cor_escura = HexColor('#1f1b29')
    cor_ciano = HexColor('#7df9ff')
    cor_fundo_card = HexColor('#f5f4f9')
    cor_borda = HexColor('#dcd6f7')

    # PÁGINA 1
    c.setFillColor(cor_escura)
    c.rect(0, h_page - 100, w_page, 100, fill=1, stroke=0)
    c.setFillColor(cor_ciano)
    c.rect(0, h_page - 104, w_page, 4, fill=1, stroke=0)

    c.setFillColor(cor_ciano)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(45, h_page - 42, seguro_latin("ASTROLOGIA CONSCIENTE"))
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(45, h_page - 62, seguro_latin("A Danca dos Ponteiros | Relatorio Tecnico & Preditivo"))
    c.setFont("Helvetica", 9)
    c.drawString(45, h_page - 78, seguro_latin("Pesquisa & Metodologia: Douglas Rosa (@astrolodoug)"))

    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, h_page - 170, w_page - 80, 55, 6, fill=1, stroke=1)
    c.setFillColor(cor_escura)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, h_page - 130, seguro_latin(f"Consulente: {nome_c}"))
    c.setFont("Helvetica", 9)
    c.drawString(55, h_page - 146, seguro_latin(f"Local de Nascimento: {cid_c}"))
    c.drawString(320, h_page - 146, seguro_latin(f"Data de Referencia: {dt_ref}"))

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(cor_escura)
    c.drawString(45, h_page - 195, seguro_latin("1. Sintese da Matriz Natal & Eixo de Maior Potencial"))
    c.line(45, h_page - 200, w_page - 45, h_page - 200)

    c.setFillColor(cor_fundo_card)
    c.roundRect(40, h_page - 265, w_page - 80, 55, 6, fill=1, stroke=1)
    c.setFillColor(cor_escura)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, h_page - 225, seguro_latin(f"• Sol Natal: {triade_info['sol']}"))
    c.drawString(55, h_page - 240, seguro_latin(f"• Lua Natal: {triade_info['lua']}"))
    c.drawString(55, h_page - 255, seguro_latin(f"• Ascendente: {triade_info['asc']}"))

    c.setFillColor(HexColor('#2b263b'))
    c.roundRect(40, h_page - 345, w_page - 80, 70, 6, fill=1, stroke=0)
    c.setFillColor(cor_ciano)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, h_page - 290, seguro_latin("AREA DE MAIOR VOCACAO & POTENCIAL DO MAPA:"))
    c.setFillColor(HexColor('#f0f0f0'))
    c.setFont("Helvetica", 9)
    c.drawString(55, h_page - 310, seguro_latin(f"Setor em Evidencia: {pot_texto['titulo']}"))
    c.drawString(55, h_page - 326, seguro_latin(f"{pot_texto['descricao'][:85]}"))
    c.drawString(55, h_page - 338, seguro_latin(f"{pot_texto['descricao'][85:170]}"))

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(cor_escura)
    c.drawString(45, h_page - 370, seguro_latin("2. Posicionamento dos 9 Ponteiros Ativos no Momento"))
    c.line(45, h_page - 375, w_page - 45, h_page - 375)

    y_p = h_page - 395
    c.setFont("Helvetica", 8.5)
    for it in tab_pont_raw:
        c.setFillColor(cor_escura)
        txt = f"• {it['Ponteiro']}: {it['Pos']}  |  {it['Reg']}"
        c.drawString(50, y_p, seguro_latin(txt))
        y_p -= 18

    c.setStrokeColor(cor_borda)
    c.line(45, 45, w_page - 45, 45)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(45, 32, seguro_latin("Astrologia Consciente | Douglas Rosa (@astrolodoug) - WhatsApp: (11) 97711-7024"))
    c.drawRightString(w_page - 45, 32, seguro_latin("Pagina 1 de 2"))

    c.showPage()

    # PÁGINA 2
    c.setFillColor(cor_escura)
    c.rect(0, h_page - 55, w_page, 55, fill=1, stroke=0)
    c.setFillColor(cor_ciano)
    c.rect(0, h_page - 58, w_page, 3, fill=1, stroke=0)
    c.setFillColor(cor_ciano)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, h_page - 34, seguro_latin("CRONOGRAMA PREDITIVO DOS PROXIMOS 12 MESES & DIRECIONAMENTO"))

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(cor_escura)
    c.drawString(45, h_page - 80, seguro_latin("3. Projecao dos 9 Ponteiros & Gatilhos no Tempo"))
    c.line(45, h_page - 85, w_page - 45, h_page - 85)

    y_f = h_page - 105
    c.setFont("Helvetica", 8.5)
    for p in tab_proj_raw:
        txt_proj = f"• {p['Data']}: {p['Ponteiro']} em {p['Aspecto']} ({p['Regência']})"
        c.drawString(50, y_f, seguro_latin(txt_proj))
        y_f -= 17

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(cor_escura)
    c.drawString(45, y_f - 15, seguro_latin("4. Guia Didatico: O Que Esperar Deste Periodo"))
    c.line(45, y_f - 20, w_page - 45, y_f - 20)

    y_f -= 35
    c.setFillColor(cor_fundo_card)
    c.setStrokeColor(cor_borda)
    c.roundRect(40, y_f - 95, w_page - 80, 100, 6, fill=1, stroke=1)
    
    c.setFillColor(cor_escura)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y_f - 12, seguro_latin("• Setores de Rigor e Maturidade (Saturno/Netuno):"))
    c.setFont("Helvetica", 8.5)
    c.drawString(65, y_f - 26, seguro_latin("Exigem método, limites claros e paciência. Toda tensão aponta onde as ilusões devem ceder"))
    c.drawString(65, y_f - 38, seguro_latin("lugar a estrutura profissional duradoura."))
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y_f - 56, seguro_latin("• Janelas de Expansao e Fluxo (Jupiter/Plutao):"))
    c.setFont("Helvetica", 8.5)
    c.drawString(65, y_f - 70, seguro_latin("Favorecem o reconhecimento do seu trabalho, alianças estratégicas e visibilidade."))
    c.drawString(65, y_f - 82, seguro_latin("Aproveite essas datas para iniciar projetos ou lançamentos."))

    y_ded = y_f - 125
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(cor_escura)
    c.drawString(45, y_ded, seguro_latin("5. Dedicatoria & Mensagem Final"))
    c.line(45, y_ded - 5, w_page - 45, y_ded - 5)

    c.setFillColor(HexColor('#2b263b'))
    c.roundRect(40, y_ded - 110, w_page - 80, 95, 6, fill=1, stroke=0)
    c.setFillColor(cor_ciano)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(55, y_ded - 25, seguro_latin("Uma mensagem de Douglas Rosa (@astrolodoug) para voce:"))
    c.setFillColor(HexColor('#f0f0f0'))
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(55, y_ded - 42, seguro_latin("\"O ceu nao determina o seu destino de forma fatalista: ele estabelece o compasso"))
    c.drawString(55, y_ded - 54, seguro_latin("exato do tempo. A Danca dos Ponteiros existe para que voce tome as redeas do seu"))
    c.drawString(55, y_ded - 66, seguro_latin("proprio relogio e conduza as transformacoes com total consciencia e estrategia.\""))

    c.setFillColor(cor_ciano)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y_ded - 88, seguro_latin("Agendamentos e Cursos: Instagram @astrolodoug | WhatsApp: (11) 97711-7024"))

    c.setStrokeColor(cor_borda)
    c.line(45, 45, w_page - 45, 45)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(45, 32, seguro_latin("Astrologia Consciente | Douglas Rosa (@astrolodoug) - Direitos Reservados"))
    c.drawRightString(w_page - 45, 32, seguro_latin("Pagina 2 de 2"))

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
    if sigla_uf == "PE" and "Recife" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Recife")
    elif sigla_uf == "CE" and "Fortaleza" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Fortaleza")
    elif sigla_uf == "PA" and "Belém" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Belém")
    elif sigla_uf == "RS" and "Porto Alegre" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Porto Alegre")
    elif sigla_uf == "PR" and "Curitiba" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Curitiba")
    elif sigla_uf == "SP" and "São Paulo" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("São Paulo")
    elif sigla_uf == "RJ" and "Rio de Janeiro" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Rio de Janeiro")
    elif sigla_uf == "BA" and "Salvador" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Salvador")
    elif sigla_uf == "MG" and "Belo Horizonte" in lista_cidades_uf:
        idx_padrao = lista_cidades_uf.index("Belo Horizonte")
    
    mun_escolhido = st.sidebar.selectbox(
        f"2. Município de {sigla_uf} ({total_cid} cidades disponíveis):",
        options=lista_cidades_uf,
        index=idx_padrao,
        key=f"mun_{sigla_uf}"
    )
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
                st.error(f"Localidade '{cidade}' não localizada. Tente selecionar outro município ou digitar manualmente.")
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

                planetas_dados = [("Sol", sujeito.sun), ("Lua", sujeito.moon), ("Mercúrio", sujeito.mercury), ("Vênus", sujeito.venus), ("Marte", sujeito.mars), ("Júpiter", sujeito.jupiter), ("Saturno", sujeito.saturn), ("Urano", sujeito.uranus), ("Netuno", sujeito.neptune), ("Plutão", sujeito.pluto)]
                
                tab_pl = []
                mapa_casas_planetas = {}
                for pn, po in planetas_dados:
                    p_abs = float(obter_dado(po, 'abs_pos', 0.0))
                    num_casa, por_orbe, orbe_val = calc_casa_orbe(p_abs, cuspides_abs)
                    mapa_casas_planetas[pn] = num_casa
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

                casa_destaque = mapa_casas_planetas.get("Sol", 10)
                potencial_info = {
                    "titulo": f"{casa_destaque}ª Casa Zodiacal",
                    "descricao": POTENCIAL_CASAS.get(casa_destaque, "Foco na consolidação de projetos e autoridade pessoal.")
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
                contato_in = c_lead1.text_input(
                    "WhatsApp (com DDD) ou E-mail:",
                    value=st.session_state.contato_salvo,
                    placeholder="ex: 11999998888 ou seu@email.com"
                )
                
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
                    
                    triade_resumo = {
                        "sol": f"{sujeito.sun['position']:.2f}° {nome_sig(sujeito.sun['sign'])} (Casa {mapa_casas_planetas.get('Sol',1)})",
                        "lua": f"{sujeito.moon['position']:.2f}° {nome_sig(sujeito.moon['sign'])} (Casa {mapa_casas_planetas.get('Lua',1)})",
                        "asc": f"{sujeito.first_house['position']:.2f}° {nome_sig(sujeito.first_house['sign'])} (1ª Casa)"
                    }

                    pdf_bytes = fabricar_pdf_estilizado(
                        nome, cidade, DATA_ANALISE.strftime('%d/%m/%Y'),
                        triade_resumo, potencial_info, tab_pont_pdf, tab_fp
                    )

                    st.success(f"✅ Contacto registado: **{st.session_state.contato_salvo}**! Seu relatório de alto padrão foi gerado:")

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
                                label="📥 Baixar PDF Estilizado",
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
