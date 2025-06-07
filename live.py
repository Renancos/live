import time
import googleapiclient.discovery

API_KEY = "AIzaSyBq8fI9rnLQQQWd10TWMNjApzoecQS7TkQ"  # Insira sua chave de API aqui
VIDEO_ID = "IX9FJJTZ-Po"  # Insira o ID do vídeo ao vivo


def get_live_chat_id(api_key, video_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.videos().list(part="liveStreamingDetails", id=video_id)
    response = request.execute()

    try:
        return response["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
    except (IndexError, KeyError):
        print("Live chat ID não encontrado. O vídeo pode não estar ao vivo.")
        return None


def get_live_chat_messages(api_key, live_chat_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    while True:
        request = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails"
        )
        response = request.execute()

        for item in response.get("items", []):
            author = item["authorDetails"]["displayName"]
            message = item["snippet"]["displayMessage"]
            print(f"{author}: {message}")

        time.sleep(5)  # Evita ultrapassar a cota da API


if __name__ == "__main__":
    live_chat_id = get_live_chat_id(API_KEY, VIDEO_ID)

    if live_chat_id:
        get_live_chat_messages(API_KEY, live_chat_id)
