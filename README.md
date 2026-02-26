# Roadmap + Starter Kit: Automação SEMASA

Este repositório traz uma base funcional para automatizar o preenchimento de protocolos no SEMASA usando **Python + Playwright + Pandas**.

## 1) Preparação do ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Bibliotecas principais:
- `playwright`: navegação e interação com a aplicação web.
- `pandas`: leitura/manipulação da planilha.
- `openpyxl`: engine de leitura/escrita `.xlsx`.

## 2) Engenharia reversa (o pulo do gato)

Use o codegen para mapear seletores reais:

```bash
playwright codegen https://SEU-SISTEMA/login
```

Depois, substitua os valores do dicionário `selectors` no arquivo `semasa_bot.py`.

Checklist de mapeamento:
- Campo usuário/senha e botão de login.
- Campo de protocolo e botão de busca.
- Campo de parecer.
- Campo de data.
- Botão salvar.
- Alerta/toast de sucesso.
- Botão limpar formulário (fallback em erro).

## 3) Lógica de dados (pandas)

A planilha precisa ter as colunas abaixo:

| Coluna | Nome esperado |
|---|---|
| A | `Protocolo` |
| B | `Parecer` |
| C | `Data` |
| D | `Status` |

O robô processa **somente** linhas com `Status` vazio, para permitir retomada após queda de conexão/energia.

## 4) Desenvolvimento do robô

Arquivo principal: `semasa_bot.py`

Recursos implementados:
- Login único e sessão mantida em `context` do Playwright.
- Loop por linhas pendentes da planilha.
- `try/except` por linha para não interromper lote inteiro.
- Escrita de `OK` ou `Erro: ...` na coluna `Status`.
- Salvamento incremental a cada `save_every` itens.

Execução:

```bash
python semasa_bot.py
```

## 5) Estabilidade e finalização

- Durante homologação: use `headless=False`.
- Em produção: altere para `headless=True`.
- Ajuste `save_every` para `5` ou `10` conforme volume e risco.

## Valor para currículo

- Stack moderna de automação (Playwright).
- Arquitetura resiliente (tratamento de exceções + retomada por status).
- Integração web + dados (`pandas`/`openpyxl`).
