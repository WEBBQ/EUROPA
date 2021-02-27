import http.server
import socketserver
import sqlite3
from urllib.parse import urlparse, parse_qs, unquote
import json
from bs4 import BeautifulSoup
import requests
import urllib
import wptools

lang_choix=['wu','en','fr','de','zh','ar']
lang='_en'
client_nom= json.dumps({
            'given_name': 'Visteur', \
            'family_name': '001' \
             })
unit={"_en":["trillion ","billion ","million ","thousand "],\
      "_de":["Tausend ","Billion ","Million ","tausend "],\
      "_fr":["trillion ","billion ","million ","mille "],\
      "_ar":["تريليون ","بليون ","مليون ","ألف "],\
      "_zh":["兆 ","亿 ","千 ","百 "],\
      }

def get_link(country):
    # desktop user-agent
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"
    # mobile user-agent
    MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"
    query = str(country).replace(' ', '+')
    URL = f"https://www.google.com/search?q={query}&tbm=nws&hl=en"

    headers = {"user-agent": USER_AGENT}
    resp = requests.get(URL, headers=headers)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
        results = []
        for g in soup.find_all('h3'):
            anchors = g.find_all('a')
            try:
                if anchors:
                    link = str(anchors[0]['href'])
                    title = g.text
                    item = {
                        "title": title,
                        "link": link
                    }
                    if item not in results:
                        results.append(item)
                    if len(results)>=3:
                        break
            except:
                 pass
    return results


def treat(number):
    global lang
    if lang !="_zh":
        if len(str(number).split(".")[0])>12:
            return[float(number)/1000000000000,unit[lang][0]]
        elif len(str(number).split(".")[0])>9:
            return[float(number)/1000000000,unit[lang][1]]
        elif len(str(number).split(".")[0])>6:
            return[float(number)/1000000,unit[lang][2]]
        elif len(str(number).split(".")[0])>3:
            return[float(number)/1000,unit[lang][3]]
        else:
            return[float(number),""]
    else:
        if len(str(number).split(".")[0])>12:
            return[float(number)/1000000000000,unit[lang][0]]
        elif len(str(number).split(".")[0])>8:
            return[float(number)/100000000,unit[lang][1]]
        elif len(str(number).split(".")[0])>4:
            return[float(number)/10000,unit[lang][2]]
        elif len(str(number).split(".")[0])>3:
            return[float(number)/1000,unit[lang][3]]
        else:
            return[float(number),""]
      
def get_data(country):
    global lang
    c = conn.cursor()
    sql = 'SELECT * from europe_country_info WHERE wp=?'
    # récupération de l'information (ou pas)
    c.execute(sql,(country,))
    info = c.fetchone()
    if info == None:
      self.send_error(404,'Country not found')
    # on génère un document au format html
    else:
      ar=247-int(info['area_rank'])+1
      po=247-int(info['population_estimate_rank'])+1
      gd=247-int(info['GDP_nominal_rank'])+1
      hd=247-int(info['HDI_rank'])+1
      [area,area_u]=treat(info['area_km2'])
      [pop,pop_u]=treat(info['population_estimate'])
      if pop_u!="":
          pop_u=pop_u.replace(" ","")
      [gdp,gdp_u]=treat(info['GPA'])
      Gini=float(info['Gini'])
      if Gini>0:
          gi=100-Gini
          Gini=str(round(Gini,2))
      else:
          gi=0
          Gini="NaN"
      HDI=float(info['HDI'])
      if HDI>0:
          HDI=str(round(HDI,2))
      else:
          HDI="NaN"
      if lang in ["_fr","_de"]:
          Gini=Gini.replace(".",",")
          HDI=HDI.replace(".",",")
          return [[" | "+str(round(area,2)).replace(".",",")+" "+area_u+"km^2"," | "+str(round(pop,2)).replace(".",",")+" "+pop_u,\
                   " | "+str(round(gdp,2)).replace(".",",")+" "+gdp_u+"$"," | "+Gini," | "+HDI],\
                  [ar,po,gd,hd,gi]]
      else:
          return [[" | "+str(round(area,2))+" "+area_u+"km^2"," | "+str(round(pop,2))+" "+pop_u,\
                   " | "+str(round(gdp,2))+" "+gdp_u+"$"," | "+Gini," | "+HDI],\
                  [ar,po,gd,hd,gi]]


