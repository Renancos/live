import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import threading

df = None


def carregar_arquivo():
    """Carrega o arquivo Excel e armazena no DataFrame global."""
    global df
    caminho_arquivo = filedialog.askopenfilename(filetypes=[("Arquivos Excel", "*.xlsx;*.xls")])
    if caminho_arquivo:
        def carregar():
            try:
                df_temp = pd.read_excel(caminho_arquivo, dtype=str)
                df_temp.columns = df_temp.columns.str.strip()  # Remove espaços extras nos nomes das colunas

                global df
                df = df_temp  # Atribuir ao df global somente após o carregamento completo
                messagebox.showinfo("Sucesso", "Arquivo carregado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível carregar o arquivo: {e}")

        threading.Thread(target=carregar, daemon=True).start()


def formatar_dados(df):
    """Formata as colunas de data e valores conforme solicitado."""
    # Colunas que devem ser formatadas como data
    colunas_data = ["Data da Venda", "Data Prevista", "Data de Envio para Ban"]
    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y")

    # Colunas que devem ser formatadas como contábil
    colunas_valores = ["Valor_venda", "Valor Bruto", "Valor Líquido"]
    for col in colunas_valores:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").map(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

    return df


def buscar_e_salvar():
    """Busca os dados de múltiplos NSUs e salva em abas separadas no Excel."""
    if df is None:
        messagebox.showerror("Erro", "Nenhum arquivo carregado!")
        return

    entrada = entrada_nsu.get().strip()
    lista_nsu = [nsu.strip() for nsu in entrada.split(",") if nsu.strip().isdigit()]

    if not lista_nsu:
        messagebox.showwarning("Entrada inválida", "Por favor, insira pelo menos um NSU válido (números separados por vírgula).")
        return

    caminho_saida = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Arquivos Excel", "*.xlsx")])
    if not caminho_saida:
        return

    with pd.ExcelWriter(caminho_saida, engine="xlsxwriter") as writer:
        workbook = writer.book
        formato_data = workbook.add_format({"num_format": "dd/mm/yyyy"})  # Formato de data correto

        for nsu in lista_nsu:
            if "NSU" not in df.columns or "Parcela" not in df.columns:
                continue

            filtro = (df["NSU"] == nsu) & (df["Parcela"] == "1")
            resultado = df[filtro]

            if resultado.empty:
                continue  # Pula NSUs sem resultados

            colunas_interesse = ["Numero PV", "Data de Envio para Ban", "Serie Antecip"]
            valores_interesse = resultado[colunas_interesse].drop_duplicates()

            if valores_interesse.empty:
                continue

            dados_finais = df[df[colunas_interesse].apply(tuple, axis=1).isin(valores_interesse.apply(tuple, axis=1))]

            # Aplicar formatação antes de exportar
            dados_finais = formatar_dados(dados_finais)

            # Adicionar ao arquivo Excel como aba separada
            sheet_name = nsu[:31]  # Limite de caracteres para abas no Excel
            dados_finais.to_excel(writer, sheet_name=sheet_name, index=False)

            # Aplicar formatação de data diretamente no Excel
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(dados_finais.columns):
                if col in ["Data da Venda", "Data Prevista", "Data de Envio para Ban"]:
                    worksheet.set_column(idx, idx, 15, formato_data)

    messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")


# Criando a interface gráfica
root = tk.Tk()
root.title("Carregar Planilha e Buscar NSUs")
root.geometry("450x300")

btn_carregar = tk.Button(root, text="Carregar Planilha", command=carregar_arquivo)
btn_carregar.pack(pady=10)

tk.Label(root, text="Digite os NSUs separados por vírgula:").pack()

entrada_nsu = tk.Entry(root, width=50)
entrada_nsu.pack(pady=5)

btn_buscar = tk.Button(root, text="Buscar e Salvar", command=buscar_e_salvar)
btn_buscar.pack(pady=10)

root.mainloop()
