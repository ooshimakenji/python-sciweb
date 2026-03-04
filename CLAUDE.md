# SEMASA Bot

Automação Python para encerrar ordens de serviço no portal SCIWEB/SEMASA.

Fluxo: login único → busca por Sequencial AS → identifica status → preenche parecer e data → encerra OS programadas → salva resultado no Excel.

## Stack

- Python 3.x
- Playwright (automação web)
- Pandas + openpyxl (leitura/escrita Excel)
- python-dotenv (.env)

## Estrutura

```
semasa_bot.py    ← entrypoint
main.py          ← orquestração
src/
  config.py      ← .env + CLI args (prioridade: CLI > .env > default)
  excel_repo.py  ← leitura/escrita da planilha
  bot.py         ← automação Playwright
dados.xlsx       ← planilha de entrada
.env             ← credenciais e config (não commitado)
.env.example     ← referência de variáveis disponíveis
```

## Comandos

```bash
# Rodar
python semasa_bot.py

# Instalar
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
playwright install chromium
```

## Planilha (dados.xlsx)

Colunas obrigatórias — nomes exatos, case-sensitive:

| Coluna | Nome             | Formato      |
|--------|------------------|--------------|
| A      | Sequencial AS    | string       |
| B      | Data de execução | dd/mm/aaaa   |
| C      | Status           | vazio = pendente |

Status possíveis após execução:

| Status | Reprocessa? | Descrição |
|--------|-------------|-----------|
| _(vazio)_ | Sim | Pendente — será processado |
| `SUCESSO` | **Não** | Encerrado com sucesso |
| `PULADO: EXECUTADO` | **Não** | Já estava executado no sistema |
| `PULADO: CANCELADO` | **Não** | Já estava cancelado no sistema |
| `PULADO: PENDENTE` | **Não** | Ainda não foi programada — não pode ser encerrada |
| `ERRO: Data de execução vazia/inválida` | **Não** | Dado errado na planilha — corrigir e limpar Status |
| `ERRO: status não identificado` | **Não** | Status novo no sistema — requer ajuste no código |
| `ERRO: timeout tentativa X - ...` | Sim | Falha transitória — reprocessado no próximo run |
| `ERRO: tentativa X - ...` | Sim | Exceção genérica — reprocessado no próximo run |
| `ERRO: falha crítica - ...` | Sim | Exceção inesperada — reprocessado no próximo run |

## Convenções

- Waits baseados em elemento (Playwright), nunca `time.sleep` ou `networkidle`
- `timeout_ms` existe apenas como teto de segurança, não como mecanismo de espera
- Todas as variáveis de ambiente têm prefixo `SEMASA_`
- Prioridade de config: CLI arg > `.env` > default hardcoded
- Dataclass `AppConfig` é frozen (imutável após criação)
- Sem relogin por linha — sessão mantida no loop, relogin só se expirar

## Regras de desenvolvimento

- **Sempre perguntar antes de implementar**, usando múltipla escolha
- Fazer quantas perguntas forem necessárias para entender o cenário real
- Ler o código existente antes de sugerir qualquer mudança
- Não adicionar abstrações, helpers ou features além do que foi pedido
- Não criar novos arquivos sem necessidade clara
- Commits em português

## Debug em modo headless

Com `SEMASA_HEADLESS=true` não é possível ver o browser. Para investigar erros:

**1. Ler o log**
```
logs/semasa_bot.log
```
Buscar pelas linhas `ERROR` ou `WARNING`. O log registra sequencial, tentativa e mensagem de exceção.

**2. Ler os screenshots**
```
logs/screenshots/<sequencial>_<timestamp>.png
```
Screenshot é salvo automaticamente em todo `ERRO`. Usar a ferramenta `Read` do Claude para visualizar a imagem — ela é multimodal e consegue ver o estado da página no momento do erro.

**3. Cruzar com erros conhecidos**

| Sintoma no screenshot / log | Causa provável | Solução |
|---|---|---|
| Página de login visível | Sessão expirou | Aumentar `SEMASA_TIMEOUT_MS` ou verificar VPN |
| Tela de busca vazia | `_abrir_tela_servico` falhou | Verificar `SEMASA_SERVICO_URL` |
| Formulário de encerramento aberto, sem mensagem de sucesso | ZebraDialog não foi detectado | Checar se `.ZebraDialog_Button0` ainda é o seletor correto |
| `net::ERR_ABORTED` | VPN caiu durante navegação | Reconectar VPN e rodar novamente |
| Timeout em `Sequencial AS` textbox | Página não carregou | Aumentar `SEMASA_TIMEOUT_MS` ou verificar URL |
| Status `DESCONHECIDO` | Nova célula de status no sistema | Adicionar novo status em `_status_da_ordem` e `_aguardar_status` |

**4. Rodar headful temporariamente**

Para um debug mais profundo, setar `SEMASA_HEADLESS=false` no `.env`, rodar o bot e observar o browser.

@CLAUDE.soul