# définition du handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):
  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  # version du serveur
  server_version = 'webbq_serveur.py/2.0'

  # on surcharge la méthode qui traite les requêtes GET
  def do_GET(self):
    global lang
    self.init_params()
    # prénom et nom dans la chaîne de requête
    if len(self.path_info)>0:
      if self.path_info[0] == "toctoc":
        self.send_toctoc()
      elif self.path_info[0] == "nom":
        self.send_nom()
      # requete location - retourne la liste de lieux et leurs coordonnées géogrpahiques
      elif self.path_info[0] == "location":
        data=self.get_countries(lang)
        self.send_json(data)
      # le chemin d'accès commence par /country et se poursuit par un nom de pays
      elif self.path_info[0] == 'country' and len(self.path_info) > 1:
        self.send_country(self.path_info[1],lang)
      # requête générique
      elif self.path_info[0] == "service":
        self.send_html('<p>Path info : <code>{}</p><p>Chaîne de requête : <code>{}</code></p>' \
            .format('/'.join(self.path_info),self.query_string));
      elif self.path_info[0].lower() in lang_choix:
        lang="_"+self.path_info.pop(0).lower()
        if lang=="_wu":
          lang="_zh"
        self.path=""
        for i in self.path_info:
          self.path += ("/"+i)
        self.do_GET()
      else:
        self.send_static()
    else:
      self.send_error(404,'Country not found')

  #
  # On envoie un document le nom et le prénom
  #    
  def send_toctoc(self):
    global client_nom
    # on construit une chaîne de caractère json
    if len(self.path_info) <= 1 or self.path_info[1]=='' or self.path_info[2]=='':   # pas de paramètre dans l'URL => on utilise la query string
        client_nom = json.dumps({
            'given_name': 'Visteur', \
            'family_name': '001' \
             })
    else:
        client_nom = json.dumps({
            'given_name': self.path_info[1], \
            'family_name': self.path_info[2] \
             });
    
  def send_nom(self):
    global client_nom
    body=client_nom
    headers = [('Content-Type','application/json')];
    self.send(body,headers)

  # on envoie un contenu encodé en json
  def send_json(self,data,headers=[]):
    body = bytes(json.dumps(data),'utf-8') # encodage en json et UTF-8
    self.send_response(200)
    self.send_header('Content-Type','application/json')
    self.send_header('Content-Length',int(len(body)))
    [self.send_header(*t) for t in headers]
    self.end_headers()
    self.wfile.write(body)

  def get_countries(self,lang='_en'):
    # création d'un curseur (conn est globale)
    c = conn.cursor()
    # récupération de la liste des pays dans la base
    c.execute("SELECT wp FROM europe_country"+lang)
    r = c.fetchall()
    # construction de la réponse
    data=[]
    for a in r:
      sql = 'SELECT * from europe_country'+lang+' WHERE wp=?'
      c.execute(sql,(a[0],))
      r = c.fetchone()
      data.append({'id':a[0],'lat':r['latitude'],'lon':r['longitude'],'name':r['name']})
    return data
  
  # On renvoie les informations d'un pays
  def send_country(self,country,lang='_en'):
    pal=country.split("%20")
    pan=pal.pop(0)
    for cn in pal:
      pan+=" "+"cn"
    country=pan
    print(country)
    # préparation de la requête SQL
    c = conn.cursor()
    sql = 'SELECT * from europe_country'+lang+' WHERE wp=?'
    # récupération de l'information (ou pas)
    c.execute(sql,(country,))
    r = c.fetchone()
    # on n'a pas trouvé le pays demandé
    print(r)
    if r == None:
      self.send_error(404,'Country not found')
    # on génère un document au format html
    else:
      cn=r['wp_en']
      if cn=="Azerbaidjan":
        cn="Azerbaijan"
      if cn=="Macedonia":
        cn="North Macedonia"
      if cn=="Bosnia-Herzegovina":
        cn="Bosnia and Herzegovina"
      da=get_data(cn)
      print(da[0])
      body = json.dumps({
        'wp':r['wp'],\
        'offname':r['name'],\
        'capital':r['capital'],\
        'lat':r['latitude'],\
        'lon':r['longitude'],\
        'id':r['wp_en'],\
        'information_head':da[0],\
        'information':da[1],\
        'links':get_link(cn)\
        })
      # on envoie la réponse
      headers = [('Content-Type','application/json')]
      self.send(body,headers)

  # on envoie le document statique demandé
  def send_static(self):
    # on modifie le chemin d'accès en insérant le répertoire préfixe
    self.path = self.static_dir + self.path
    
    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)


  # on envoie un document html dynamique
  def send_html(self,content):
     headers = [('Content-Type','text/html;charset=utf-8')]
     html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}' \
         .format(self.path_info[0],content)
     self.send(html,headers)


  # on envoie la réponse
  def send(self,body,headers=[]):
     encoded = bytes(body, 'UTF-8')

     self.send_response(200)

     [self.send_header(*t) for t in headers]
     self.send_header('Content-Length',int(len(encoded)))
     self.end_headers()

     self.wfile.write(encoded)

  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.query_string = info.query
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
    else:
      self.body = ''
   
    # traces
    print('info_path =',self.path_info)
    print('body =',length,ctype,self.body)
    print('params =', self.params)



# Ouverture d'une connexion avec la base de données
conn = sqlite3.connect('europe.db')
# Pour accéder au résultat des requêtes sous forme d'un dictionnaire
conn.row_factory = sqlite3.Row

# Instanciation et lancement du serveur

httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
