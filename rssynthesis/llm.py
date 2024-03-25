from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from tempfile import NamedTemporaryFile
from yaml import load, SafeLoader
from pathlib import Path

from rssynthesis.models import LLM
from rssynthesis.constants import CONFIG_DIR

bullet_prompt = """
Write a summary in markdown format of the following text.

The summary should cover all the key points and main ideas presented in the original text
while also condensing the information into a concise and easy-to-understand format. 
Ensure that the summary includes relevant details and examples that support the main ideas, 
while avoiding any unnecessary information or repetition. The length of the summary should
be appropriate for the length and complexity of the original text, providing a clear and 
accurate overview without omitting any important information. The summary should not repeat
the original text without adding anything new.

The summary should be bullet points. The tone should be informational and authoritative.

<BEGIN TEXT>
{text}
<END TEXT>
Summary:
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

def load_llm_config() -> LLM:
    llm_config_path = Path(CONFIG_DIR, "llm.yml").resolve()

    with open(llm_config_path, 'r') as fp:
        config = load(fp, Loader=SafeLoader)
    
    return LLM(**config)


def summarize_single(mk: str) -> str:
    mk_len = len(mk.split())
    if mk_len <= 500:
        return None
    
    llm = load_llm_config()

    prompt = PromptTemplate.from_template(bullet_prompt)
    with NamedTemporaryFile() as tmp:
        tmp.write(mk.encode("utf-8"))
        loader = UnstructuredMarkdownLoader(file_path=tmp.name)
        docs = loader.load()

    chain = LLMChain(llm=llm.llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=chain, document_variable_name="text")

    return stuff_chain.run(docs)
