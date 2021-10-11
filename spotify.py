import base64
import requests
import datetime
from urllib.parse import urlencode
import datetime
import pandas as pd

class SpotifyAPI(object):
  access_token = None 
  access_token_expires = datetime.datetime.now()
  acces_token_did_expire = True
  client_id = None
  client_secret = None
  token_url = 'https://accounts.spotify.com/api/token'

  def __init__(self, client_id, client_secret, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.client_id = client_id
    self.client_secret = client_secret

  def get_client_credential(self):
    """
    Returns a base64 encoded string
    """
    client_id = self.client_id
    client_secret = self.client_secret
    if client_secret == None or client_id == None:
      raise Exception("you must set client_id or client_secret")
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode())
    return client_creds_b64.decode() 

  def get_token_header(self):
    client_creds_b64 = self.get_client_credential()
    return {
        "Authorization": f"Basic {client_creds_b64}"
    }
 
  def get_token_data(self):
    return {
        "grant_type": "client_credentials"
    }


  def perform_auth(self):
    token_url = self.token_url
    token_data = self.get_token_data()
    token_header = self.get_token_header()
    r = requests.post(token_url, data=token_data, headers=token_header)
    if r.status_code not in range(200, 299):
      raise Exception("Could not authenticate client")
          #return False 
    data = r.json()
    access_token = data['access_token']
    expires_in = data['expires_in']
    now = datetime.datetime.now()
    expires = now + datetime.timedelta(seconds=expires_in)
    self.access_token = access_token
    self.access_token_expires = expires
    self.access_token_did_expire = expires < now
    return True
  
  def get_access_token(self):
    token = self.access_token
    expires = self.access_token_expires
    now = datetime.datetime.now()
    if expires < now:
      self.perform_auth()
      return self.get_access_token()
    elif token == None:
      self.perform_auth()
      return self.get_access_token()
    return token

  def get_access_header(self):
      access_token = self.get_access_token()
      header = {
      "Authorization": f"Bearer {access_token}"
      }
      return header



  def get_resource(self, _id, resource_type="albums", version='v1'):
    endpoint= f"https://api.spotify.com/{version}/{resource_type}/{_id}"
    header = self.get_access_header()
    r = requests.get(endpoint, headers=header)
    if r.status_code not in range(200, 299):
      return {}
    return r.json()
  
  def get_album(self, _id):
    return self.get_resource(_id, resource_type = 'albums')

  def get_artist(self, _id):
    return self.get_resource(_id, resource_type = 'artists')
  
  def get_related(self, _id):
    endpoint= f"https://api.spotify.com/v1/artists/{_id}/related-artists"
    header = self.get_access_header()
    r = requests.get(endpoint, headers=header)
    if r.status_code not in range(200, 299):
      return {}
    return r.json()

  def get_artist_album(self,_id):
    endpoint = f"https://api.spotify.com/v1/artists/{_id}/albums"
    header = self.get_access_header()
    r = requests.get(endpoint, headers=header)
    if r.status_code not in range(200,299):
      return {}
    return r.json()

  def get_info_tracks(self, _id):
    endpoint= f"https://api.spotify.com/v1/audio-features?ids={_id}"
    header = self.get_access_header()
    r = requests.get(endpoint, headers=header)
    if r.status_code not in range(200, 299):
      return {}
    return r.json()

  def get_track_album(self,_id):
    endpoint = f"https://api.spotify.com/v1/albums/{_id}/tracks"
    header = self.get_access_header()
    r = requests.get(endpoint, headers=header)
    if r.status_code not in range(200,299):
      return {}
    return r.json()

  def base_search(self, query_params, search_type='artist' ):
      header = self.get_access_header()
      endpoint = "https://api.spotify.com/v1/search"
      lookup_url = f"{endpoint}?{query_params}"
      r = requests.get(lookup_url, headers=header)
      if r.status_code not in range(200, 299):
        return {}
      return r.json()

  def raccomand_basic(self, seed_artist, genre, seed_track):
    header = self.get_access_header()
    endpoint = f"https://api.spotify.com/v1/recommendations?seed_artists={seed_artist}&seed_genres={genre}&seed_tracks={seed_track}&min_energy=0.4&min_popularity=20"
    r = requests.get(endpoint, headers=header)
    if r.status_code not in range(200, 299):
      return {}
    json_data = r.json()
    id_track_rec = json_data['tracks']
    return id_track_rec

    
  def search(self, query=None, operator=None, operator_query=None, search_type='artist' ):
      if query == None:
        raise Exception("Query is required")
      if isinstance(query, dict):
        query = "%20".join([f"{k}:{v}" for k,v in query.items()])
      if operator != None and operator_query != None:
        if operator.lower() == 'or' or operator.lower() == 'not': 
          operator = operator.upper()
          if isinstance(operator_query, str):
            query = f"{query} {operator} {operator_query}"
      query_params = urlencode({"q": query, 'type':search_type.lower()})

      return self.base_search(query_params)
      