import json
import base64
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, Request
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

try:
	from ..database import adicionar_movimentacao_db
except ImportError:
	from database import adicionar_movimentacao_db

try:
	from openai import OpenAI
	api_key = os.getenv("OPENAI_API_KEY", "")
	client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
	IA_DISPONIVEL = bool(api_key)
except Exception:
	client = None
	IA_DISPONIVEL = False

router = APIRouter()


class ChatPayload(BaseModel):
	mensagem: str


class MultimodalPayload(BaseModel):
	mensagem: str = ""
	imagem: str
	mime_type: Optional[str] = None
	filename: Optional[str] = None


class AudioPayload(BaseModel):
	audio: str
	mime_type: Optional[str] = None
	filename: Optional[str] = None


def _infer_audio_suffix(mime_type: Optional[str], filename: Optional[str]) -> str:
	if filename:
		suffix = Path(filename).suffix
		if suffix:
			return suffix

	if not mime_type:
		return ".wav"

	if "ogg" in mime_type:
		return ".ogg"
	if "mpeg" in mime_type or "mp3" in mime_type:
		return ".mp3"
	if "wav" in mime_type:
		return ".wav"

	return ".wav"


def executar_acoes(resposta_ia):
	data = json.loads(resposta_ia)

	acoes = data.get("acoes")
	if not acoes:
		return "Não identifiquei movimentações."

	respostas = []
	for acao in acoes:
		adicionar_movimentacao_db(
			acao["evento"],
			acao["tipo"],
			acao["valor"],
			acao["descricao"],
		)
		respostas.append(
			f"{acao['tipo']} de R${acao['valor']} no evento {acao['evento']}"
		)

	return "Registrado:\n" + "\n".join(respostas)


@router.post("/ia/chat")
def chat_ia(dados: ChatPayload):
	if not IA_DISPONIVEL or client is None:
		return {
			"resposta": "IA nao configurada. Defina a chave OpenAI em routers/ia.py"
		}

	mensagem = dados.mensagem

	prompt = f"""
Você é a IA Lion 🦁.

Analise a mensagem e extraia TODAS as movimentações financeiras.

Responda APENAS em JSON válido.

Formato:
{{
  "acoes": [
    {{
      "tipo": "entrada" ou "saida",
      "valor": número,
      "evento": número,
      "descricao": "texto"
    }}
  ]
}}

Se não houver movimentações, responda:
{{ "acoes": [] }}

Mensagem:
{mensagem}
"""

	try:
		resposta = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{"role": "user", "content": prompt}
			]
		)

		conteudo = resposta.choices[0].message.content or ""
		if not conteudo:
			return {"resposta": "Resposta vazia da IA"}

		try:
			resposta_final = executar_acoes(conteudo)
		except Exception:
			resposta_final = "Erro ao processar comando"

		return {"resposta": resposta_final}
	except Exception as exc:
		return {
			"resposta": f"Erro ao conectar com OpenAI: {str(exc)}"
		}


@router.post("/ia/imagem")
async def analisar_imagem(
	file: UploadFile = File(...),
	evento: int = Form(...),
	legenda: str = Form(""),
):
	if not IA_DISPONIVEL or client is None:
		return {"resposta": "IA nao configurada."}

	imagem_bytes = await file.read()
	imagem_base64 = base64.b64encode(imagem_bytes).decode("utf-8")
	mime_type = file.content_type or "image/jpeg"

	prompt = f"""
Você é a IA Lion 🦁.

Analise a nota fiscal e retorne APENAS JSON:

{{
	"tipo": "saida",
	"valor": número,
	"descricao": "resumo da compra + {legenda}"
}}
"""

	try:
		response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{
					"role": "user",
					"content": [
						{
							"type": "text",
							"text": prompt,
						},
						{
							"type": "image_url",
							"image_url": {
								"url": f"data:{mime_type};base64,{imagem_base64}"
							},
						},
					],
				}
			],
		)
		conteudo = response.choices[0].message.content or ""
		if not conteudo:
			return {"resposta": "Resposta vazia da IA"}
		data = json.loads(conteudo)

		adicionar_movimentacao_db(
			evento,
			data["tipo"],
			data["valor"],
			data["descricao"],
		)

		return {"msg": "Imagem processada e salva"}
	except Exception as exc:
		return {"resposta": f"Erro ao analisar imagem: {exc}"}


