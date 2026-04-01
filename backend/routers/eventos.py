from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
	from ..database import (
		adicionar_movimentacao_db,
		listar_eventos_db,
		listar_historico_evento_db,
		obter_resumo_evento_db,
	)
except ImportError:
	from database import (
		adicionar_movimentacao_db,
		listar_eventos_db,
		listar_historico_evento_db,
		obter_resumo_evento_db,
	)

router = APIRouter()


class MovimentacaoPayload(BaseModel):
	id_evento: int
	tipo: str
	valor: float
	descricao: str


@router.get("/eventos")
def listar_eventos():
	try:
		eventos = listar_eventos_db()
	except Exception as exc:
		raise HTTPException(status_code=503, detail=f"Falha ao carregar eventos: {exc}") from exc

	return eventos


@router.get("/eventos/{id_evento}")
def detalhe_evento(id_evento: int):
	try:
		dados = obter_resumo_evento_db(id_evento)
	except Exception as exc:
		raise HTTPException(status_code=503, detail=f"Falha ao carregar os detalhes do evento: {exc}") from exc

	entrada = 0.0
	saida = 0.0

	for dado in dados:
		if dado["tipo"] == "entrada":
			entrada = float(dado["total"])
		else:
			saida = float(dado["total"])

	return {
		"entrada": entrada,
		"saida": saida,
		"saldo": entrada - saida,
	}


@router.get("/eventos/{id_evento}/historico")
def historico_evento(id_evento: int):
	try:
		dados = listar_historico_evento_db(id_evento)
	except Exception as exc:
		raise HTTPException(status_code=503, detail=f"Falha ao carregar historico: {exc}") from exc

	return dados


@router.post("/movimentacao")
def adicionar_movimentacao(dados: MovimentacaoPayload):
	if dados.tipo not in {"entrada", "saida"}:
		raise HTTPException(status_code=400, detail="O campo tipo deve ser 'entrada' ou 'saida'.")

	try:
		adicionar_movimentacao_db(dados.id_evento, dados.tipo, dados.valor, dados.descricao)
	except Exception as exc:
		raise HTTPException(status_code=503, detail=f"Falha ao salvar movimentacao: {exc}") from exc

	return {"msg": "ok"}
