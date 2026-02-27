from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright

from src.bot import SemasaBot
from src.config import load_config
from src.excel_repo import ExcelRepo


def setup_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("semasa_bot")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def main() -> None:
    config = load_config()
    config.log_file.parent.mkdir(parents=True, exist_ok=True)
    config.screenshot_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(str(config.log_file))
    repo = ExcelRepo(config.excel_path)
    rows = repo.get_pending_rows()

    if not rows:
        logger.info("Nenhuma linha pendente com Status vazio.")
        return

    bot = SemasaBot(config, logger)
    contador = {"desde_ultimo_save": 0}
    resumo: dict[str, int] = {}

    def on_row_done(row_index: int, status: str) -> None:
        repo.update_status(row_index, status)
        chave = status if not status.startswith("ERRO") else "ERRO"
        resumo[chave] = resumo.get(chave, 0) + 1
        contador["desde_ultimo_save"] += 1
        if contador["desde_ultimo_save"] >= config.save_every:
            repo.save()
            contador["desde_ultimo_save"] = 0

    with sync_playwright() as playwright:
        bot.run(playwright, rows, on_row_done)

    repo.save()

    logger.info("Execução finalizada. Resumo:")
    for status, total in sorted(resumo.items()):
        logger.info("  %-25s %d", status, total)


if __name__ == "__main__":
    main()
