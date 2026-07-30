import os
import json
import time

from collections import defaultdict

import weaviate
from weaviate.auth import AuthApiKey

from dotenv import load_dotenv
load_dotenv()

from google import genai

from langchain_weaviate import WeaviateVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from memory import ConversationMemory


class RAGConfig:
    def __init__(
        self,
        collection_name="CampusHelpdesk",
        chunk_size=800,
        chunk_overlap=100,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm_model="gemini-3.1-flash-lite",
        checkpoint_file="checkpoint.json",
        sleep_time=2,
        retrieval_k=4
    ):
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.checkpoint_file = checkpoint_file
        self.sleep_time = sleep_time
        self.retrieval_k = retrieval_k

        # API Keys
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.weaviate_url = os.getenv("WEAVIATE_URL2")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY2")

class ConnectionManager:
    def __init__(self, config):
        self.config = config

    def get_gemini_client(self): #gemini client
        return genai.Client(
            api_key=self.config.gemini_api_key
        )

    #def get_weaviate_client(self):  #weaviate client
     #   return weaviate.connect_to_weaviate_cloud(
      #      cluster_url=self.config.weaviate_url,
       #     auth_credentials=AuthApiKey(self.config.weaviate_api_key),
        #    skip_init_checks=True
        #)
    def get_weaviate_client(self):
        print("=== CONNECTING TO WEAVIATE ===")

        print("URL:", repr(self.config.weaviate_url))
        print("Key:", self.config.weaviate_api_key[:8])

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.config.weaviate_url,
            auth_credentials=AuthApiKey(self.config.weaviate_api_key),
            skip_init_checks=True,
        )

        print("=== CONNECTED ===")

        return client        

class DocumentLoader:
    def __init__(self, config, client):
        self.config = config
        self.client = client

    def load_file(self, filepath):   
        extension = filepath.split(".")[-1].lower()

        loaders = {
            "pdf": PyPDFLoader,
            "txt": TextLoader,
            "csv": CSVLoader,
            "doc": UnstructuredWordDocumentLoader,
            "docx": UnstructuredWordDocumentLoader,
        }

        if extension not in loaders:
            print(f"Skipping unsupported file: {filepath}")
            return []

        try:
            loader = loaders[extension](filepath)
            return loader.load()

        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return []        

    def add_file_metadata(self, doc, file_name):
        doc.metadata["file_name"] = file_name
        doc.metadata["file_type"] = file_name.split(".")[-1].lower()

    def get_department(self, file_name):

        file_name = file_name.lower()

        department_mapping = {
            "admission": "Admissions",
            "fee": "Finance",
            "hostel": "Hostel",
            "leave": "Student Affairs",
            "faculty": "Academic Affairs",
            "exam": "Examination Cell",
            "od": "Student Affairs",
            "fest": "Cultural Committee"
        }

        for keyword, department in department_mapping.items():
            if keyword in file_name:
                return department

        return "General"


    def summarize_document(self, documents):

        full_text = "\n".join(
            doc.page_content for doc in documents
        )

    # Prevent token overflow
        full_text = full_text[:12000]

        prompt = f"""
            You are reading an official university document.

            Write a concise summary (2-3 sentences) describing:
            - What this document is about.
            - What topics it covers.
            - What kind of information students can find in it.

            Document:

        {full_text}
        """

        try:
                response = self.client.models.generate_content(
                model=self.config.llm_model,
                contents=prompt
                )

                return response.text.strip()

        except Exception as e:

                print(f"Summary generation failed: {e}")
                return "No summary available."    

    def load_documents(self, folder_path):

        if not os.path.exists(folder_path):
            raise FileNotFoundError(
                f"Folder '{folder_path}' not found."
            )

        all_docs = []

        for root, _, files in os.walk(folder_path):

            for file_name in files:

                filepath = os.path.join(root, file_name)

                docs = self.load_file(filepath)

                for doc in docs:

                    self.add_file_metadata(doc, file_name)

                    # Store department name (folder name)
                    department = os.path.basename(root)
                    doc.metadata["department"] = department

                all_docs.extend(docs)

        print(f"\nTotal pages loaded: {len(all_docs)}")

        loaded_files = sorted(
            {
                doc.metadata["file_name"]
                for doc in all_docs
            }
        )

        print("\nLoaded Documents:")

        for file in loaded_files:
            print(f"• {file}")

        return all_docs

    def split_documents(self, documents):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )

        chunks = splitter.split_documents(documents)

        total_chars = sum(
            len(chunk.page_content)
            for chunk in chunks
        )

        print("\nChunks:", len(chunks))
        print("Characters:", total_chars)
        print(
            "Average chars per chunk:",
            round(total_chars / len(chunks), 2)
        )

        return chunks    

    def load_and_split(self, folder_path):

        documents = self.load_documents(folder_path)
        chunks = self.split_documents(documents)
        return chunks

