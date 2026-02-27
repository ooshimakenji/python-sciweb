from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError, expect

from src.config import AppConfig
from src.excel_repo import RowData


class SemasaBot:
    def __init__(self, config: AppConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def _login(self, page: Page) -> None:
        self.logger.info("Realizando login.")
        page.goto(self.config.login_url)
        page.locator("#NmContaUsuario").fill(self.config.usuario)
        page.locator("#CdHashPwd").fill(self.config.senha)
        page.locator("#CdHashPwd").press("Enter")
        # Aguarda o campo de login desaparecer — confirma redirect pós-login
        page.locator("#NmContaUsuario").wait_for(state="hidden", timeout=self.config.timeout_ms)

    def _abrir_tela_servico(self, page: Page) -> None:
        page.goto(self.config.servico_url)
        # Aguarda o campo de busca estar disponível — página carregada
        page.get_by_role("textbox", name="Sequencial AS").wait_for(state="visible", timeout=self.config.timeout_ms)

    def _capturar_screenshot(self, page: Page, sequencial: str) -> Path:
        self.config.screenshot_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.config.screenshot_dir / f"{sequencial}_{stamp}.png"
        page.screenshot(path=str(path), full_page=True)
        return path

    def _aguardar_status(self, page: Page) -> None:
        # Aguarda qualquer célula de status aparecer após a busca
        locator = (
            page.get_by_role("cell", name="CANCELADO")
            .or_(page.get_by_role("cell", name="EXECUTADO"))
            .or_(page.get_by_role("cell", name="PROGRAMADO"))
        )
        locator.first.wait_for(state="visible", timeout=self.config.timeout_ms)

    def _status_da_ordem(self, page: Page) -> str:
        if page.get_by_role("cell", name="CANCELADO").first.is_visible():
            return "CANCELADO"
        if page.get_by_role("cell", name="EXECUTADO").first.is_visible():
            return "EXECUTADO"
        if page.get_by_role("cell", name="PROGRAMADO").first.is_visible():
            return "PROGRAMADO"
        return "DESCONHECIDO"

    def _encerrar_sequencial(self, page: Page, row: RowData) -> str:
        if not row.data_execucao:
            return "ERRO: Data de execução vazia/inválida"

        # Sempre parte da tela de serviço para garantir estado consistente
        self._abrir_tela_servico(page)

        seq = page.get_by_role("textbox", name="Sequencial AS")
        seq.click()
        seq.fill(row.sequencial_as)
        seq.press("Enter")

        # Aguarda o sequencial correto aparecer na tabela — evita ler resultado de busca anterior
        page.get_by_role("cell", name=row.sequencial_as, exact=True).wait_for(state="visible", timeout=self.config.timeout_ms)
        self._aguardar_status(page)

        status_atual = self._status_da_ordem(page)
        if status_atual in {"CANCELADO", "EXECUTADO"}:
            return f"PULADO: {status_atual}"
        if status_atual == "DESCONHECIDO":
            return "ERRO: status não identificado"

        # Seleciona a linha PROGRAMADO para habilitar os botões de ação
        page.get_by_role("cell", name="PROGRAMADO").first.click()

        encerramento_btn = page.get_by_role("button", name="Encerramento")
        expect(encerramento_btn).to_be_enabled(timeout=self.config.timeout_ms)
        encerramento_btn.click()
        parecer = page.locator("#DsParecer")
        parecer.click()
        parecer.fill(self.config.fixed_parecer)

        data_exec = page.locator("#DtHoraInicioExecucao")
        data_exec.click()
        data_exec.press("ControlOrMeta+a")
        data_exec.fill(row.data_execucao)

        page.locator("#salvar").click()

        sucesso = page.get_by_text(self.config.success_message, exact=False).first
        sucesso.wait_for(state="visible", timeout=self.config.timeout_ms)
        return "SUCESSO"

    def _processar_com_retry(self, page: Page, row: RowData) -> str:
        ultimo_erro = ""
        for tentativa in range(1, self.config.retries + 1):
            try:
                return self._encerrar_sequencial(page, row)
            except PlaywrightTimeoutError as exc:
                ultimo_erro = f"ERRO: timeout tentativa {tentativa} - {exc}"
            except Exception as exc:  # noqa: BLE001
                ultimo_erro = f"ERRO: tentativa {tentativa} - {exc}"

            self.logger.warning("Falha sequencial=%s tentativa=%s: %s", row.sequencial_as, tentativa, ultimo_erro)

        return ultimo_erro or "ERRO: falha desconhecida"

    def run(self, playwright: Playwright, rows: list[RowData], save_callback) -> None:
        browser = playwright.chromium.launch(headless=self.config.headless)
        context: BrowserContext = browser.new_context()
        page = context.new_page()

        self._login(page)
        self._abrir_tela_servico(page)

        for i, row in enumerate(rows, start=1):
            self.logger.info("Processando %s/%s - sequencial=%s", i, len(rows), row.sequencial_as)

            try:
                status = self._processar_com_retry(page, row)
                if status.startswith("ERRO"):
                    screenshot_path = self._capturar_screenshot(page, row.sequencial_as)
                    self.logger.error("Erro no sequencial=%s, screenshot=%s", row.sequencial_as, screenshot_path)
                else:
                    self.logger.info("Resultado sequencial=%s: %s", row.sequencial_as, status)

            except Exception as exc:  # noqa: BLE001
                screenshot_path = self._capturar_screenshot(page, row.sequencial_as)
                status = f"ERRO: falha crítica - {exc}"
                self.logger.exception("Falha crítica no sequencial=%s, screenshot=%s", row.sequencial_as, screenshot_path)

            save_callback(row.index, status)

            # Sessão expirada: tenta relogin 1x quando cair para login
            if page.locator("#NmContaUsuario").first.count() > 0:
                self.logger.warning("Sessão possivelmente expirada. Tentando relogin automático.")
                self._login(page)
                self._abrir_tela_servico(page)

        context.close()
        browser.close()
