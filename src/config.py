from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    excel_path: Path
    login_url: str
    servico_url: str
    usuario: str
    senha: str
    headless: bool
    save_every: int
    timeout_ms: int
    retries: int
    success_message: str
    fixed_parecer: str
    log_file: Path
    screenshot_dir: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Robô SEMASA (Playwright + Pandas)")
    parser.add_argument("--excel", default="dados.xlsx", help="Caminho da planilha")
    parser.add_argument("--login-url", default="http://sciweb.semasaitajai.com.br:5050/")
    parser.add_argument(
        "--servico-url",
        default="http://sciweb.semasaitajai.com.br:5050/Servicos/Servico?aba=1&NrSequencial=2025146360",
    )
    parser.add_argument("--usuario", default=os.getenv("SEMASA_USUARIO", ""))
    parser.add_argument("--senha", default=os.getenv("SEMASA_SENHA", ""))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--save-every", type=int, default=5)
    parser.add_argument("--timeout-ms", type=int, default=15_000)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--success-message", default="Dados salvos com sucesso!")
    parser.add_argument("--parecer-fixo", default="Serviço Executado conforme demanda")
    parser.add_argument("--log-file", default="logs/semasa_bot.log")
    parser.add_argument("--screenshot-dir", default="logs/screenshots")
    return parser


def load_config() -> AppConfig:
    load_dotenv()
    args = build_parser().parse_args()

    usuario = args.usuario or os.getenv("SEMASA_USUARIO", "")
    senha = args.senha or os.getenv("SEMASA_SENHA", "")

    if not usuario or not senha:
        raise ValueError("Credenciais ausentes. Defina no .env ou via --usuario/--senha.")

    return AppConfig(
        excel_path=Path(args.excel),
        login_url=args.login_url,
        servico_url=args.servico_url,
        usuario=usuario,
        senha=senha,
        headless=args.headless,
        save_every=max(1, args.save_every),
        timeout_ms=max(1000, args.timeout_ms),
        retries=max(1, args.retries),
        success_message=args.success_message,
        fixed_parecer=args.parecer_fixo,
        log_file=Path(args.log_file),
        screenshot_dir=Path(args.screenshot_dir),
    )
