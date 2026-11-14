"""Leitura da fonte original, sem qualquer escrita no arquivo."""
from pathlib import Path
import pandas as pd
from .config import DATASET

REQUIRED = ['Mes_Ano_Data', 'Data_Coleta', 'Estab', 'Produto', 'Marca', 'Preco', 'Quantidade', 'PPK']

def load_data(path: Path = DATASET) -> pd.DataFrame:
    """Lê a única aba da fonte e valida suas colunas obrigatórias."""
    path = Path(path)
    frame = pd.read_excel(path) if path.suffix.lower() in ('.xlsx', '.xls') else pd.read_csv(path)
    missing = set(REQUIRED) - set(frame.columns)
    if missing:
        raise ValueError(f'Colunas ausentes: {sorted(missing)}')
    return frame[REQUIRED].copy()
