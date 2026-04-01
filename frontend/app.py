import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
	import sounddevice as sd  # type: ignore[import-not-found]
	from scipy.io.wavfile import write  # type: ignore[import-not-found]
	AUDIO_LIBS_OK = True
except Exception:
	AUDIO_LIBS_OK = False

import requests

API_URL = "http://127.0.0.1:8000"

gravando = False
audio_data = None
stream = None


class ControleEventosApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Controle de Eventos")
		self.root.geometry("420x540")

		self.eventos = []
		self.evento_selecionado = None

		container = tk.Frame(root)
		container.pack(fill="both", expand=True)

		self.canvas = tk.Canvas(container)
		self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)

		self.frame = tk.Frame(self.canvas, padx=16, pady=16)

		self.frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)

		self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.canvas.pack(side="left", fill="both", expand=True)
		self.scrollbar.pack(side="right", fill="y")

		def _on_mousewheel(event):
			self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

		self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

		self._montar_ui_principal()
		self.carregar_eventos()

	def _limpar_frame(self):
		for widget in self.frame.winfo_children():
			widget.destroy()

	def _montar_ui_principal(self):
		self._limpar_frame()

		self.titulo = tk.Label(self.frame, text="Eventos", font=("Arial", 16, "bold"))
		self.titulo.pack(pady=(0, 12))

		tk.Button(self.frame, text="Chat Lion 🦁", command=self.abrir_chat).pack(pady=10)

		self.lista_eventos = tk.Listbox(self.frame, width=40, height=10)
		self.lista_eventos.pack(fill="both", expand=True, pady=10)
		self.lista_eventos.bind("<<ListboxSelect>>", self.selecionar_evento)

		self.botao_recarregar = tk.Button(
			self.frame,
			text="Recarregar eventos",
			command=self.carregar_eventos,
		)
		self.botao_recarregar.pack(fill="x", expand=True, pady=(10, 16))

		self.label_evento = tk.Label(self.frame, text="Selecione um evento")
		self.label_evento.pack(anchor="w", fill="x", expand=True)

		self.label_entrada = tk.Label(self.frame, text="Entrada: R$ 0,00")
		self.label_entrada.pack(anchor="w", pady=(8, 0), fill="x", expand=True)

		self.label_saida = tk.Label(self.frame, text="Saida: R$ 0,00")
		self.label_saida.pack(anchor="w", fill="x", expand=True)

		self.label_saldo = tk.Label(self.frame, text="Saldo: R$ 0,00", font=("Arial", 11, "bold"))
		self.label_saldo.pack(anchor="w", pady=(0, 16), fill="x", expand=True)

		self.botao_historico = tk.Button(
			self.frame,
			text="Ver historico",
			command=self._ver_historico_selecionado,
			state="disabled",
		)
		self.botao_historico.pack(pady=10)

		ttk.Separator(self.frame, orient="horizontal").pack(fill="x", pady=8)

		tk.Label(self.frame, text="Nova movimentacao", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8, 8))

		tk.Label(self.frame, text="Tipo").pack(anchor="w")
		self.tipo_var = tk.StringVar(value="entrada")
		self.tipo_combo = ttk.Combobox(
			self.frame,
			textvariable=self.tipo_var,
			values=["entrada", "saida"],
			state="readonly",
		)
		self.tipo_combo.pack(fill="x", expand=True, pady=(0, 8))

		tk.Label(self.frame, text="Valor").pack(anchor="w")
		self.valor_entry = tk.Entry(self.frame)
		self.valor_entry.pack(fill="x", expand=True, pady=(0, 8))

		tk.Label(self.frame, text="Descricao").pack(anchor="w")
		self.descricao_entry = tk.Entry(self.frame)
		self.descricao_entry.pack(fill="x", expand=True, pady=(0, 12))

		self.botao_salvar = tk.Button(
			self.frame,
			text="Adicionar movimentacao",
			command=self.adicionar_movimentacao,
		)
		self.botao_salvar.pack(fill="x", expand=True)

	def _ver_historico_selecionado(self):
		if not self.evento_selecionado:
			messagebox.showwarning("Aviso", "Selecione um evento antes de ver o historico.")
			return
		self.ver_historico(self.evento_selecionado["id"])

	def carregar_eventos(self):
		self.lista_eventos.delete(0, tk.END)

		try:
			resposta = requests.get(f"{API_URL}/eventos", timeout=5)
			resposta.raise_for_status()
			self.eventos = resposta.json()
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Nao foi possivel carregar eventos.\n{exc}")
			return

		for evento in self.eventos:
			self.lista_eventos.insert(tk.END, f"{evento['id']} - {evento['nome']}")

		self.evento_selecionado = None
		self.atualizar_resumo({"entrada": 0, "saida": 0, "saldo": 0})
		self.label_evento.config(text="Selecione um evento")
		self.botao_historico.config(state="disabled")

	def selecionar_evento(self, _event):
		selecao = self.lista_eventos.curselection()
		if not selecao:
			return

		selecionado = self.lista_eventos.get(selecao[0])
		id_evento = int(selecionado.split(" - ")[0])
		self.abrir_evento(id_evento)

	def abrir_evento(self, id_evento):
		for evento in self.eventos:
			if evento["id"] == id_evento:
				self.evento_selecionado = evento
				break
		else:
			self.evento_selecionado = None
			messagebox.showwarning("Aviso", "Evento selecionado nao foi encontrado.")
			return

		self.label_evento.config(text=f"Evento: {self.evento_selecionado['nome']}")
		self.carregar_detalhes_evento(id_evento)
		self.botao_historico.config(state="normal")

	def ver_historico(self, id_evento):
		self._limpar_frame()

		try:
			dados = requests.get(
				f"{API_URL}/eventos/{id_evento}/historico",
				timeout=5,
			).json()
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Nao foi possivel carregar historico.\n{exc}")
			self._montar_ui_principal()
			self.carregar_eventos()
			return

		tk.Label(self.frame, text="Historico", font=("Arial", 16)).pack(pady=10)

		if not dados:
			tk.Label(self.frame, text="Sem movimentacoes").pack()
		else:
			for item in dados:
				texto = f"{item['tipo']} - R$ {item['valor']} - {item['descricao']}"
				tk.Label(self.frame, text=texto, anchor="w").pack(fill="x", padx=10)

		def voltar():
			self._montar_ui_principal()
			self.carregar_eventos()
			self.abrir_evento(id_evento)

		tk.Button(self.frame, text="Voltar", command=voltar).pack(pady=10)

		if not hasattr(self, "botao_historico"):
			self.botao_historico = tk.Button(self.frame, text="Ver historico")
			self.botao_historico.pack(pady=10)
		self.botao_historico.config(command=lambda: self.ver_historico(id_evento))

	def ver_historico(self, id_evento):
		historico_window = tk.Toplevel(self.root)
		historico_window.title("Historico")
		historico_window.geometry("400x500")

		frame = tk.Frame(historico_window, padx=16, pady=16)
		frame.pack(fill="both", expand=True)

		try:
			dados = requests.get(
				f"{API_URL}/eventos/{id_evento}/historico",
				timeout=5,
			).json()
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Nao foi possivel carregar historico.\n{exc}")
			historico_window.destroy()
			return

		tk.Label(frame, text="Historico", font=("Arial", 16)).pack(pady=10)

		if not dados:
			tk.Label(frame, text="Sem movimentacoes").pack()
		else:
			for item in dados:
				texto = f"{item['tipo']} - R$ {item['valor']} - {item['descricao']}"
				tk.Label(frame, text=texto, anchor="w").pack(fill="x", padx=10)

		def voltar():
			historico_window.destroy()
			self.abrir_evento(id_evento)

		tk.Button(frame, text="Voltar", command=voltar).pack(pady=10)

	def carregar_detalhes_evento(self, id_evento):
		try:
			resposta = requests.get(f"{API_URL}/eventos/{id_evento}", timeout=5)
			resposta.raise_for_status()
			dados = resposta.json()
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Nao foi possivel carregar os detalhes.\n{exc}")
			return

		self.atualizar_resumo(dados)

	def atualizar_resumo(self, dados):
		self.label_entrada.config(text=f"Entrada: R$ {dados['entrada']:.2f}")
		self.label_saida.config(text=f"Saida: R$ {dados['saida']:.2f}")
		self.label_saldo.config(text=f"Saldo: R$ {dados['saldo']:.2f}")

	def adicionar_movimentacao(self):
		if not self.evento_selecionado:
			messagebox.showwarning("Aviso", "Selecione um evento antes de adicionar uma movimentacao.")
			return

		valor_texto = self.valor_entry.get().strip().replace(",", ".")
		descricao = self.descricao_entry.get().strip()

		if not valor_texto or not descricao:
			messagebox.showwarning("Aviso", "Preencha valor e descricao.")
			return

		try:
			valor = float(valor_texto)
		except ValueError:
			messagebox.showwarning("Aviso", "Informe um valor numerico valido.")
			return

		payload = {
			"id_evento": self.evento_selecionado["id"],
			"tipo": self.tipo_var.get(),
			"valor": valor,
			"descricao": descricao,
		}

		try:
			resposta = requests.post(f"{API_URL}/movimentacao", json=payload, timeout=5)
			resposta.raise_for_status()
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Nao foi possivel salvar a movimentacao.\n{exc}")
			return

		self.valor_entry.delete(0, tk.END)
		self.descricao_entry.delete(0, tk.END)
		self.carregar_detalhes_evento(self.evento_selecionado["id"])
		messagebox.showinfo("Sucesso", "Movimentacao adicionada com sucesso.")

	def abrir_chat(self):
		chat_window = tk.Toplevel(self.root)
		chat_window.title("Lion IA 🦁")
		chat_window.geometry("400x500")

		chat_area = tk.Text(chat_window, state="disabled", wrap="word")
		chat_area.pack(fill="both", expand=True, padx=10, pady=10)

		botoes_frame = tk.Frame(chat_window)
		botoes_frame.pack(pady=5)

		entry = tk.Entry(chat_window)
		entry.pack(fill="x", padx=10, pady=5)

		imagens_selecionadas = []

		def selecionar_imagem():
			caminhos = filedialog.askopenfilenames(
				title="Selecione imagens",
				filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp")],
			)
			if not caminhos:
				return

			imagens_selecionadas.extend(caminhos)
			chat_area.config(state="normal")
			chat_area.insert(
				tk.END,
				f"{len(caminhos)} imagem(ns) anexada(s)\n",
			)
			chat_area.config(state="disabled")
			chat_area.see(tk.END)

		def enviar_mensagem():
			mensagem = entry.get().strip()
			entry.delete(0, tk.END)

			files = []
			open_files = []
			try:
				for caminho in imagens_selecionadas:
					arquivo = open(caminho, "rb")
					open_files.append(arquivo)
					files.append(("files", arquivo))

				data = {
					"mensagem": mensagem,
				}

				resp = requests.post(
					f"{API_URL}/ia/multimodal",
					files=files,
					data=data,
					timeout=30,
				)
				resp.raise_for_status()
				resposta = resp.json().get("resposta", "Sem resposta")
			except requests.RequestException as exc:
				resposta = f"Erro ao conectar com a IA: {exc}"
			finally:
				for arquivo in open_files:
					try:
						arquivo.close()
					except Exception:
						pass

			chat_area.config(state="normal")
			if mensagem:
				chat_area.insert(tk.END, f"Você: {mensagem}\n")
			chat_area.insert(tk.END, f"Lion 🦁: {resposta}\n\n")
			chat_area.config(state="disabled")
			chat_area.see(tk.END)

			imagens_selecionadas.clear()

		def iniciar_gravacao():
			global gravando, audio_data, stream

			if not AUDIO_LIBS_OK:
				messagebox.showwarning(
					"Aviso",
					"Bibliotecas de audio nao instaladas. Instale sounddevice e scipy.",
				)
				return

			gravando = True
			audio_data = []

			def callback(indata, frames, time, status):
				if gravando:
					audio_data.append(indata.copy())

			stream = sd.InputStream(callback=callback, channels=1, samplerate=44100)
			stream.start()

			chat_area.config(state="normal")
			chat_area.insert(tk.END, "🎤 Gravando...\n")
			chat_area.config(state="disabled")

		def parar_gravacao():
			global gravando, audio_data, stream

			if not stream:
				return

			gravando = False
			stream.stop()
			stream.close()
			stream = None

			try:
				import numpy as np

				audio = np.concatenate(audio_data, axis=0)
				write("audio.wav", 44100, audio)

				with open("audio.wav", "rb") as arquivo:
					files = {"file": arquivo}
					resp = requests.post(f"{API_URL}/ia/audio", files=files, timeout=30)
					resp.raise_for_status()
				texto = resp.json().get("texto", "")

				resp2 = requests.post(
					f"{API_URL}/ia/chat",
					json={"mensagem": texto},
					timeout=30,
				)
				resp2.raise_for_status()
				resposta = resp2.json().get("resposta")
			except requests.RequestException as exc:
				resposta = f"Erro ao enviar audio: {exc}"
				texto = ""
			except Exception as exc:
				resposta = f"Erro ao gravar audio: {exc}"
				texto = ""

			chat_area.config(state="normal")
			if texto:
				chat_area.insert(tk.END, f"Voce (audio): {texto}\n")
			chat_area.insert(tk.END, f"Lion 🦁: {resposta}\n\n")
			chat_area.config(state="disabled")
			chat_area.see(tk.END)

		def alternar_gravacao():
			if gravando:
				parar_gravacao()
				audio_button.config(text="🎤 Iniciar")
			else:
				iniciar_gravacao()
				audio_button.config(text="⏹ Parar")

		tk.Button(botoes_frame, text="📷 Imagem", command=selecionar_imagem).pack(side="left", padx=5)
		audio_button = tk.Button(botoes_frame, text="🎤 Iniciar", command=alternar_gravacao)
		audio_button.pack(side="left", padx=5)
		tk.Button(chat_window, text="Enviar", command=enviar_mensagem).pack(pady=5)

	def enviar_imagem(self):
		caminho = filedialog.askopenfilename(
			title="Selecione uma imagem",
			filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp")],
		)
		if not caminho:
			return

		try:
			with open(caminho, "rb") as arquivo:
				files = {"file": arquivo}
				resp = requests.post(f"{API_URL}/ia/imagem", files=files, timeout=30)
				resp.raise_for_status()
				dados = resp.json()
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Falha ao enviar imagem: {exc}")
			return

		messagebox.showinfo("Resposta da IA", dados.get("resposta", "Sem resposta"))

	def gravar_audio(self):
		if not AUDIO_LIBS_OK:
			messagebox.showwarning(
				"Aviso",
				"Bibliotecas de audio nao instaladas. Instale sounddevice e scipy.",
			)
			return

		try:
			fs = 44100
			segundos = 5
			audio = sd.rec(int(segundos * fs), samplerate=fs, channels=1)
			sd.wait()
			write("audio.wav", fs, audio)
			messagebox.showinfo("Audio", "Gravacao concluida: audio.wav")
		except Exception as exc:
			messagebox.showerror("Erro", f"Falha ao gravar audio: {exc}")

	def enviar_audio(self):
		try:
			with open("audio.wav", "rb") as arquivo:
				files = {"file": arquivo}
				resp = requests.post(f"{API_URL}/ia/audio", files=files, timeout=30)
				resp.raise_for_status()
				dados = resp.json()
		except FileNotFoundError:
			messagebox.showwarning("Aviso", "Arquivo audio.wav nao encontrado. Grave o audio primeiro.")
			return
		except requests.RequestException as exc:
			messagebox.showerror("Erro", f"Falha ao enviar audio: {exc}")
			return

		messagebox.showinfo("Transcricao", dados.get("texto", "Sem texto"))


if __name__ == "__main__":
	root = tk.Tk()
	app = ControleEventosApp(root)
	root.mainloop()
