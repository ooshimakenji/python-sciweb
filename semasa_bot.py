"""Automação SEMASA com Python + Playwright + Pandas.

Fluxo principal:
1. Lê a planilha Excel e seleciona linhas com Status vazio.
2. Faz login uma única vez e mantém o contexto ativo.
3. Para cada linha pendente, busca protocolo, preenche parecer/data e salva.
4. Atualiza a coluna Status com "OK" ou "Erro: ...".
5. Salva incrementalmente a cada N operações.

Ajuste os seletores em `selectors` após mapear com `playwright codegen`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


@dataclass(frozen=True)
class BotConfig:
    excel_path: Path
    login_url: str
    busca_url: str
    username: str
    password: str
    headless: bool = False
    save_every: int = 5
    timeout_ms: int = 15_000


selectors: dict[str, str] = {
    # Login
    "usuario": "#usuario",
    "senha": "#senha",
    "botao_login": "button[type='submit']",
    # Tela de protocolo
    "campo_protocolo": "#protocolo",
    "botao_buscar": "#buscar",
    "campo_parecer": "#parecer",
    "campo_data": "#data",
    "botao_salvar": "#salvar",
    "toast_sucesso": ".toast-success",
    "botao_limpar": "#limpar",
}


class SemasaBot:
    def __init__(self, config: BotConfig):
        self.config = config

    def _load_planilha(self) -> pd.DataFrame:
        df = pd.read_excel(self.config.excel_path, engine="openpyxl")

        required_cols = ["Protocolo", "Parecer", "Data", "Status"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

        df["Status"] = df["Status"].fillna("")
        return df

    def _save_planilha(self, df: pd.DataFrame) -> None:
        df.to_excel(self.config.excel_path, index=False, engine="openpyxl")

    def _login(self, page: Page) -> None:
        page.goto(self.config.login_url)
        page.fill(selectors["usuario"], self.config.username)
        page.fill(selectors["senha"], self.config.password)
        page.click(selectors["botao_login"])
        page.wait_for_url("**", timeout=self.config.timeout_ms)

    def _limpar_formulario(self, page: Page) -> None:
        if page.locator(selectors["botao_limpar"]).count() > 0:
            page.click(selectors["botao_limpar"])

    def _processar_linha(self, page: Page, row: pd.Series) -> str:
        protocolo = str(row["Protocolo"]).strip()
        parecer = str(row["Parecer"]).strip()

        data_val = row["Data"]
        if pd.isna(data_val):
            data_formatada = datetime.today().strftime("%d/%m/%Y")
        elif isinstance(data_val, datetime):
            data_formatada = data_val.strftime("%d/%m/%Y")
        else:
            data_formatada = str(data_val).strip()

        page.goto(self.config.busca_url)
        page.fill(selectors["campo_protocolo"], protocolo)
        page.click(selectors["botao_buscar"])

        # Campos podem aparecer após carregamento assíncrono.
        page.wait_for_selector(selectors["campo_parecer"], timeout=self.config.timeout_ms)
        page.wait_for_selector(selectors["campo_data"], timeout=self.config.timeout_ms)

        page.fill(selectors["campo_parecer"], parecer)
        page.fill(selectors["campo_data"], data_formatada)

        page.click(selectors["botao_salvar"])
        page.wait_for_selector(selectors["toast_sucesso"], timeout=self.config.timeout_ms)
        return "OK"

    def run(self) -> None:
        df = self._load_planilha()
        pendentes = df[df["Status"].str.strip() == ""]

        if pendentes.empty:
            print("Nenhuma linha pendente encontrada.")
            return

        processadas_desde_ultimo_save = 0

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.config.headless)
            context = browser.new_context()
            page = context.new_page()

            self._login(page)

            for idx, row in pendentes.iterrows():
                try:
                    status = self._processar_linha(page, row)
                except PlaywrightTimeoutError as exc:
                    status = f"Erro: timeout - {exc}"
                    self._limpar_formulario(page)
                except Exception as exc:  # noqa: BLE001
                    status = f"Erro: {exc}"
                    self._limpar_formulario(page)

                df.at[idx, "Status"] = status
                processadas_desde_ultimo_save += 1

                if processadas_desde_ultimo_save >= self.config.save_every:
                    self._save_planilha(df)
                    processadas_desde_ultimo_save = 0

            self._save_planilha(df)
            context.close()
            browser.close()


if __name__ == "__main__":
    config = BotConfig(
        excel_path=Path("dados.xlsx"),
        login_url="https://sistema.semasa.exemplo/login",
        busca_url="https://sistema.semasa.exemplo/protocolos",
        username="SEU_USUARIO",
        password="SUA_SENHA",
        headless=False,  # Troque para True após validar fluxo.
        save_every=5,
    )

    SemasaBot(config).run()
