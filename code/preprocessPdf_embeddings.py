import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "Reports" / "APT_CyberCriminal_Campagin_Collections Reports"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore_gemini_embeddings"
CSV_FILE = PROJECT_ROOT / "ArticlesDataset_500_Valid.csv"
if not CSV_FILE.exists():
    CSV_FILE = PROJECT_ROOT / "code" / "ArticlesDataset_500_Valid.csv"
EMBEDDING_MODEL = "text-embedding-004"
API_KEY = os.environ["GOOGLE_API_KEY"]


def vectorize_pdf(pdf_path: Path, db_faiss_path: Path, api_key: str) -> None:
    loader = PyPDFLoader(str(pdf_path))

    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=api_key,
        )
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
        db_faiss_path.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(db_faiss_path))
    except IndexError:
        pdf_file = pdf_path.stem
        df = pd.read_csv(CSV_FILE)
        df = df.drop(df.loc[(df["Filename"] == pdf_file)].index)
        print(f"\nArticle {pdf_file} was deleted from dataset")
        df.to_csv(CSV_FILE, index=False)
        main()
    except RuntimeError as e:
        print("\n", e)
        print(f"\n{pdf_path}")
        exit()


def main():
    contents = pd.read_csv(CSV_FILE)
    contents["Date"] = pd.to_datetime(contents["Date"])

    pdf_files = []
    for _, row in contents.iterrows():
        year = row["Date"].year
        document = REPORTS_DIR / str(year) / f'{row["Filename"]}.pdf'
        if document.exists():
            pdf_files.append(document)

    for pdf_file in (progress_bar := tqdm(pdf_files)):
        progress_bar.set_description(f"Processing {pdf_file.name}")
        file_name = pdf_file.stem
        db_faiss_path = VECTORSTORE_DIR / f"db_faiss_{file_name}"

        if (db_faiss_path / "index.faiss").exists() and (db_faiss_path / "index.pkl").exists():
            continue

        vectorize_pdf(pdf_file, db_faiss_path, API_KEY)


if __name__ == "__main__":
    main()