@router.post("/ia/audio")
async def transcrever_audio(request: Request, file: UploadFile = File(None)):
	if not IA_DISPONIVEL or client is None:
		return {"texto": "IA nao configurada."}

	audio_bytes = b""
	mime_type = None
	filename = None

	if request.headers.get("content-type", "").startswith("application/json"):
		dados = await request.json()
		payload = AudioPayload(**dados)
		try:
			audio_bytes = base64.b64decode(payload.audio)
		except Exception:
			return {"texto": "Audio base64 invalido."}
		mime_type = payload.mime_type
		filename = payload.filename
	else:
		if file is None:
			return {"texto": "Arquivo de audio nao enviado."}
		filename = file.filename
		mime_type = file.content_type
		audio_bytes = await file.read()

	temp_path = None
	try:
		suffix = _infer_audio_suffix(mime_type, filename)
		with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
			temp_file.write(audio_bytes)
			temp_path = temp_file.name

		with open(temp_path, "rb") as audio_file:
			transcription = client.audio.transcriptions.create(
				model="gpt-4o-mini-transcribe",
				file=audio_file,
			)

		return {"texto": transcription.text}
	except Exception as exc:
		return {"texto": f"Erro ao transcrever audio: {exc}"}
	finally:
		if temp_path:
			try:
				Path(temp_path).unlink(missing_ok=True)
			except Exception:
				pass


@router.post("/ia/multimodal")
async def multimodal(
	request: Request,
	mensagem: str = Form(""),
	files: list[UploadFile] = File(default=[]),
):
	if not IA_DISPONIVEL or client is None:
		return {"resposta": "IA nao configurada."}

	imagens = []

	if request.headers.get("content-type", "").startswith("application/json"):
		dados = await request.json()
		payload = MultimodalPayload(**dados)
		mensagem = payload.mensagem
		mime_type = payload.mime_type or "image/jpeg"
		if not payload.imagem:
			return {"resposta": "Imagem base64 nao enviada."}
		imagens.append(
			{
				"type": "image_url",
				"image_url": {
					"url": f"data:{mime_type};base64,{payload.imagem}"
				},
			}
		)
	else:
		for file in files:
			conteudo = await file.read()
			base64_img = base64.b64encode(conteudo).decode("utf-8")
			imagens.append(
				{
					"type": "image_url",
					"image_url": {
						"url": f"data:image/jpeg;base64,{base64_img}"
					},
				}
			)

	prompt = f"""
Você é a IA Lion 🦁.

Analise o texto e as imagens.

IMPORTANTE:
- Responda APENAS JSON válido
- NÃO escreva texto fora do JSON

Formato:
{{
  "acoes": [
    {{
      "tipo": "saida",
      "valor": número,
      "evento": número,
      "descricao": "detalhe"
    }}
  ]
}}

Se não conseguir identificar, retorne:
{{ "acoes": [] }}

Mensagem:
{mensagem}
"""

	try:
		response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{
					"role": "user",
					"content": [
						{"type": "text", "text": prompt},
						*imagens,
					],
				}
			],
		)

		conteudo = (response.choices[0].message.content or "").strip()
		if not conteudo:
			return {"resposta": "Erro ao interpretar resposta da IA"}
		try:
			data = json.loads(conteudo)
		except Exception:
			print("ERRO IA:", conteudo)
			return {"resposta": "Erro ao interpretar resposta da IA"}

		for acao in data.get("acoes", []):
			adicionar_movimentacao_db(
				acao.get("evento", 1),
				acao["tipo"],
				acao["valor"],
				acao["descricao"],
			)

		return {"resposta": "Tudo processado e salvo 💾"}
	except Exception as exc:
		return {"resposta": f"Erro ao processar multimodal: {exc}"}