class VectorStoreManager:

    def __init__(self, config, vectorstore):

        self.config = config
        self.vectorstore = vectorstore
        self.processed = self.load_checkpoint()    

    def load_checkpoint(self):

        try:
            with open(self.config.checkpoint_file, "r") as f:
                return json.load(f)

        except (FileNotFoundError, json.JSONDecodeError):
            return {}   

    def save_checkpoint(self):

        try:
            with open(self.config.checkpoint_file, "w") as f:
                json.dump(self.processed, f, indent=2)

        except Exception as e:
            print(f"Checkpoint error: {e}")   

    def add_chunk_metadata(self, chunks):

        chunk_counter = defaultdict(int)

        for chunk in chunks:

            file_name = chunk.metadata["file_name"]

            chunk.metadata["chunk_id"] = (
            f"{file_name}_chunk_{chunk_counter[file_name]}"
            )

            chunk.metadata["chunk_number"] = chunk_counter[file_name]

            chunk.metadata["chunk_name"] = (
                f"{file_name}_chunk_{chunk_counter[file_name]}"
            )

            chunk.metadata["chunk_size"] = len(chunk.page_content)

            chunk_counter[file_name] += 1

        return chunks          

    def process_and_store(self, chunks):

        print(f"Already processed: {len(self.processed)}")

        for i, chunk in enumerate(chunks):

            chunk_id = chunk.metadata["chunk_id"]

            if chunk_id in self.processed:
                continue

            try:

                self.vectorstore.add_documents([chunk])

                self.processed[chunk_id] = {

                    "file_name": chunk.metadata["file_name"],

                    "department": chunk.metadata["department"],

                    "chunk_number": chunk.metadata["chunk_number"]

                }

                self.save_checkpoint()

                print(
                    f"Indexed {i+1}/{len(chunks)} : "
                    f"{chunk.metadata['chunk_name']}"
                )

            except Exception as e:

                print(
                    f"Error storing {chunk_id}: {e}"
                )

