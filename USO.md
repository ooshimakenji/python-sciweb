# Como usar o SEMASA Bot

## Pré-requisitos

- VPN conectada (sistema só responde na rede interna)
- Python instalado
- Ambiente configurado (ver seção Instalação)

---

## Instalação (primeira vez)

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
# ou: .venv\Scripts\activate       # CMD/PowerShell
pip install -r requirements.txt
playwright install chromium
```

---

## Fluxo de uso

### 1. Preparar a planilha

Abrir (ou criar) `dados.xlsx` com as colunas exatas:

| A | B | C |
|---|---|---|
| Sequencial AS | Data de execução | Status |
| 2026019539 | 26/02/2026 | _(vazio)_ |

- **Sequencial AS**: número da OS
- **Data de execução**: data no formato `dd/mm/aaaa`
- **Status**: deixar em **branco** — o bot preenche automaticamente

O bot processa apenas as linhas com Status vazio. Linhas já com status são ignoradas.

### 2. Configurar o .env

Editar `.env` antes de rodar. Campos mais usados:

```env
SEMASA_USUARIO=SEU_USUARIO
SEMASA_SENHA=SUA_SENHA
SEMASA_EXCEL=dados.xlsx           # nome da planilha
SEMASA_PARECER_FIXO=repavimentação realizado conforme demanda
SEMASA_HEADLESS=true              # false para ver o browser
SEMASA_TIMEOUT_MS=15000           # aumentar se houver muitos timeouts
```

### 3. Rodar

```bash
source .venv/Scripts/activate
python semasa_bot.py
```

O bot salva o progresso a cada 5 OS processadas. Se interromper no meio, basta rodar de novo — ele continua do ponto onde parou (linhas com Status vazio).

---

## Resultados possíveis por OS

| Status | Significado |
|--------|-------------|
| `SUCESSO` | OS encerrada com sucesso |
| `PULADO: EXECUTADO` | OS já estava executada no sistema |
| `PULADO: CANCELADO` | OS cancelada, ignorada |
| `ERRO: ...` | Falha — ver seção abaixo |

---

## Reprocessar OS com erro

Após a execução, as OS com `ERRO` na planilha precisam ser re-tentadas:

**Opção 1 — via script Python:**
```python
import pandas as pd
df = pd.read_excel('dados.xlsx')
df.loc[df['Status'].str.startswith('ERRO', na=False), 'Status'] = ''
df.to_excel('dados.xlsx', index=False, engine='openpyxl')
```

**Opção 2 — manualmente:** abrir `dados.xlsx` e apagar o conteúdo da coluna Status nas linhas com ERRO.

Depois rodar o bot novamente — ele só processa as linhas com Status vazio.

---

## Investigar erros

### Logs
```
logs/semasa_bot.log
```
Buscar `ERROR` ou `WARNING` para ver qual sequencial falhou e o motivo.

### Screenshots
```
logs/screenshots/<sequencial>_<timestamp>.png
```
Salvo automaticamente para toda OS com ERRO. Mostra o estado exato da tela no momento da falha.

### Erros comuns

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Timeout após ZebraDialog | Servidor lento no save | Rodar novamente — normalmente resolve |
| `net::ERR_ABORTED` | VPN caiu | Reconectar VPN e rodar de novo |
| Timeout em `Sequencial AS` | Página não carregou | Aumentar `SEMASA_TIMEOUT_MS` para 30000 |
| Página de login visível | Sessão expirou | O bot faz relogin automático; se persistir, verificar VPN |
| Status `DESCONHECIDO` | Nova situação no sistema | Chamar o Claude para adicionar o novo status |

### Ver o browser para debug
```env
SEMASA_HEADLESS=false
```
Setar no `.env`, rodar o bot e observar o browser em tempo real. Reverter para `true` depois.

---

## Logs e arquivos gerados

| Arquivo/Pasta | Descrição |
|---|---|
| `logs/semasa_bot.log` | Log completo de execução |
| `logs/screenshots/` | Screenshots de erros |
| `dados.xlsx` | Planilha atualizada com status |
