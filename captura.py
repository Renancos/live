import sys
import time
from datetime import datetime, timedelta, timezone
import googleapiclient.discovery

API_KEY = "AIzaSyBq8fI9rnLQQQWd10TWMNjApzoecQS7TkQ"  # Insira sua chave de API aqui

def corrigir_timestamp(ts):
    if '.' in ts:
        base, rest = ts.split('.', 1)
        microsec = rest.split('+')[0].split('Z')[0]
        microsec_corrigido = microsec[:6].ljust(6, '0')
        tz = ''
        if '+' in rest:
            tz = '+' + rest.split('+')[1]
        elif 'Z' in rest:
            tz = 'Z'
        return f"{base}.{microsec_corrigido}{tz}"
    return ts

def get_live_chat_id(api_key, video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.videos().list(part="liveStreamingDetails", id=video_id)
    response = request.execute()

    try:
        return response["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
    except (IndexError, KeyError):
        print("Live chat ID não encontrado. O vídeo pode não estar ao vivo.")
        return None

def salvar_comentario_arquivo(comentario, arquivo):
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(comentario + "\n")

def get_live_chat_messages(api_key, live_chat_id, nome_live):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    next_page_token = None
    nome_arquivo = "comentarios.txt"
    print(f"Salvando comentários no arquivo: {nome_arquivo}")

    ids_processados = set()  # Armazenar IDs de comentários já salvos

    while True:
        request = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails",
            pageToken=next_page_token or ""
        )
        response = request.execute()

        for item in response.get("items", []):
            comentario_id = item["id"]
            if comentario_id in ids_processados:
                continue  # Pula comentários já processados

            ids_processados.add(comentario_id)

            snippet = item["snippet"]
            timestamp = snippet["publishedAt"]
            timestamp_corrigido = corrigir_timestamp(timestamp)
            dt_utc = datetime.fromisoformat(timestamp_corrigido.replace("Z", "+00:00"))
            dt_brasil = dt_utc.astimezone(timezone(timedelta(hours=-3)))

            data = dt_brasil.strftime("%d-%m-%y")
            hora = dt_brasil.strftime("%H:%M:%S")

            autor = item["authorDetails"]["displayName"]

            if "superChatDetails" in snippet:
                valor = snippet["superChatDetails"]["amountDisplayString"]
                mensagem = snippet["displayMessage"]
                comentario_formatado = f"[{data} {hora}] {nome_live} - {autor} (Super Chat {valor}): {mensagem}"
            else:
                mensagem = snippet["displayMessage"]
                comentario_formatado = f"[{data} {hora}] {nome_live} - {autor}: {mensagem}"

            print(comentario_formatado)
            salvar_comentario_arquivo(comentario_formatado, nome_arquivo)

        next_page_token = response.get("nextPageToken")
        time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python captura.py <video_id> <nome_da_live>")
        sys.exit(1)

    video_id = sys.argv[1]
    nome_live = sys.argv[2]

    live_chat_id = get_live_chat_id(API_KEY, video_id)
    if live_chat_id:
        get_live_chat_messages(API_KEY, live_chat_id, nome_live)
