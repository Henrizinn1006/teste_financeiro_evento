# Protótipo Financeiro — Controle de Eventos

Sistema de controle financeiro desenvolvido para gestão de eventos, com foco em organização de entradas e saídas, acompanhamento de lucro por evento e automação de registros através de inteligência artificial.

O projeto tem como objetivo resolver um problema real: permitir que empresas de eventos tenham clareza sobre seus ganhos, custos e resultados financeiros de forma simples e eficiente.

## Objetivo

Fornecer uma ferramenta prática para controle financeiro por evento, permitindo que o usuário registre movimentações manualmente ou através de interações com um assistente inteligente.

## Funcionalidades

- Criação e gerenciamento de eventos
- Registro de entradas (receitas)
- Registro de saídas (despesas)
- Edição e exclusão de movimentações
- Visualização de saldo por evento
- Controle financeiro separado por categoria
- Integração com IA para registro automatizado de movimentações
- Interface simples e intuitiva

## Tecnologias utilizadas

**Backend:**
- Python
- FastAPI

**Frontend:**
- Flutter (em desenvolvimento)

**Banco de dados:**
- MySQL

**Outros:**
- APIs REST
- Integração com inteligência artificial (planejado)

## Estrutura do sistema

O sistema é dividido em três camadas principais:

- **Backend:** responsável pela lógica de negócio, validações e comunicação com o banco de dados
- **Banco de dados:** armazenamento das informações de eventos e movimentações
- **Interface:** interação com o usuário (desktop/mobile)

## Estrutura de diretórios (exemplo)

```
backend/
  app/
  routers/
  models/
  schemas/
  services/
  main.py

frontend/
  lib/
  screens/
  widgets/

database/
  models.sql
```

## Como executar o projeto

### Backend

1) Criar ambiente virtual:
```
python -m venv venv
```

2) Ativar ambiente:
```
venv\Scripts\activate
```

3) Instalar dependências:
```
pip install -r requirements.txt
```

4) Executar servidor:
```
uvicorn main --reload
```

5) Acessar documentação:
```
http://localhost:8000/docs
```

## Modelo de funcionamento

O sistema trabalha com eventos como entidades principais. Cada evento possui:

- Nome
- Data
- Cliente
- Lista de movimentações financeiras

Cada movimentação pode ser:

- Entrada: valores recebidos
- Saída: custos ou despesas

O saldo do evento é calculado automaticamente com base nas movimentações registradas.

## Integração com Inteligência Artificial

O sistema prevê uma funcionalidade onde o usuário poderá registrar movimentações através de mensagens, como:

- "Recebi 4000 reais do evento 2"
- "Gastei 500 com decoração no evento 1"

A IA será responsável por interpretar essas informações e registrar automaticamente no sistema.

## Status do projeto

Protótipo em desenvolvimento.

Funcionalidades principais em construção, com foco inicial no backend e estrutura de dados.

## Possíveis melhorias

- Dashboard com gráficos financeiros
- Integração com WhatsApp para entrada de dados
- Upload de comprovantes (imagem ou PDF)
- Relatórios por período
- Exportação de dados
- Sistema de autenticação de usuários

## Autor

Henrique Tavares

Desenvolvedor em formação focado em backend e desenvolvimento de sistemas completos.

## Licença

Projeto desenvolvido para fins de estudo e uso interno.
