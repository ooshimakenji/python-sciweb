from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["Sequencial AS", "Data de execução", "Status"]

# Status que nunca devem ser reprocessados (erros de dado ou conclusão definitiva)
STATUS_DEFINITIVOS = {
    "SUCESSO",
    "PULADO: EXECUTADO",
    "PULADO: CANCELADO",
    "PULADO: PENDENTE",
    "ERRO: Data de execução vazia/inválida",
    "ERRO: status não identificado",
}


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
        def _reprocessavel(status: str) -> bool:
            s = status.strip()
            return s == "" or (s.startswith("ERRO:") and s not in STATUS_DEFINITIVOS)

        pendentes = self.df[self.df["Status"].apply(_reprocessavel)]
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
