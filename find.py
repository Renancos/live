from flask import Flask, request, render_template_string, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "comentarios.db"

def carregar_comentarios_do_banco(ordem="desc"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ordem_sql = "DESC" if ordem == "desc" else "ASC"
    cursor.execute(f"SELECT data, hora, live, autor, mensagem, valor FROM comentarios ORDER BY data {ordem_sql}, hora {ordem_sql}")
    resultados = cursor.fetchall()
    conn.close()
    return resultados

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
            body { padding: 20px; background-color: #ffffff; }
            #comentarios > div { margin-bottom: 15px; padding: 10px; border-radius: 5px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            #comentarios > div.superchat {
                background-color: #fff3cd;
                border-left: 5px solid #ffa500;
            }
            .cabecalho { font-weight: 600; margin-bottom: 4px; }
            .valor-superchat { font-weight: 700; color: #856404; margin-left: 15px; margin-bottom: 6px; }
            .mensagem { margin-left: 15px; white-space: pre-wrap; }
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
            <div class="col-md-2">
                <label class="form-label">Palavras-chave</label>
                <input type="text" id="filtro_palavras" class="form-control" placeholder="ex: Diva, corrida">
            </div>
            <div class="col-md-1 d-flex align-items-end">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="filtro_superchat">
                    <label class="form-check-label">💰</label>
                </div>
            </div>
            <div class="col-md-1">
                <label class="form-label">Ordem</label>
                <select id="filtro_ordem" class="form-select">
                    <option value="desc">Mais recentes</option>
                    <option value="asc">Mais antigos</option>
                </select>
            </div>
            <div class="col-md-12 text-end">
                <button onclick="atualizarComentarios()" class="btn btn-primary">🔍 Filtrar</button>
            </div>
        </div>

        <div id="comentarios" class="mt-4"></div>

        <script>
            async function atualizarComentarios() {
                const horario = document.getElementById('filtro_horario').value;
                const live = document.getElementById('filtro_live').value;
                const autor = document.getElementById('filtro_autor').value;
                const palavras = document.getElementById('filtro_palavras').value;
                const superchat = document.getElementById('filtro_superchat').checked;
                const ordem = document.getElementById('filtro_ordem').value;

                let url = '/comentarios?';
                if (horario) url += `horario=${encodeURIComponent(horario)}&`;
                if (live) url += `live=${encodeURIComponent(live)}&`;
                if (autor) url += `autor=${encodeURIComponent(autor)}&`;
                if (palavras) url += `palavras=${encodeURIComponent(palavras)}&`;
                if (superchat) url += `superchat=1&`;
                if (ordem) url += `ordem=${ordem}`;

                const response = await fetch(url);
                const data = await response.json();
                const div = document.getElementById('comentarios');
                div.innerHTML = '';

                data.forEach(c => {
                    let isSuperchat = c.includes("Super Chat");
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

                    let container = document.createElement('div');
                    if (isSuperchat) {
                        container.className = "superchat";

                        let valor = "";
                        let mensagemSC = mensagem;
                        let valorMatch = mensagem.match(/^(R\\$[\\d,.]+)\\s*from\\s*[^:]+:\\s*(.*)$/i);
                        if (valorMatch) {
                            valor = valorMatch[1];
                            mensagemSC = valorMatch[2];
                        }

                        let cabecalhoDiv = document.createElement('div');
                        cabecalhoDiv.className = "cabecalho";
                        cabecalhoDiv.innerHTML = `${tempo} <span class="text-primary">${liveName}</span> - <span class="text-success">${autorNome}</span>`;

                        let valorDiv = document.createElement('div');
                        valorDiv.className = "valor-superchat";
                        valorDiv.textContent = `${valor} 💰`;

                        let mensagemDiv = document.createElement('div');
                        mensagemDiv.className = "mensagem";
                        mensagemDiv.textContent = mensagemSC;

                        container.appendChild(cabecalhoDiv);
                        container.appendChild(valorDiv);
                        container.appendChild(mensagemDiv);
                    } else {
                        container.className = "";

                        let cabecalhoDiv = document.createElement('div');
                        cabecalhoDiv.className = "cabecalho";
                        cabecalhoDiv.innerHTML = `${tempo} <span class="text-primary">${liveName}</span> - <span class="text-success">${autorNome}</span>`;

                        let mensagemDiv = document.createElement('div');
                        mensagemDiv.className = "mensagem";
                        mensagemDiv.textContent = mensagem;

                        container.appendChild(cabecalhoDiv);
                        container.appendChild(mensagemDiv);
                    }

                    div.appendChild(container);
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
    ordem = request.args.get("ordem", "desc")
    comentarios = carregar_comentarios_do_banco(ordem)

    horario = request.args.get("horario", "").strip()
    live = request.args.get("live", "").lower().strip()
    autor = request.args.get("autor", "").lower().strip()
    palavras = request.args.get("palavras", "").lower().strip()
    superchat = request.args.get("superchat")

    resultado_formatado = []

    for c in comentarios:
        data, hora, live_name, autor_nome, mensagem, valor = c

        prefixo = f"[{data} {hora}] {live_name} - {autor_nome}"
        try:
            if valor and valor.strip() and float(valor.replace("R$", "").replace(",", ".")) > 0:
                prefixo += " (Super Chat)"
        except (ValueError, AttributeError):
            pass

        linha = f"{prefixo}: {mensagem}"

        if horario and horario not in f"{data} {hora}":
            continue
        if live and live not in live_name.lower():
            continue
        if autor and autor not in autor_nome.lower():
            continue
        if palavras:
            palavras_lista = palavras.split()
            texto_lower = linha.lower()
            if not any(p in texto_lower for p in palavras_lista):
                continue
        if superchat and "(Super Chat" not in linha:
            continue

        resultado_formatado.append(linha)

    return jsonify(resultado_formatado)

if __name__ == "__main__":
    app.run(debug=True)
