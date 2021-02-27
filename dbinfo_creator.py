import sqlite3
import wptools

def conv(num):
  try:
    if num[1]=="trillion":
        return float(num[0])*1000000000000
    elif num[1]=="billon":
        return float(num[0])*1000000000
    elif num[1]=="million":
        return float(num[0])*1000000
    elif num[1]=="thousand":
        return float(num[0])*1000
    else:
        return float(num[0])
  except:
    return float(num[0])

def save_country(country):
    page = wptools.page(country)
    page.get_parse(False)
    info=page.data['infobox']
    # préparation de la commande SQL
    c = conn.cursor()
    sql = 'INSERT OR REPLACE INTO europe_country_info VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    # les infos à enregistrer
    try:
        ar=info['area_rank'].split("st")[0].split("nd")[0].split("rd")[0].split("th")[0]
    except:
        ar="NaN"
    try:
        po=info['population_estimate_rank'].split("st")[0].split("nd")[0].split("rd")[0].split("th")[0]
    except:
        po="NaN"
    try:
        gd=info['GDP_nominal_rank'].split("st")[0].split("nd")[0].split("rd")[0].split("th")[0]
    except:
        gd="NaN"
    try:
        hd=info['HDI_rank'].split("st")[0].split("nd")[0].split("rd")[0].split("th")[0]
    except:
        hd="NaN"
    try:
        area=info['area_km2'].replace(",","")
    except:
        area="NaN"
    try:
        pop=info['population_estimate'].replace(",","").split("}")[2].split("{")[0].replace(" ","")
    except:
        pop="NaN"
    try:
        gdp_a=info['GDP_nominal'].replace(",","").split("$")[-1].split("&nbsp;")[0].split(" ")[0]
        gdp_b=info['GDP_nominal'].replace(",","").split("$")[-1].split("&nbsp;")[-1].split(" ")[-1]
        gdp=conv([gdp_a,gdp_b])
    except:
        gdp="NaN"
    try:
        gini=info['Gini']
    except:
        gini="NaN"
    try:
        hdi=info['HDI']
    except:
        hdi="NaN"
    # soumission de la commande (noter que le second argument est un tuple)
    c.execute(sql,(country, ar,po,gd,hd,area,pop,gdp,gini,hdi))
    conn.commit()

def get_countries():
    # création d'un curseur (conn est globale)
    c = conn.cursor()
    # récupération de la liste des pays dans la base
    c.execute("SELECT wp FROM europe_country_en")
    r = c.fetchall()
    # construction de la réponse
    data=[]
    for a in r:
      sql = 'SELECT * from europe_country_en WHERE wp=?'
      c.execute(sql,(a[0],))
      r = c.fetchone()
      data.append(a[0])
    return data

def init_db(conn):
    for country in get_countries():
            info = save_country(country)
            print(country)


conn = sqlite3.connect('europe.db')
# Pour accéder au résultat des requêtes sous forme d'un dictionnaire
conn.row_factory = sqlite3.Row
init_db(conn)
