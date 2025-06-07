from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)


def carregar_comentarios(arquivo="comentarios.txt"):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        return []


@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Comentários da Live</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; background-color: #f9f9f9; }
            #comentarios p { margin-bottom: 10px; }
            .superchat { background-color: #fff3cd; padding: 10px; border-left: 5px solid #ffc107; }
        </style>
    </head>
    <body>
        <h1 class="mb-4">🗨️ Comentários da Live</h1>

        <div class="row g-3 mb-4 bg-white p-3 shadow rounded" style="position: sticky; top: 0; z-index: 1000;">
            <div class="col-md-2">
                <label class="form-label">Data - Horário</label>
                <input type="text" id="filtro_horario" class="form-control" placeholder="ex: 16:05">
            </div>
            <div class="col-md-3">
                <label class="form-label">Live</label>
                <input type="text" id="filtro_live" class="form-control" placeholder="ex: DiaTV">
            </div>
            <div class="col-md-3">
                <label class="form-label">Autor</label>
                <input type="text" id="filtro_autor" class="form-control" placeholder="ex: Danilo Paiva">
            </div>
            <div class="col-md-3">
                <label class="form-label">Palavras-chave</label>
                <input type="text" id="filtro_palavras" class="form-control" placeholder="ex: Diva, corrida">
            </div>
            <div class="col-md-1 d-flex align-items-end">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="filtro_superchat">
                    <label class="form-check-label">💰</label>
                </div>
            </div>
            <div class="col-md-12 text-end">
                <button onclick="atualizarComentarios()" class="btn btn-primary">🔍 Filtrar</button>
            </div>
        </div>

        <div id="comentarios" class="mt-4">
            <!-- Comentários aparecerão aqui -->
        </div>

        <script>
            async function atualizarComentarios() {
                const horario = document.getElementById('filtro_horario').value;
                const live = document.getElementById('filtro_live').value;
                const autor = document.getElementById('filtro_autor').value;
                const palavras = document.getElementById('filtro_palavras').value;
                const superchat = document.getElementById('filtro_superchat').checked;

                let url = '/comentarios?';
                if (horario) url += `horario=${horario}&`;
                if (live) url += `live=${live}&`;
                if (autor) url += `autor=${autor}&`;
                if (palavras) url += `palavras=${palavras}&`;
                if (superchat) url += `superchat=1`;

                const response = await fetch(url);
                const data = await response.json();
                const div = document.getElementById('comentarios');
                div.innerHTML = '';
                data.forEach(c => {
                    let partes = c.split("] ");
                    let tempo = partes[0] + "]";
                    let resto = partes[1] || "";

                    let nome_completo = resto.split(":")[0];
                    if (nome_completo.includes(" (Super Chat")) {
                        nome_completo = nome_completo.split(" (Super Chat")[0];
                    }

                    let [liveName, autorNome] = nome_completo.split(" - ");
                    if (!autorNome) {
                        autorNome = liveName;
                        liveName = "";
                    }

                    let mensagem = resto.split(": ").slice(1).join(": ");
                    let p = document.createElement('p');
                    p.className = c.includes("Super Chat") ? "superchat" : "";
                    p.innerHTML = `<b>${tempo} <span class="text-primary">${liveName}</span> - <span class="text-success">${autorNome}</span></b>: ${mensagem}`;
                    div.appendChild(p);
                });
            }

            atualizarComentarios();
            setInterval(atualizarComentarios, 10000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/comentarios")
def comentarios():
    comentarios = carregar_comentarios()

    horario = request.args.get("horario", "").strip()
    live = request.args.get("live", "").lower().strip()
    autor = request.args.get("autor", "").lower().strip()
    palavras = request.args.get("palavras", "").lower().strip()
    superchat = request.args.get("superchat")

    filtrados = []

    for c in comentarios:
        if horario and horario not in c:
            continue

        try:
            partes = c.split("] ")
            corpo = partes[1]
            nome_completo = corpo.split(":")[0]

            if "(Super Chat" in nome_completo:
                nome_completo = nome_completo.split(" (Super Chat")[0]

            if " - " in nome_completo:
                live_name, autor_nome = nome_completo.split(" - ", 1)
            else:
                live_name = ""
                autor_nome = nome_completo

        except Exception:
            continue

        if live and live not in live_name.lower():
            continue
        if autor and autor not in autor_nome.lower():
            continue
        if palavras:
            palavras_lista = palavras.split()
            if not any(p in c.lower() for p in palavras_lista):
                continue
        if superchat and "(Super Chat" not in c:
            continue

        filtrados.append(c.strip())

    return jsonify(filtrados)


if __name__ == "__main__":
    app.run(debug=True)
