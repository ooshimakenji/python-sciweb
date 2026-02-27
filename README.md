# Robô SEMASA (Playwright + Pandas)

Automação para fluxo único do SCIWEB:
- login 1 vez,
- busca `Sequencial AS`,
- identifica `CANCELADO`/`EXECUTADO`/`PROGRAMADO`,
- se programado abre encerramento, preenche parecer fixo e data da planilha,
- clica em `Encerrar`, valida mensagem de sucesso,
- grava resultado no Excel e continua o loop sem novo login.

## Estrutura

- `main.py`: orquestração geral
- `src/config.py`: carregamento `.env` e argumentos
- `src/excel_repo.py`: leitura/escrita da planilha
- `src/bot.py`: automação Playwright
- `semasa_bot.py`: entrypoint simples
- `run_semasa_bot.bat`: execução manual no Windows

## 1) Instalação (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## 2) Credenciais em `.env`

1. Copie `.env.example` para `.env`.
2. Ajuste:

```dotenv
SEMASA_USUARIO=SEU_USUARIO
SEMASA_SENHA=SUA_SENHA
```

## 3) Planilha esperada

Colunas obrigatórias:

| Coluna | Nome |
|---|---|
| A | `Sequencial AS` |
| B | `Data de execução` |
| C | `Status` |

### Como funciona o `Status`

A coluna `Status` é o checkpoint da automação:
- vazio: pendente (será processado)
- `SUCESSO`: encerrado com sucesso
- `CANCELADO`: já cancelado no sistema
- `EXECUTADO`: já executado no sistema
- `ERRO: ...`: falha e motivo

Assim você pode reexecutar o bot sem reprocessar o que já foi tratado.

## 4) Execução

### Opção A: `.bat`

```bat
run_semasa_bot.bat
```

### Opção B: PowerShell

```powershell
python semasa_bot.py --excel dados.xlsx
```

Parâmetros úteis:
- `--headless` executa sem abrir navegador
- `--save-every 5` salva incrementalmente
- `--retries 2` tentativas por linha
- `--servico-url` URL fixa de serviço (já vem preenchida)
- `--success-message "Dados salvos com sucesso!"`

## 5) Logs e evidências

- Log: `logs/semasa_bot.log`
- Screenshots de erro: `logs/screenshots/*.png`
- Progresso também aparece no terminal.

## 6) Regras implementadas conforme alinhamento

- Sem relogin por linha (loop contínuo).
- Relogin automático se sessão expirar.
- Retry de 2 tentativas por linha (configurável).
- Data obrigatória no formato `dd/mm/aaaa`; se vazia/inválida, registra erro e pula.
- Parecer fixo: `Serviço Executado conforme demanda` (configurável via `--parecer-fixo`).