class RAGQA:

    def __init__(self, config, client, vectorstore):

            self.config = config
            self.client = client

            self.retriever = vectorstore.as_retriever(
                search_kwargs={
                    "k": 4
                }
            )

            # Conversation Memory
            self.memory = ConversationMemory(max_history=5)

    # Retrieve relevant chunks
    def retrieve(self, question, department):

        search_query = f"""
    Department: {department}

    Question:
    {question}
    """
        return self.retriever.invoke(search_query)

    # Build Prompt
    def build_prompt(self, question, docs):
        conversation_history = self.memory.get_history()

        context = ""

        for i, doc in enumerate(docs, start=1):

            context += f"""
==============================
Retrieved Chunk {i}

Department:
{doc.metadata.get("department")}

Document:
{doc.metadata.get("file_name")}

Document Summary:
{doc.metadata.get("document_summary")}

Content:
{doc.page_content}

==============================

"""

        prompt = f"""
You are the official AI Campus Helpdesk Assistant.

Your job is to answer student questions ONLY using the provided university documents.

-----------------------------
Conversation History
-----------------------------

{conversation_history}

-----------------------------
Retrieved University Documents
-----------------------------

{context}

-----------------------------
Current Student Question
-----------------------------

{question}

Instructions:

1. Use the conversation history only to understand follow-up questions.

2. Use ONLY the retrieved university documents to answer.

3. Never make up policies or information.

4. If the answer is not present in the documents, reply exactly:

"I couldn't find this information in the official university documents."

5. Keep the answer concise and student-friendly.

Answer:
"""
        return prompt

    # ---------------------------------------------------
    # Gemini Call
    # ---------------------------------------------------

    def ask_llm(self, prompt):

        response = self.client.models.generate_content(
            model=self.config.llm_model,
            contents=prompt
        )

        return response.text.strip()

    # ---------------------------------------------------
    # Main Query Function
    # ---------------------------------------------------

    def query(self, question):

        department = self.detect_department(question)

        docs = self.retrieve(
            question,
            department
        )

        if len(docs) == 0:

            return {

                "answer": "I couldn't find this information in the official university documents.",

                "sources": [],

                "departments": [],

                "predicted_department": department

            }

        prompt = self.build_prompt(
            question,
            docs
        )

        answer = self.ask_llm(prompt)
        # Store conversation in memory
        self.memory.add_message("User", question)
        self.memory.add_message("Assistant", answer)

        sources = sorted(
            list(
                {
                    doc.metadata["file_name"]
                    for doc in docs
                }
            )
        )

        departments = sorted(
            list(
                {
                    doc.metadata["department"]
                    for doc in docs
                }
            )
        )

        return {

            "answer": answer,

            "sources": sources,

            "departments": departments,

            "predicted_department": department

        }

    # ---------------------------------------------------
    # Pretty Print
    # ---------------------------------------------------

    def display_response(self, result):

        print(
            f"\nRouted Department: "
            f"{result['predicted_department']}"
        )

        print("\n" + "=" * 70)

        print("Campus Helpdesk\n")

        print(result["answer"])

        print("\nSources Used:")

        if result["sources"]:

            for source in result["sources"]:
                print(f"• {source}")

        else:
            print("None")

        print("\nDepartments Referenced:")

        if result["departments"]:

            for dept in result["departments"]:
                print(f"• {dept}")

        else:
            print("None")

        print("=" * 70)                


    def detect_department(self, question):

        prompt = f"""
    You are a routing agent for a university helpdesk.

    Choose ONLY ONE department from the following list.

    Admissions
    Finance
    Hostel
    Student Affairs
    Academic Affairs
    Examination Cell
    Cultural Committee
    General

    Question:

    {question}

    Reply with ONLY the department name.
    """

        response = self.client.models.generate_content(
            model=self.config.llm_model,
            contents=prompt
        )

        return response.text.strip()    

    # Initialize Chatbot
def initialize_chatbot():

        config = RAGConfig()

        connections = ConnectionManager(config)

        client = connections.get_gemini_client()

        vector_db = connections.get_weaviate_client()

        embeddings = HuggingFaceEmbeddings(
            model_name=config.embedding_model
        )

        vectorstore = WeaviateVectorStore(
            client=vector_db,
            index_name=config.collection_name,
            text_key="text",
            embedding=embeddings
        )

        rag = RAGQA(
            config=config,
            client=client,
            vectorstore=vectorstore
        )

        return rag, config, vector_db

if __name__ == "__main__":

    rag, config, vector_db = initialize_chatbot()

    print("="*70)
    print("Campus Helpdesk")
    print("="*70)

    while True:

        question = input("\nYou: ")

        if question.lower() == "exit":
            break

        result = rag.query(question)

        rag.display_response(result)

    vector_db.close()