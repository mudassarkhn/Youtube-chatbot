from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Set up API keys and model configs
GOOGLE_API_KEY = ''
CHROMA_DIR = './chromadb'

import asyncio

def get_llm():
    async def create_llm():
        return ChatGoogleGenerativeAI(
            google_api_key=GOOGLE_API_KEY,
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    return asyncio.run(create_llm())

def get_embeddings():
    async def create_embeddings():
        return GoogleGenerativeAIEmbeddings(
            google_api_key=GOOGLE_API_KEY,
            model="models/gemini-embedding-exp-03-07"
        )
    return asyncio.run(create_embeddings())

def extract_video_id(youtube_url: str):
    import re
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", youtube_url)
    return match.group(1) if match else None

def load_transcript(video_id: str):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        transcript = " ".join(chunk["text"] for chunk in transcript_list)
        return transcript
    except TranscriptsDisabled:
        return None

def build_vector_store(transcript_text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
    embeddings = get_embeddings()
    chunks = splitter.create_documents([transcript_text])
    db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
    return db

def get_retrieval_chain(db):
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    prompt = ChatPromptTemplate.from_template('''
    You are a helpful assistant.
    Answer ONLY from the provided transcript context.
    If the context is insufficient, just say you don't know.
    <context>
    {context}
    </context>
    Question: {input}
''')
    llm = get_llm()
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    return retrieval_chain
