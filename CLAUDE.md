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

Status possíveis após execução: `SUCESSO`, `CANCELADO`, `EXECUTADO`, `ERRO: ...`

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

@CLAUDE.soul
