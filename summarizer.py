import os
import re
import PyPDF2
import markdown
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate

# Initialize LLM
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

def extract_text(file):
    if file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    elif file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    else:
        return None

def split_text(text, chunk_size=1000, overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return splitter.split_text(text)

def summarize_text(text, method="easy"):
    prompts = {
        "easy": (
            "Generate a detailed note summary of the following text in Markdown format. "
            "Include a title, bullet points for key points, and a section titled 'Points to Remember'.\n\n{text}"
        ),
        "80/20": (
            "Analyze the following text and extract the most critical 20% of the content (Key 20%) that "
            "represents 80% of the ideas (Supporting 80%). Present in two sections 'Key 20%' and 'Supporting 80%', "
            "plus bullet points and a 'Points to Remember' section.\n\n{text}"
        ),
        "understanding": (
            "Rewrite the following text into an easily understandable set of notes in Markdown format. "
            "Use headings, bullet points for key takeaways, and include a section 'Points to Remember'.\n\n{text}"
        )
    }
    if method not in prompts:
        raise ValueError("Invalid summarization method.")

    template = PromptTemplate(template=prompts[method], input_variables=["text"])
    chunks = split_text(text)
    docs = [Document(page_content=chunk) for chunk in chunks]
    chain = load_summarize_chain(
        llm,
        chain_type="map_reduce",
        map_prompt=template,
        combine_prompt=template
    )

    raw_md = chain.run(docs)
    clean_md = re.sub(r'^[\s\S]*?(#)', r'\1', raw_md)  # strip any prose before first '#'
    html = markdown.markdown(clean_md)
    return clean_md, html
