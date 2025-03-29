import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from deep_translator import GoogleTranslator  # Libreria alternativa
import sys

# Funzione per autenticarsi e ottenere il servizio YouTube
def get_youtube_service():
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    client_secrets_file = os.path.join(os.path.dirname(__file__), "client_secrets.json")
    
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    return youtube

# Funzione per controllare se un video esiste
def check_video_exists(youtube, video_id):
    try:
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        
        if len(response.get("items", [])) > 0:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Video trovato: {response['items'][0]['snippet']['title']}")
            return response['items'][0]['snippet']
        else:
            print("Video non trovato.")
            return None
    except googleapiclient.errors.HttpError as e:
        print(f"Errore durante la richiesta API: {e}")
        return None

# Funzione per impostare la lingua predefinita del video
def set_default_language(youtube, video_id, language_code):
    try:
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if not response.get("items", []):
            print("Video non trovato.")
            return False

        snippet = response["items"][0]["snippet"]
        snippet["defaultLanguage"] = language_code  # Imposta la lingua predefinita

        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": snippet
            }
        )
        update_response = update_request.execute()

        print(f"Lingua predefinita impostata su {language_code}.")
        return True
    except googleapiclient.errors.HttpError as e:
        print(f"Errore durante l'aggiornamento della lingua predefinita: {e}")
        return False

# Funzione per tradurre il testo
def translate_text(text, target_language="it"):
    try:
        translated = GoogleTranslator(source="auto", target=target_language).translate(text)
        return translated
    except Exception as e:
        print(f"Errore durante la traduzione per la lingua {target_language}: {e}")
        return None

# Funzione per aggiungere localizzazione al titolo e alla descrizione
def add_localization(youtube, video_id, language_code, localized_title, localized_description):
    try:
        request = youtube.videos().list(part="localizations", id=video_id)
        response = request.execute()
        
        localizations = response["items"][0].get("localizations", {})
        localizations[language_code] = {
            "title": localized_title,
            "description": localized_description
        }
        
        request = youtube.videos().update(
            part="localizations",
            body={
                "id": video_id,
                "localizations": localizations
            }
        )
        response = request.execute()

        print(f"Localizzazione aggiunta per la lingua {language_code}.")
        return True
    except googleapiclient.errors.HttpError as e:
        print(f"Errore durante la richiesta API: {e}")
        return False

# Funzione per leggere le lingue da un file di testo
def read_languages_from_file(file_path):
    try:
        with open(file_path, "r") as f:
            languages = [line.strip() for line in f if line.strip()]
        return languages
    except FileNotFoundError:
        print(f"Errore: il file {file_path} non è stato trovato.")
        return None
    except IOError as e:
        print(f"Errore durante la lettura del file {file_path}: {e}")
        return None

# Esempio di utilizzo
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Errore: devi fornire l'ID del video come argomento.")
        sys.exit(1)
    
    video_id = sys.argv[1]
    youtube = get_youtube_service()
    
    # Verifica se il video esiste
    video_details = check_video_exists(youtube, video_id)
    
    if video_details:
        print("Il video esiste e puoi procedere.")
        original_title = video_details['title']
        original_description = video_details['description']
        default_language = video_details.get('defaultLanguage', None)
        
        # Se il video non ha una lingua predefinita, impostala in italiano
        if not default_language:
            set_default_language(youtube, video_id, "it")
            default_language = "it"
        
        language_codes = read_languages_from_file(os.path.join(os.path.dirname(__file__), "youtube_languages.txt"))
        
        counter = 0
        for language_code in language_codes:
            if language_code != default_language:
                translated_title = translate_text(original_title, language_code)
                if translated_title is None:
                    continue
                
                translated_description = translate_text(original_description, language_code)
                if translated_description is None:
                    continue
                
                request = youtube.videos().list(part="localizations", id=video_id)
                response = request.execute()
                localizations = response["items"][0].get("localizations", {})
                
                if language_code not in localizations:
                    add_localization(youtube, video_id, language_code, translated_title, translated_description)
                    counter += 1
                else:
                    print(f"La lingua {language_code} è già localizzata.")
                    counter += 1
        
        print(f"Localizzazione completata per {counter} lingue su {len(language_codes)} presenti nel file.")
    else:
        print("Non puoi procedere, il video non esiste.")
