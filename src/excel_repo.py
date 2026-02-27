from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["Sequencial AS", "Data de execução", "Status"]


@dataclass
class RowData:
    index: int
    sequencial_as: str
    data_execucao: str


class ExcelRepo:
    def __init__(self, excel_path: Path):
        self.excel_path = excel_path
        self.df = self._load()

    def _load(self) -> pd.DataFrame:
        df = pd.read_excel(self.excel_path, engine="openpyxl")
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

        df["Status"] = df["Status"].fillna("").astype(str)
        return df

    @staticmethod
    def _formatar_data_excel(valor: object) -> str:
        if pd.isna(valor):
            return ""
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor).strip()
        if not texto:
            return ""
        parsed = pd.to_datetime(texto, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return ""
        return parsed.strftime("%d/%m/%Y")

    def get_pending_rows(self) -> list[RowData]:
        pendentes = self.df[self.df["Status"].str.strip() == ""]
        result: list[RowData] = []
        for idx, row in pendentes.iterrows():
            result.append(
                RowData(
                    index=idx,
                    sequencial_as=str(row["Sequencial AS"]).strip(),
                    data_execucao=self._formatar_data_excel(row["Data de execução"]),
                )
            )
        return result

    def update_status(self, row_index: int, status: str) -> None:
        self.df.at[row_index, "Status"] = status

    def save(self) -> None:
        self.df.to_excel(self.excel_path, index=False, engine="openpyxl")
