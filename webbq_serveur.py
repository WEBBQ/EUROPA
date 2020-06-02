# TD3-serveur1.py

import http.server
import socketserver
import sqlite3
from urllib.parse import urlparse, parse_qs, unquote
import json
from PIL import Image


client_nom= json.dumps({
            'given_name': 'Visteur', \
            'family_name': '001' \
             })

# définition du handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):
  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  # version du serveur
  server_version = 'webbq_serveur.py/1.0'

  # on surcharge la méthode qui traite les requêtes GET
  def do_GET(self):
    self.init_params()
    # prénom et nom dans la chaîne de requête
    if self.path_info[0] == "toctoc":
      self.send_toctoc()
    elif self.path_info[0] == "nom":
      self.send_nom()
    # requete location - retourne la liste de lieux et leurs coordonnées géogrpahiques
    elif self.path_info[0] == "location":
      data=self.get_countries()
      self.send_json(data)
    # le chemin d'accès commence par /country et se poursuit par un nom de pays
    elif self.path_info[0] == 'country' and len(self.path_info) > 1:
      self.send_country(self.path_info[1])
    # requête générique
    elif self.path_info[0] == "service":
      self.send_html('<p>Path info : <code>{}</p><p>Chaîne de requête : <code>{}</code></p>' \
          .format('/'.join(self.path_info),self.query_string));
    else:
      self.send_static()

  # méthode pour traiter les requêtes HEAD
  def do_HEAD(self):
      self.send_static()

  # méthode pour traiter les requêtes POST
  def do_POST(self):
    self.init_params()

    # prénom et nom dans la chaîne de requête dans le corps
    if self.path_info[0] == "toctoc":
      self.send_toctoc()

    elif self.path_info[0] == "nom":
      self.send_nom()
      
    # requête générique
    elif self.path_info[0] == "service":
      self.send_html(('<p>Path info : <code>{}</code></p><p>Chaîne de requête : <code>{}</code></p>' \
          + '<p>Corps :</p><pre>{}</pre>').format('/'.join(self.path_info),self.query_string,self.body));

    else:
      self.send_error(405)

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

  def get_countries(self):
    # création d'un curseur (conn est globale)
    c = conn.cursor()
    # récupération de la liste des pays dans la base
    c.execute("SELECT wp FROM europe_country")
    r = c.fetchall()
    # construction de la réponse
    data=[]
    n=0
    for a in r:
      n+=1
      sql = 'SELECT * from europe_country WHERE wp=?'
      c.execute(sql,(a[0],))
      r = c.fetchone()
      data.append({'id':a[0],'lat':r['latitude'],'lon':r['longitude'],'name':r['name']})
    return data
  
  # On renvoie les informations d'un pays
  def send_country(self,country):
    # préparation de la requête SQL
    c = conn.cursor()
    sql = 'SELECT * from europe_country WHERE wp=?'
    # récupération de l'information (ou pas)
    c.execute(sql,(country,))
    r = c.fetchone()
    # on n'a pas trouvé le pays demandé
    if r == None:
      self.send_error(404,'Country not found')
    # on génère un document au format html
    else:
      body = json.dumps({
        'offname':r['name'],\
        'capital':r['capital'],\
        'lat':r['latitude'],\
        'lon':r['longitude']\
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
