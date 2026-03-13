"""
Scraping da página Wikipedia: Brazilian submissions for the Academy Award
Extrai o histórico completo de submissões brasileiras ao Oscar de Melhor Filme Internacional.
"""

import io
import pandas as pd
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://en.wikipedia.org/wiki/List_of_Brazilian_submissions_for_the_Academy_Award_for_Best_International_Feature_Film"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) OscarProject/1.0"
}


def scrape_brasil_oscar() -> pd.DataFrame:
    """Faz scraping da tabela de submissões brasileiras na Wikipedia."""
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(io.StringIO(response.text))

    # Procura a maior tabela que tem "Year" em alguma coluna
    best_table = None
    best_len = 0
    for table in tables:
        cols_str = " ".join(str(c).lower() for c in table.columns)
        if "year" in cols_str and len(table) > best_len:
            best_table = table
            best_len = len(table)

    if best_table is None:
        best_table = max(tables, key=len)

    df = best_table.copy()

    # Debug: mostra colunas originais
    print(f"Colunas originais: {list(df.columns)}")

    # Trata colunas duplicadas — a Wikipedia pode ter "Film" duas vezes
    # (título original e título em inglês)
    cols = list(df.columns)
    new_cols = []
    seen = {}
    for c in cols:
        c_str = str(c).strip()
        if c_str in seen:
            seen[c_str] += 1
            new_cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            new_cols.append(c_str)
    df.columns = new_cols

    # Encontra e renomeia colunas por padrão
    rename = {}
    filme_found = False
    for col in df.columns:
        cl = col.lower()
        if "year" in cl and "ano" not in rename.values():
            rename[col] = "ano"
        elif ("film" in cl or "title" in cl) and not filme_found:
            rename[col] = "filme"
            filme_found = True
        elif ("film" in cl or "title" in cl) and filme_found:
            rename[col] = "titulo_en"
        elif "director" in cl:
            rename[col] = "diretor"
        elif "result" in cl or "outcome" in cl:
            rename[col] = "resultado"
        elif "language" in cl:
            rename[col] = "idioma"

    df = df.rename(columns=rename)
    print(f"Colunas renomeadas: {list(df.columns)}")

    # Extrai ano (4 dígitos)
    if "ano" in df.columns:
        df["ano"] = df["ano"].astype(str).str.extract(r"(\d{4})")
        df = df.dropna(subset=["ano"])
        df["ano"] = df["ano"].astype(int)

    # Classifica resultado
    if "resultado" in df.columns:
        df["status"] = df["resultado"].astype(str).apply(classificar_resultado)
    else:
        df["status"] = "Submetido"

    # Remove linhas sem filme
    if "filme" in df.columns:
        df = df[df["filme"].notna()]
        df = df[df["filme"].astype(str).str.strip().str.len() > 0]

    # Seleciona colunas finais
    final_cols = ["ano", "filme", "diretor", "status"]
    if "titulo_en" in df.columns:
        final_cols.insert(2, "titulo_en")
    existing = [c for c in final_cols if c in df.columns]
    df = df[existing].reset_index(drop=True)

    return df


def classificar_resultado(texto: str) -> str:
    """Classifica o resultado da submissão brasileira."""
    texto = texto.lower().strip()
    if "won" in texto or "winner" in texto:
        return "Vencedor"
    elif "not nominated" in texto or "disqualif" in texto:
        return "Submetido"
    elif "nomin" in texto:
        return "Indicado"
    elif "shortlist" in texto:
        return "Shortlisted"
    else:
        return "Submetido"


def main():
    print("Fazendo scraping da Wikipedia...")
    df = scrape_brasil_oscar()
    output_path = RAW_DIR / "brasil_oscar.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSalvo em {output_path}")
    print(f"Total de registros: {len(df)}")
    print(f"\nDistribuição de status:")
    if "status" in df.columns:
        print(df["status"].value_counts().to_string())
    print(f"\nPrimeiras linhas:")
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()
