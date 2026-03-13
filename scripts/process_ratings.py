"""
Processa e cruza os dados de ratings (Entregável 1) e do Brasil no Oscar (Entregável 2).
Gera os CSVs finais em data/processed/.
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MANUAL_DIR = BASE_DIR / "data" / "manual"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def process_ratings():
    """Processa o CSV de ratings e calcula métricas de divergência."""
    df = pd.read_csv(MANUAL_DIR / "ratings.csv")

    # Normaliza IMDb para escala 0-100 para comparação justa com RT
    df["imdb_norm"] = df["imdb_score"] * 10

    # Diferença: positivo = crítica gostou mais, negativo = público gostou mais
    df["diff_critica_publico"] = df["rt_score"] - df["imdb_norm"]
    df["diff_abs"] = df["diff_critica_publico"].abs()

    # Média entre crítica e público (consenso)
    df["media_geral"] = (df["rt_score"] + df["imdb_norm"]) / 2

    # Rankings
    df["rank_mais_divisivo"] = df["diff_abs"].rank(ascending=False).astype(int)
    df["rank_mais_consensual"] = df["diff_abs"].rank(ascending=True).astype(int)

    # Classificação
    def classificar(row):
        if row["diff_critica_publico"] > 15:
            return "Superestimado pela crítica"
        elif row["diff_critica_publico"] < -15:
            return "Subestimado pela crítica"
        else:
            return "Consensual"

    df["classificacao"] = df.apply(classificar, axis=1)

    output = PROCESSED_DIR / "critica_vs_publico.csv"
    df.to_csv(output, index=False)
    print(f"Ratings processados: {output}")
    print(f"  - Filmes únicos: {df['filme'].nunique()}")
    print(f"  - Mais divisivo: {df.loc[df['rank_mais_divisivo'] == 1, 'filme'].values}")
    print(f"  - Mais consensual: {df.loc[df['rank_mais_consensual'] == 1, 'filme'].values}")
    return df


def process_brasil():
    """Processa os dados do Brasil no Oscar."""
    raw_path = RAW_DIR / "brasil_oscar.csv"
    if not raw_path.exists():
        print(f"AVISO: {raw_path} não encontrado. Rode scrape_brasil_oscar.py primeiro.")
        return None

    df = pd.read_csv(raw_path)

    # Garante que temos as colunas necessárias
    cols_needed = ["ano", "filme", "status"]
    for col in cols_needed:
        if col not in df.columns:
            print(f"AVISO: coluna '{col}' ausente no CSV do Brasil.")

    # Ordena por ano
    if "ano" in df.columns:
        df = df.sort_values("ano").reset_index(drop=True)

    output = PROCESSED_DIR / "brasil_oscar.csv"
    df.to_csv(output, index=False)
    print(f"Brasil no Oscar processado: {output}")
    print(f"  - Total de submissões: {len(df)}")
    if "status" in df.columns:
        print(f"  - Status:\n{df['status'].value_counts().to_string()}")
    return df


def main():
    print("=" * 50)
    print("Processando dados...")
    print("=" * 50)
    print("\n--- Entregável 1: Crítica vs Público ---")
    process_ratings()
    print("\n--- Entregável 2: Brasil no Oscar ---")
    process_brasil()
    print("\nDone!")


if __name__ == "__main__":
    main()
