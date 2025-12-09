import os
import time
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_google_genai import HarmBlockThreshold, HarmCategory

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Try both locations for CSV file
CSV_FILE = PROJECT_ROOT / "ArticlesDataset_500_Valid.csv"
if not CSV_FILE.exists():
    CSV_FILE = PROJECT_ROOT / "code" / "ArticlesDataset_500_Valid.csv"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore_gemini_embeddings"
OUTPUT_FILE = PROJECT_ROOT / "ArticlesDataset_LLMAnswered.csv"

LLM_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "text-embedding-004"
BATCH_SIZE = 5

MAX_REQUESTS = 700
SLEEP_TIME = 1

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is not set. "
        "Please set it in your .env file or environment variables."
    )

QUESTION_MAP = [
    ("What is the name of a threat actor group?", "Threat Actor"),
    ("Which countries are being targeted?", "Victim Country"),
    ("Was a zero-day vulnerability used in this attack? Answer with TRUE or FALSE.", "Zero-Day"),
    (
        "What are the initial attack vectors described in this report? Group them into one of the following: "
        "SpearPhishing, Phishing, Watering Hole, Credential Reuse, Social Engineering, Exploit Vulnerability, "
        "Malicious Documents, Covert Channels, Drive-by Download, Removable Media, Website Equipping, Meta Data Monitoring.",
        "Attack Vector",
    ),
    (
        "Which specific malware, tool names, or software frameworks are used in the attack from this report?",
        "Malware",
    ),
    (
        "Identify the targeted sectors in this document. Group them into one of the following: Government and defense agencies, "
        "Corporations and Businesses, Financial institutions, Healthcare, Energy and utilities, Cloud/IoT services, "
        "Manufacturing, Education and research institutions, Media and entertainment companies, Critical infrastructure, "
        "Non-Governmental Organizations (NGOs) and Nonprofits, Individuals.",
        "Target Sector",
    ),
]


def load_knowledge_base(article: str) -> FAISS:
    """
    Load pre-computed FAISS vector store for an article.
    Note: The embeddings object is only needed for interface compatibility.
    The actual vectors are already stored in FAISS, so changing API keys is safe.
    """
    db_path = VECTORSTORE_DIR / f"db_faiss_{article}"
    if not db_path.exists():
        raise FileNotFoundError(
            f"FAISS vector store not found for article '{article}' at {db_path}. "
            f"Please run preprocessPdf_Submission.py first to generate embeddings."
        )
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
    return FAISS.load_local(str(db_path), embeddings, allow_dangerous_deserialization=True)


def load_llm() -> GoogleGenerativeAI:
    return GoogleGenerativeAI(
        model=LLM_MODEL,
        safety_settings={
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        },
        api_key=GOOGLE_API_KEY,
    )


def load_prompt() -> ChatPromptTemplate:
    prompt = """
You are an experienced security engineer analyzing APT incident reports. Answer each question using only the provided context.
- Keep responses concise (one sentence or phrase).
- If the information is not mentioned, reply exactly with "Not mentioned".
context = {context}
question = {question}
"""
    return ChatPromptTemplate.from_template(prompt)


def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def initialize_all_answers() -> dict:
    base = {
        "Date": [],
        "Filename": [],
        "Title": [],
        "Download Url": [],
    }
    for _, column in QUESTION_MAP:
        base[column] = []
    return base


