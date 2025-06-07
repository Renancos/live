import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import json
import os
import threading

ARQUIVO_JSON = "lives_salvas.json"

# Carregar lives salvas
def carregar_lives_salvas():
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Salvar lives no JSON
def salvar_lives(lives):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(lives, f, indent=4, ensure_ascii=False)

lives = carregar_lives_salvas()
modo_edicao = {"indice": None}  # Para armazenar o índice da live sendo editada

def adicionar_ou_salvar_edicao():
    video_id = video_id_entry.get().strip()
    nome = nome_entry.get().strip()

    if not video_id or not nome:
        messagebox.showerror("Erro", "Preencha o ID da live e o nome.")
        return

    if modo_edicao["indice"] is not None:
        idx = modo_edicao["indice"]
        lives[idx] = {"video_id": video_id, "nome": nome}
        salvar_lives(lives)
        lista_lives.delete(idx)
        lista_lives.insert(idx, f"{nome} ({video_id})")
        modo_edicao["indice"] = None
        add_btn.config(text="Adicionar Live")
    else:
        if any(live["video_id"] == video_id for live in lives):
            messagebox.showwarning("Duplicado", "Essa live já foi adicionada.")
            return
        lives.append({"video_id": video_id, "nome": nome})
        salvar_lives(lives)
        lista_lives.insert(tk.END, f"{nome} ({video_id})")

    video_id_entry.delete(0, tk.END)
    nome_entry.delete(0, tk.END)

def editar_live():
    selecionado = lista_lives.curselection()
    if not selecionado:
        messagebox.showwarning("Nenhuma seleção", "Selecione uma live para editar.")
        return

    idx = selecionado[0]
    live = lives[idx]
    video_id_entry.delete(0, tk.END)
    video_id_entry.insert(0, live["video_id"])
    nome_entry.delete(0, tk.END)
    nome_entry.insert(0, live["nome"])

    modo_edicao["indice"] = idx
    add_btn.config(text="Salvar Edição")

def remover_live():
    selecionado = lista_lives.curselection()
    if not selecionado:
        messagebox.showwarning("Nenhuma seleção", "Selecione uma live para remover.")
        return

    idx = selecionado[0]
    confirm = messagebox.askyesno("Confirmar", f"Remover a live '{lives[idx]['nome']}'?")
    if confirm:
        del lives[idx]
        salvar_lives(lives)
        lista_lives.delete(idx)

        if modo_edicao["indice"] == idx:
            modo_edicao["indice"] = None
            add_btn.config(text="Adicionar Live")

processos = []

def ler_saida(proc, nome):
    for linha in proc.stdout:
        print(f"[{nome}] {linha.rstrip()}")

def iniciar_capturas():
    if not lives:
        messagebox.showwarning("Nenhuma Live", "Adicione pelo menos uma live.")
        return

    for live in lives:
        video_id = live["video_id"]
        nome = live["nome"]

        proc = subprocess.Popen(
            [sys.executable, "captura.py", video_id, nome],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        processos.append(proc)

        thread = threading.Thread(target=ler_saida, args=(proc, nome), daemon=True)
        thread.start()

    messagebox.showinfo("Captura Iniciada", f"Captura iniciada para {len(lives)} live(s).")

# Interface
janela = tk.Tk()
janela.title("YouTube Live Chat Tracker")

tk.Label(janela, text="ID da Live:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
video_id_entry = tk.Entry(janela, width=35)
video_id_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(janela, text="Nome da Live:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
nome_entry = tk.Entry(janela, width=35)
nome_entry.grid(row=1, column=1, padx=10, pady=5)

add_btn = tk.Button(janela, text="Adicionar Live", command=adicionar_ou_salvar_edicao)
add_btn.grid(row=2, column=0, columnspan=2, pady=10)

tk.Label(janela, text="Lives Adicionadas:").grid(row=3, column=0, columnspan=2)

lista_lives = tk.Listbox(janela, width=60)
lista_lives.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

for live in lives:
    lista_lives.insert(tk.END, f"{live['nome']} ({live['video_id']})")

iniciar_btn = tk.Button(janela, text="Iniciar Captura", command=iniciar_capturas, bg="green", fg="white")
iniciar_btn.grid(row=5, column=0, columnspan=2, pady=10)

remover_btn = tk.Button(janela, text="Remover Selecionada", command=remover_live, bg="red", fg="white")
remover_btn.grid(row=6, column=0, columnspan=2, pady=5)

editar_btn = tk.Button(janela, text="Editar Selecionada", command=editar_live, bg="orange", fg="black")
editar_btn.grid(row=7, column=0, columnspan=2, pady=5)

janela.mainloop()
