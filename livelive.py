import time
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build

API_KEY = "AIzaSyBq8fI9rnLQQQWd10TWMNjApzoecQS7TkQ"
ARQUIVO_JSON = "lives_salvas.json"
DB_PATH = "comentarios.db"

# Cria ou conecta ao banco de dados SQLite com UNIQUE para evitar duplicados
def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comentarios (
            data TEXT,
            hora TEXT,
            live TEXT,
            autor TEXT,
            mensagem TEXT,
            valor TEXT,
            UNIQUE(live, autor, mensagem, data, hora)
        )
    ''')
    conn.commit()
    return conn

def corrigir_timestamp(ts):
    if '.' in ts:
        base, rest = ts.split('.', 1)
        microsec = rest.split('Z')[0].split('+')[0]
        microsec_corrigido = microsec[:6].ljust(6, '0')
        tz = ''
        if '+' in rest:
            tz = '+' + rest.split('+')[1]
        elif 'Z' in rest:
            tz = 'Z'
        return f"{base}.{microsec_corrigido}{tz}"
    return ts

def get_live_chat_id(api_key, video_id):
    youtube = build("youtube", "v3", developerKey=api_key)
    req = youtube.videos().list(part="liveStreamingDetails", id=video_id)
    res = req.execute()
    try:
        return res["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
    except (IndexError, KeyError):
        print(f"Live chat ID não encontrado para vídeo {video_id}.")
        return None

def salvar_comentarios_sqlite(conn, linhas):
    if linhas:
        conn.executemany("""
            INSERT OR IGNORE INTO comentarios (data, hora, live, autor, mensagem, valor)
            VALUES (?, ?, ?, ?, ?, ?)
        """, linhas)
        conn.commit()
        print(f"{len(linhas)} comentários tentados para salvar no SQLite (duplicates ignorados).")

def capturar_comentarios(api_key, live_chat_id, nome_live, conn):
    youtube = build("youtube", "v3", developerKey=api_key)
    linhas_para_salvar = []
    next_page_token = None

    while True:
        try:
            request = youtube.liveChatMessages().list(
                liveChatId=live_chat_id,
                part="snippet,authorDetails",
                maxResults=200,
                pageToken=next_page_token or ""
            )
            response = request.execute()

            items = response.get("items", [])
            if not items:
                print(f"Nenhum comentário encontrado para {nome_live} neste momento.")
                break

            for item in items:
                snippet = item["snippet"]
                autor = item["authorDetails"]["displayName"]
                mensagem = snippet.get("displayMessage", "")
                timestamp = corrigir_timestamp(snippet["publishedAt"])
                dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                dt_brasil = dt_utc.astimezone(timezone(timedelta(hours=-3)))
                data = dt_brasil.strftime("%d-%m-%y")
                hora = dt_brasil.strftime("%H:%M:%S")

                valor = ""
                if "superChatDetails" in snippet:
                    valor = snippet["superChatDetails"].get("amountDisplayString", "")

                linhas_para_salvar.append([data, hora, nome_live, autor, mensagem, valor])
                print(f"[{data} {hora}] {nome_live} - {autor}: {mensagem}")

            if len(linhas_para_salvar) >= 50:
                salvar_comentarios_sqlite(conn, linhas_para_salvar)
                linhas_para_salvar.clear()

            next_page_token = response.get("nextPageToken")
            time.sleep(5)

        except Exception as e:
            print(f"Erro ao capturar comentários de {nome_live}: {e}")
            break

    if linhas_para_salvar:
        salvar_comentarios_sqlite(conn, linhas_para_salvar)

def main():
    conn = conectar_banco()

    with open(ARQUIVO_JSON, encoding="utf-8") as f:
        lives = json.load(f)

    print("\n🔄 Iniciando captura contínua dos comentários...")
    while True:
        for live in lives:
            video_id = live["video_id"]
            nome_live = live["nome"]

            print(f"\n📺 Capturando comentários da live: {nome_live}")
            live_chat_id = get_live_chat_id(API_KEY, video_id)
            if live_chat_id:
                capturar_comentarios(API_KEY, live_chat_id, nome_live, conn)
            else:
                print(f"Pulando live '{nome_live}' - chat não disponível.")

        print("\n⏳ Esperando 60 segundos antes da próxima varredura...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()