def main():
    print(f"The {LLM_MODEL} model was chosen.\n")
    print(f"The {EMBEDDING_MODEL} embedding model was chosen.\n")

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"CSV file not found at {CSV_FILE}. "
            f"Please ensure ArticlesDataset_500_Valid.csv exists in the project root or code/ directory."
        )
    
    contents = pd.read_csv(CSV_FILE)

    if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 0:
        output_df = pd.read_csv(OUTPUT_FILE)
        start_index = output_df.shape[0]
        print(f"Resuming from index {start_index} (found {start_index} completed articles)")
        # Verify we're not trying to resume beyond available articles
        if start_index >= len(contents):
            print(f"All articles already processed! Exiting.")
            return
    else:
        output_df = pd.DataFrame()
        start_index = 0
        print("Starting processing from the beginning")

    llm = load_llm()
    prompt = load_prompt()

    cnt = 0
    request_count = 0
    batch_answers = initialize_all_answers()
    total_articles = len(contents)

    for i in (progress_bar := tqdm(range(start_index, total_articles))):
        # Check if we've reached the request limit
        if request_count >= MAX_REQUESTS:
            print(f"\n{'='*70}")
            print(f"Reached request limit: {MAX_REQUESTS} requests used")
            print(f"Processed {i - start_index} articles in this session")
            print(f"Total articles processed: {i} / {total_articles}")
            print(f"Remaining: {total_articles - i} articles ({total_articles - i} * 6 = {(total_articles - i) * 6} requests)")
            print(f"\nTo continue:")
            print(f"1. Switch to your second API key (update GOOGLE_API_KEY in .env)")
            print(f"2. Run the script again - it will auto-resume from article {i}")
            print(f"{'='*70}\n")
            break

        article = contents["Filename"][i]
        progress_bar.set_description(f"Processing {article} [Requests: {request_count}/{MAX_REQUESTS}]")

        try:
            knowledge_base = load_knowledge_base(article)
        except FileNotFoundError as e:
            print(f"\n⚠️  Warning: {e}")
            print(f"Skipping article '{article}' and continuing with next article.\n")
            continue
        
        retriever = knowledge_base.as_retriever(search_kwargs={"k": 4})

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        answers = {}
        article_complete = True
        for question, column in QUESTION_MAP:
            # Check request limit before each API call
            if request_count >= MAX_REQUESTS:
                article_complete = False
                break
            
            try:
                response = rag_chain.invoke(question)
                request_count += 1
            except Exception as exc:  # noqa: BLE001
                print(f"Failed to process question '{question}' for {article}: {exc}")
                response = "Error processing question"
                # Don't increment on error (API call may not have been made)
            answers[column] = response
            time.sleep(SLEEP_TIME)
        
        # Only save complete articles (all 6 questions answered)
        if article_complete:
            batch_answers["Date"].append(contents["Date"][i])
            batch_answers["Filename"].append(contents["Filename"][i])
            batch_answers["Title"].append(contents["Title"][i] if "Title" in contents.columns else "")
            batch_answers["Download Url"].append(contents["Download Url"][i])
            for _, column in QUESTION_MAP:
                batch_answers[column].append(answers.get(column, "Not mentioned"))
            cnt += 1
        else:
            # Hit limit mid-article - break and let it be processed fully on next run
            break
        if cnt == BATCH_SIZE:
            cnt = 0
            new_answers_df = pd.DataFrame(batch_answers)
            if not output_df.empty:
                missing_cols = set(output_df.columns) - set(new_answers_df.columns)
                for col in missing_cols:
                    new_answers_df[col] = "Not specified"
            output_df = pd.concat([output_df, new_answers_df], ignore_index=True)
            output_df.to_csv(OUTPUT_FILE, index=False)
            batch_answers = initialize_all_answers()

    if cnt > 0:
        new_answers_df = pd.DataFrame(batch_answers)
        output_df = pd.concat([output_df, new_answers_df], ignore_index=True)
        output_df.to_csv(OUTPUT_FILE, index=False)
    
    # Final summary
    if OUTPUT_FILE.exists():
        final_df = pd.read_csv(OUTPUT_FILE)
        print(f"\n{'='*70}")
        print(f"Session Summary:")
        print(f"  Total requests made: {request_count}")
        print(f"  Articles processed: {len(final_df)} / {total_articles}")
        if len(final_df) < total_articles:
            remaining = total_articles - len(final_df)
            print(f"  Remaining: {remaining} articles ({remaining * 6} requests)")
            print(f"  Progress saved to: {OUTPUT_FILE}")
        else:
            print(f"  ✅ All articles completed!")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
