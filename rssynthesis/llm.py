from langchain_community.llms import ollama
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from tempfile import NamedTemporaryFile

bullet_prompt = """
Write a summary in markdown format of the following text.
The summary should be a number of bullet points.
The tone should be informational and authoritative.
<BEGIN TEXT>
{text}
<END TEXT>
<BEGIN SUMMARY>:
"""

paragraph_prompt = """
Write a concise summary in markdown format of the following text.
The summary should be one short paragraph.
The tone should be informational and authoritative.
<BEGIN TEXT>
{text}
<END TEXT>
<BEGIN SUMMARY>:
"""


llm = ollama.Ollama(
    base_url="https://ollama.leozq.in", model="openhermes:v2.5", num_ctx=8000
)


def summarize_single(mk: str) -> str:
    mk_len = len(mk.split())

    if mk_len <= 500:
        return None

    prompt = PromptTemplate.from_template(bullet_prompt)
    with NamedTemporaryFile() as tmp:
        tmp.write(mk.encode("utf-8"))
        loader = UnstructuredMarkdownLoader(file_path=tmp.name)
        docs = loader.load()

    chain = LLMChain(llm=llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=chain, document_variable_name="text")

    return stuff_chain.run(docs)
