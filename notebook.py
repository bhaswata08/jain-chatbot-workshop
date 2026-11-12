# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.2.2",
#     "groq==1.7.0",
#     "langchain==1.5.0",
#     "langchain-chroma==1.1.0",
#     "langchain-classic==1.0.8",
#     "langchain-community==0.4.2",
#     "langchain-core==1.8.0",
#     "langchain-experimental==0.4.2",
#     "langchain-huggingface==1.2.3",
#     "langchain-text-splitters==1.1.3",
#     "markdown==3.11.3",
#     "numpy==2.5.4",
#     "pandas==3.0.3",
#     "rank-bm25==0.2.2",
#     "sentence-transformers==5.6.0",
#     "umap-learn==0.5.12",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Setup
    """)
    return


@app.cell
def _(mo):
    groq_key = mo.ui.text(
        kind="password",
        label="Groq API key (console.groq.com → API Keys)",
        placeholder="gsk_...",
        full_width=True,
    )
    groq_key
    return (groq_key,)


@app.cell
def _():
    import zipfile
    from urllib.request import urlretrieve

    urlretrieve(
        "https://github.com/bhaswata08/jain-chatbot-workshop/releases/latest/download/jain_kb.zip",
        "jain_kb.zip",
    )
    zipfile.ZipFile("jain_kb.zip").extractall(".")  # creates kb/
    return


@app.cell(hide_code=True)
def _(mo):
    from collections.abc import Sequence
    from datetime import datetime
    from typing import Literal
    from langchain_core.documents import Document

    def create_docs_table(
        docs: Sequence[Document],
        keys: Sequence[str] = ("category", "title", "source_url"),
        selection: Literal["single", "multi"] | None = None,
        label: str | None = None,
    ) -> mo.ui.table:
      """Create a Marimo UI table from document metadata. Pass "page_content" as a key to show the text too."""
      def _value(d, k):
        if k == "page_content":
          return d.page_content
        v = d.metadata.get(k)
        if k in ("created", "last_modified", "last_accessed") and isinstance(v, float):
          return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M")  # file times are Unix seconds
        return v

      table_data = [{k: _value(d, k) for k in keys} for d in docs]
      table_label = label if label is not None else f"{len(docs)} pages loaded"

      return mo.ui.table(
          table_data,
          selection=selection,
          label=table_label,
      )

    return Document, create_docs_table


@app.cell(hide_code=True)
def _(mo):
    # The RAG map from the slides (deck/sections/05-rag.html), so each section shows where we are.
    _NODES = "raw loaders docs index store chunks query qt retrieval relevant dt context llm prompt response".split()
    _SVG = r"""
    <g font-family="Inter, sans-serif" text-anchor="middle" stroke-linecap="round">
      <!-- query -->
      <g style="opacity:var(--o-query,1);color:var(--c-query,#e9ebef)">
        <rect x="4" y="150" width="120" height="84" rx="14" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-query,#1a1f28)"/>
        <text x="64" y="200" font-size="26" font-weight="600" fill="currentColor">Query</text>
      </g>
      <g style="opacity:var(--o-qt,1);color:var(--c-qt,#a7b0be)">
        <line x1="134" y1="192" x2="282" y2="192" stroke="currentColor" stroke-width="3"/>
        <polygon points="280,184 296,192 280,200" fill="currentColor"/>
        <text x="212" y="148" font-size="22" fill="currentColor">Query</text>
        <text x="212" y="172" font-size="22" fill="currentColor">Transformation</text>
      </g>
      <!-- knowledge base -->
      <g style="opacity:var(--o-store,1);color:var(--c-store,#e9ebef)">
        <rect x="300" y="40" width="230" height="300" rx="34" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-store,#1a1f28)"/>
        <text x="415" y="108" font-size="21" fill="currentColor">Knowledge Base</text>
        <text x="415" y="144" font-size="27" font-weight="600" fill="currentColor">Vector/Doc</text>
        <text x="415" y="176" font-size="27" font-weight="600" fill="currentColor">Store</text>
      </g>
      <g style="opacity:var(--o-chunks,1);color:var(--c-chunks,#e9ebef)">
        <rect x="322" y="222" width="186" height="78" rx="10" stroke="currentColor" stroke-width="1.5" stroke-dasharray="5 5" style="fill:var(--f-chunks,none)"/>
        <text x="415" y="254" font-size="21" fill="currentColor">Documents &amp;</text>
        <text x="415" y="282" font-size="21" fill="currentColor">Sub-Documents</text>
      </g>
      <g style="opacity:var(--o-retrieval,1);color:var(--c-retrieval,#a7b0be)">
        <line x1="540" y1="192" x2="638" y2="192" stroke="currentColor" stroke-width="3"/>
        <polygon points="636,184 652,192 636,200" fill="currentColor"/>
        <text x="595" y="148" font-size="22" fill="currentColor">Retrieval</text>
        <text x="595" y="172" font-size="22" fill="currentColor">Method</text>
      </g>
      <g style="opacity:var(--o-relevant,1);color:var(--c-relevant,#e9ebef)">
        <rect x="658" y="158" width="140" height="68" rx="12" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-relevant,#1a1f28)"/>
        <text x="728" y="187" font-size="21" fill="currentColor">Relevant</text>
        <text x="728" y="213" font-size="21" fill="currentColor">Docs</text>
      </g>
      <g style="opacity:var(--o-dt,1);color:var(--c-dt,#a7b0be)">
        <line x1="808" y1="192" x2="896" y2="192" stroke="currentColor" stroke-width="3"/>
        <polygon points="894,184 910,192 894,200" fill="currentColor"/>
        <text x="858" y="148" font-size="22" fill="currentColor">Document</text>
        <text x="858" y="172" font-size="22" fill="currentColor">Transform</text>
      </g>
      <g style="opacity:var(--o-context,1);color:var(--c-context,#e9ebef)">
        <rect x="916" y="156" width="170" height="72" rx="12" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-context,#1a1f28)"/>
        <text x="1001" y="202" font-size="28" font-weight="600" fill="currentColor">Context</text>
      </g>
      <g style="opacity:var(--o-llm,1);color:var(--c-llm,#e9ebef)">
        <text x="1001" y="276" font-size="36" font-weight="600" fill="currentColor">+</text>
        <rect x="916" y="292" width="170" height="72" rx="12" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-llm,#1a1f28)"/>
        <text x="1001" y="338" font-size="28" font-weight="600" fill="currentColor">LLM</text>
      </g>
      <g style="opacity:var(--o-prompt,1);color:var(--c-prompt,#a7b0be)">
        <line x1="1094" y1="328" x2="1130" y2="328" stroke="currentColor" stroke-width="3"/>
        <polygon points="1128,320 1144,328 1128,336" fill="currentColor"/>
        <text x="1119" y="396" font-size="22" fill="currentColor">Prompt</text>
        <text x="1119" y="420" font-size="22" fill="currentColor">Method</text>
      </g>
      <g style="opacity:var(--o-response,1);color:var(--c-response,#e9ebef)">
        <rect x="1150" y="292" width="126" height="72" rx="12" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-response,#1a1f28)"/>
        <text x="1213" y="336" font-size="22" font-weight="600" fill="currentColor">Response</text>
      </g>
      <!-- ingestion column -->
      <g style="opacity:var(--o-index,1);color:var(--c-index,#a7b0be)">
        <line x1="415" y1="390" x2="415" y2="358" stroke="currentColor" stroke-width="3"/>
        <polygon points="407,360 415,344 423,360" fill="currentColor"/>
        <text x="432" y="376" font-size="22" text-anchor="start" fill="currentColor">Index</text>
      </g>
      <g style="opacity:var(--o-docs,1);color:var(--c-docs,#e9ebef)">
        <rect x="315" y="392" width="200" height="60" rx="12" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-docs,#1a1f28)"/>
        <text x="415" y="431" font-size="25" font-weight="600" fill="currentColor">Documents</text>
      </g>
      <g style="opacity:var(--o-loaders,1);color:var(--c-loaders,#a7b0be)">
        <line x1="415" y1="520" x2="415" y2="476" stroke="currentColor" stroke-width="3"/>
        <polygon points="407,478 415,462 423,478" fill="currentColor"/>
        <text x="432" y="500" font-size="22" text-anchor="start" fill="currentColor">Loaders</text>
      </g>
      <g style="opacity:var(--o-raw,1);color:var(--c-raw,#e9ebef)">
        <rect x="315" y="522" width="200" height="72" rx="12" stroke="currentColor" stroke-width="2.5" style="fill:var(--f-raw,#1a1f28)"/>
        <text x="415" y="552" font-size="23" font-weight="600" fill="currentColor">Raw Data</text>
        <text x="415" y="580" font-size="23" font-weight="600" fill="currentColor">Source</text>
      </g>
    </g>
    """


    def rag_map(now: str, done: str = ""):
        """Draw the map: boxes in `now` in amber, boxes in `done` in normal ink, the rest faded."""
        _style = []
        for _n in _NODES:
            if _n in now.split():
                _style.append(f"--o-{_n}:1;--c-{_n}:#f0a35e;--f-{_n}:#f0a35e26")
            elif _n not in done.split():
                _style.append(f"--o-{_n}:.16")
        return mo.Html(
            f"<div style='{';'.join(_style)};background:#15171c;border-radius:12px;padding:12px 16px;max-width:760px'>"
            f"<svg viewBox='0 0 1280 600' style='width:100%;display:block' role='img' aria-label='RAG pipeline map'>{_SVG}</svg></div>"
        )

    return (rag_map,)


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Basics of calling a model
    """),
        rag_map("query llm prompt response"),
    ])
    return


@app.cell
def _(groq_key, mo):
    from groq import Groq

    mo.stop(not groq_key.value, mo.md("**Paste your Groq API key in the box above to run this.**"))

    client = Groq(
        api_key=groq_key.value,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Explain the importance of fast language models",
            }
        ],
        model="openai/gpt-oss-20b",
    )

    mo.md(chat_completion.choices[0].message.content)
    return (Groq,)


@app.cell
def _(Groq, groq_key, mo):
    mo.stop(not groq_key.value, mo.md("**Paste your Groq API key in the box above to run this.**"))


    def llm(prompt: str, system: str | None = None, temperature: float = 1.0) -> str:
        messages = [{"role": "system", "content": system}] if system else []
        messages.append({"role": "user", "content": prompt})
        client = Groq(
            api_key=groq_key.value,
        )

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="openai/gpt-oss-20b",
            temperature=temperature,  # 0 = always the most likely token, higher = more random
        )
        return chat_completion.choices[0].message.content

    return (llm,)


@app.cell
def _(llm, mo):
    mo.md(llm(prompt = "Hey what can you do"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## System prompt: make it a JAIN helpdesk

    The **system** message holds the rules: who the bot is and what it must not do. The student never sees it.
    Same question, two system prompts.
    """)
    return


@app.cell
def _(llm, mo):
    HELPDESK = (
        "You are JAIN University's student helpdesk. Answer in 2 sentences. "
        "If unsure, say so and give the office contact."
    )
    _question = "I'm stressed about exams. Help?"


    def _reply(system):
        return mo.vstack(
            [
                mo.md(f"**system:** {system}"),
                mo.md(llm(_question, system=system)).style({"max-height": "420px", "overflow-y": "auto"}),
            ]
        )


    mo.vstack(
        [
            mo.md(f"**student:** {_question}"),
            mo.hstack([_reply("You are a helpful assistant."), _reply(HELPDESK)], widths="equal", gap=2, align="start"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Ask the refund question. Watch it fail

    The model has never read JAIN's refund page. The real answer: 16–30 days after the last date of admission, **50% is deducted**.
    Run it a few times. Some replies invent a percentage, rupee amounts or an email address; others admit they don't know.
    Neither one gives the student the answer.
    """)
    return


@app.cell
def _(llm, mo):
    mo.md(llm("I joined BCA at JAIN and want to cancel 20 days after the last date of admission. How much fee do I get back?"))
    return


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Loaders: get the documents into text

    `jain_kb.zip` already holds every page as Markdown with front matter (`title`, `source_url`, `category`, `fetched_at`).
    LangChain's `ObsidianLoader` reads a folder of Markdown files and turns that front matter into metadata.
    We keep it, because the answer has to cite where it came from.
    """),
        rag_map("raw loaders docs", done="query llm prompt response"),
    ])
    return


@app.cell
def _():
    from langchain_community.document_loaders import ObsidianLoader

    return (ObsidianLoader,)


@app.cell
def _(ObsidianLoader, create_docs_table):
    create_docs_table(ObsidianLoader("kb").load())
    # This has a silent issue of loading README.md
    return


@app.cell
def _(ObsidianLoader, create_docs_table):
    # Lets make it even more obvious
    create_docs_table(ObsidianLoader("kb").load(), keys=("source", "path", "last_modified"))
    return


@app.cell
def _(ObsidianLoader, create_docs_table):
    # Now we have excluded readme from the selection
    create_docs_table([d for d in ObsidianLoader("kb").load() if not d.metadata['source'] == "README.md"], keys=("source", "path", "last_modified"))
    return


@app.cell
def _(ObsidianLoader, create_docs_table):
    # Docs contains only the required documents from Jain university now
    docs = [d for d in ObsidianLoader("kb").load() if not d.metadata['source'] == "README.md"]  # skips kb/README.md
    create_docs_table(docs)
    return (docs,)


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Chunking: one vector per page is too coarse

    A programme page covers fees, syllabus, eligibility and placements. One vector blurs all of it.
    LangChain's `RecursiveCharacterTextSplitter` cuts **recursively**: on Markdown headings first, then paragraphs,
    lines and words, until each piece fits in `chunk_size`. Each chunk keeps its page's metadata.
    """),
        rag_map("chunks", done="query llm prompt response raw loaders docs"),
    ])
    return


@app.cell
def _(docs, mo):
    from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    mo.md(f"**{len(docs)} pages became {len(chunks)} chunks.** The first one:\n\n```\n{chunks[0].page_content}\n```")
    return Language, RecursiveCharacterTextSplitter, chunks


@app.cell(hide_code=True)
def _(docs, mo):
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_text_splitters import CharacterTextSplitter

    compare_page = mo.ui.dropdown(
        {d.metadata["title"]: d for d in docs},
        value=next(d.metadata["title"] for d in docs if d.metadata["source"] == "www-current-student-student-conduct-policy.md"),
        label="Page",
    )
    compare_size = mo.ui.slider(200, 1500, step=100, value=400, label="chunk_size", show_value=True)
    compare_find = mo.ui.text(value="75%", label="Highlight chunks containing")
    mo.hstack([compare_page, compare_size, compare_find], justify="start")
    return (
        CharacterTextSplitter,
        SemanticChunker,
        compare_find,
        compare_page,
        compare_size,
    )


@app.cell(hide_code=True)
def _(
    CharacterTextSplitter,
    Language,
    RecursiveCharacterTextSplitter,
    SemanticChunker,
    compare_find,
    compare_page,
    compare_size,
    embeddings,
    mo,
):
    # Comparing splitters
    import html

    _splitters = {
        "Fixed size": CharacterTextSplitter(separator="", chunk_size=compare_size.value, chunk_overlap=0),
        "Recursive": RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=compare_size.value, chunk_overlap=0),
        "Semantic (ignores chunk_size)": SemanticChunker(embeddings),
    }


    def _card(text):
        _hit = compare_find.value and compare_find.value.lower() in text.lower()
        _accent = "var(--amber-9, #d97706)" if _hit else "var(--gray-7, #9ca3af)"
        _bg = "var(--amber-3, #fef3c7)" if _hit else "var(--gray-2, #f9fafb)"
        return (
            f'<pre style="white-space:pre-wrap;overflow-wrap:anywhere;margin:0 0 8px;padding:8px 10px;'
            f'font-size:13px;line-height:1.45;border-left:3px solid {_accent};background:{_bg};border-radius:4px">'
            f"{html.escape(text.strip())}</pre>"
        )


    def _column(name, splitter):
        _pieces = [p.page_content for p in splitter.split_documents([compare_page.value])]
        return f"<div style='min-width:0'><h4 style='margin:0 0 8px'>{name} · {len(_pieces)} chunks</h4>{''.join(_card(p) for p in _pieces)}</div>"


    mo.Html(
        "<div style='display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px'>"
        + "".join(_column(n, s) for n, s in _splitters.items())
        + "</div>"
    )
    return (html,)


@app.cell
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Index: turn chunks into vectors

    `all-mpnet-base-v2`, loaded through LangChain's `HuggingFaceEmbeddings`, reads text and returns 768 numbers.
    We prefix each chunk with its page title, URL and category so a stray table row still knows which page it belongs to.
    """),
        rag_map("index", done="query llm prompt response raw loaders docs chunks"),
    ])
    return


@app.cell
def _():
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        encode_kwargs={"normalize_embeddings": True},  # unit length, so a dot product is the cosine similarity
    )
    query_embedding = embeddings.embed_query("What is a sentence embedding?")
    return embeddings, query_embedding


@app.cell
def _(query_embedding):
    query_embedding
    return


@app.cell
def _(query_embedding):
    len(query_embedding)
    return


@app.cell
def _(embeddings):
    # In the case of two example documents, shape will be 2x768
    doc_embeddings = embeddings.embed_documents(
        [
            "Sentence embeddings map text to dense vectors.",
            "LangChain provides a standard Embeddings interface.",
        ]
    )
    return (doc_embeddings,)


@app.cell
def _(doc_embeddings):
    doc_embeddings # shape is 2x768
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Lets build the embeddings for our Jain University docs now
    """)
    return


@app.cell
def _(chunks):
    # we prepend the title, source URL and category to each chunk's content
    documents_modified = [
        f"""Title: {c.metadata["title"]}\n
    Source URL: {c.metadata["source_url"]}\n
    Category: {c.metadata["category"]}\n
    Document content: {c.page_content}"""
        for c in chunks
    ]
    return (documents_modified,)


@app.cell(hide_code=True)
def _(chunks, create_docs_table, documents_modified, html, mo):
    _pre = "white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:10px 12px;font-size:13px;line-height:1.45;border-left:3px solid var(--gray-7, #9ca3af);background:var(--gray-2, #f9fafb);border-radius:4px"
    mo.vstack(
        [
            create_docs_table(
                chunks[0:5],
                keys=("title", "page_content", *(k for k in chunks[0].metadata if k != "title")),
                label="First 5 chunks, every field",
            ),
            *(
                mo.vstack([mo.md(f"### Document no. {n}"), mo.Html(f'<pre style="{_pre}">{html.escape(documents_modified[n])}</pre>')])
                for n in (0, 1)
            ),
        ]
    )
    return


@app.cell
def _(documents_modified, embeddings, mo):
    import numpy as np

    chunk_vectors = np.array(embeddings.embed_documents(documents_modified))
    mo.md(f"`chunk_vectors.shape` = `{chunk_vectors.shape}`: one row of {chunk_vectors.shape[1]} numbers per chunk.")
    return chunk_vectors, np


@app.cell(hide_code=True)
def _(chunk_vectors, chunks, mo):
    import altair as alt
    import pandas as pd
    import umap

    _xy = umap.UMAP(metric="cosine", random_state=0).fit_transform(chunk_vectors)  # 768 numbers -> 2
    _points = pd.DataFrame(
        {
            "x": _xy[:, 0],
            "y": _xy[:, 1],
            "category": [c.metadata["category"] for c in chunks],
            "title": [c.metadata["title"] for c in chunks],
            "chunk": [c.page_content[:200] for c in chunks],
        }
    )
    embedding_map = mo.ui.altair_chart(
        alt.Chart(_points)
        .mark_circle(size=40, opacity=0.7)
        .encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            color=alt.Color("category:N", scale=alt.Scale(scheme="tableau20")),
            tooltip=["category:N", "title:N", "chunk:N"],
        )
        .properties(width="container", height=500, title=f"{len(chunks)} chunks, squashed from {chunk_vectors.shape[1]} dimensions to 2 (UMAP). Drag a box to inspect."),
    )
    embedding_map
    return (embedding_map,)


@app.cell(hide_code=True)
def _(embedding_map, mo):
    mo.ui.table(embedding_map.value[["category", "title", "chunk"]], selection=None, label="Chunks in your box")
    return


@app.cell
def _(mo):
    probe_question = mo.ui.text(
        value="can I get my fee back?",
        label="Ask anything, see the cosine scores",
        full_width=True,
    )
    probe_question
    return (probe_question,)


@app.cell
def _(chunk_vectors, chunks, embeddings, mo, np, probe_question):
    _q = np.array(embeddings.embed_query(probe_question.value))
    _scores = chunk_vectors @ _q
    mo.ui.table(
        [
            {"cosine": round(float(_scores[i]), 2), "page": chunks[i].metadata["title"], "chunk": chunks[i].page_content[:200]}
            for i in np.argsort(-_scores)[:8]
        ],
        selection=None,
    )
    return


@app.cell
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Vector store: the vectors need a home

    A NumPy array is fine for a few hundred chunks. A vector store adds what a real bot needs:
    add, update and delete by id, filter by metadata, and fast search. We use Chroma, in memory, through LangChain.
    """),
        rag_map("store", done="query llm prompt response raw loaders docs chunks index"),
    ])
    return


@app.cell
def _(Document, chunks, documents_modified, embeddings, mo):
    from langchain_chroma import Chroma

    # Same chunks, but the text we embed and retrieve carries the title, URL and category prefix.
    index_docs = [Document(page_content=text, metadata=c.metadata) for text, c in zip(documents_modified, chunks)]

    vector_store = Chroma(
        collection_name="jain_kb",
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )
    vector_store.add_documents(index_docs, ids=[str(i) for i in range(len(index_docs))])
    mo.md(f"Chroma collection `jain_kb` holds **{vector_store._collection.count()}** chunks.")
    return index_docs, vector_store


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Query transformation: fix the question before searching

    Students write "bro how to get money back fast". Search works better on "admission cancellation refund rules".
    A small LLM call rewrites the question, using the conversation so far to resolve words like "it" or "that course".
    """),
        rag_map("qt", done="query llm prompt response raw loaders docs chunks index store"),
    ])
    return


@app.cell
def _(llm):
    def rewrite_query(question: str, history: str = "") -> str:
        prompt = f"""Rewrite the student's latest message as a short search query for JAIN University's website.
    Use the conversation to resolve references like "it" or "that course".
    Keep programme names, numbers and dates. Reply with the query only.

    Conversation so far:
    {history or "(none)"}

    Latest message: {question}"""
        return llm(prompt).strip().strip('"')


    rewrite_query("bro how to get money back fast parents will kill me")
    return (rewrite_query,)


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Retrieval: dense, keyword, hybrid

    * **Dense**: cosine on embeddings. Finds meaning ("computer course fees" finds BCA).
    * **Keyword**: BM25. Finds exact words ("BCA", "MCA", "NEP").
    * **Hybrid**: run both and merge the rankings with reciprocal rank fusion. A chunk near the top of both lists wins.
      LangChain's `EnsembleRetriever` does the merge.
    """),
        rag_map("retrieval relevant", done="query llm prompt response raw loaders docs chunks index store qt"),
    ])
    return


@app.cell
def _(Document, index_docs, vector_store):
    import re

    from langchain_classic.retrievers import EnsembleRetriever
    from langchain_community.retrievers import BM25Retriever

    dense_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    keyword_retriever = BM25Retriever.from_documents(
        index_docs, k=10, preprocess_func=lambda text: re.findall(r"\w+", text.lower())
    )
    hybrid_retriever = EnsembleRetriever(retrievers=[dense_retriever, keyword_retriever], weights=[0.5, 0.5])


    def hybrid_search(query: str, k: int = 5) -> list[Document]:
        return hybrid_retriever.invoke(query)[:k]

    return dense_retriever, hybrid_search, keyword_retriever


@app.cell(hide_code=True)
def _(mo):
    retrieval_query = mo.ui.dropdown(
        options=[
            "BCA fees",
            "computer course fees",
            "NEP",
            "refund after the last date of admission",
            "minimum attendance for exams",
            "hostel for girls",
        ],
        value="BCA fees",
        label="Compare retrieval methods",
        full_width=True,
    )
    retrieval_query
    return (retrieval_query,)


@app.cell(hide_code=True)
def _(
    dense_retriever,
    html,
    hybrid_search,
    keyword_retriever,
    mo,
    retrieval_query,
):
    _rankings = {
        "Dense": dense_retriever.invoke(retrieval_query.value)[:5],
        "Keyword (BM25)": keyword_retriever.invoke(retrieval_query.value)[:5],
        "Hybrid": hybrid_search(retrieval_query.value),
    }


    def _card(rank, doc):
        _text = doc.page_content.split("Document content: ", 1)[-1]  # drop the title/URL/category prefix
        return (
            "<div style='margin:0 0 10px;padding:8px 10px;border-left:3px solid var(--gray-7, #9ca3af);"
            "background:var(--gray-2, #f9fafb);border-radius:4px'>"
            f"<div style='font-size:13px;font-weight:600;margin-bottom:4px'>{rank}. {html.escape(doc.metadata['title'])}</div>"
            "<pre style='white-space:pre-wrap;overflow-wrap:anywhere;margin:0;font-size:12.5px;line-height:1.45;"
            f"max-height:220px;overflow-y:auto'>{html.escape(_text.strip())}</pre></div>"
        )


    mo.Html(
        "<div style='display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px'>"
        + "".join(
            f"<div style='min-width:0'><h4 style='margin:0 0 8px'>{method}</h4>"
            + "".join(_card(rank, d) for rank, d in enumerate(hits, 1))
            + "</div>"
            for method, hits in _rankings.items()
        )
        + "</div>"
    )
    return


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Document transform: chunks become labelled context

    Don't dump raw chunks. Wrap each one with where it came from (**provenance**), so the model can cite it and you can check it.
    """),
        rag_map("dt context", done="query llm prompt response raw loaders docs chunks index store qt retrieval relevant"),
    ])
    return


@app.cell
def _(Document, hybrid_search, mo):
    def format_context(hits: list[Document]) -> str:
        return "\n\n".join(
            f'<doc id="{n}" source="{d.metadata["source_url"]}" fetched="{d.metadata["fetched_at"][:10]}">\n'
            f"{d.page_content}\n</doc>"
            for n, d in enumerate(hits, 1)
        )


    mo.md(f"```xml\n{format_context(hybrid_search('admission cancellation refund rules', k=2))}\n```")
    return (format_context,)


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # Prompt method: role, rules, context, question

    Each rule blocks one way to hallucinate.
    """),
        rag_map("llm prompt response", done="raw loaders docs chunks index store query qt retrieval relevant dt context"),
    ])
    return


@app.cell
def _(format_context, hybrid_search, llm, rewrite_query):
    PROMPT = """# role
    You are JAIN University's student helpdesk.

    # rules
    Answer ONLY from the documents below.
    If the answer is not there, say "I don't know" and point the student to the right office.
    Cite the source of every fact as [doc id], for example [2].
    Keep it short and plain.

    # context
    {context}

    # question
    {question}"""


    def answer(question: str, history: str = "") -> dict:
        query = rewrite_query(question, history)
        hits = hybrid_search(query)
        reply = llm(PROMPT.format(context=format_context(hits), question=question))
        return {"question": question, "query": query, "hits": hits, "answer": reply}

    return (answer,)


@app.cell(hide_code=True)
def _(mo, rag_map):
    mo.vstack([
        mo.md(r"""
    # The chatbot

    Every message runs the whole inference half: rewrite, hybrid retrieve, label, prompt, answer.
    The sources under each answer match the `[n]` citations, so you can check the page yourself.
    """),
        rag_map("query qt retrieval relevant dt context llm prompt response", done="raw loaders docs chunks index store"),
    ])
    return


@app.cell
def _(answer, mo):
    def _chat_model(messages, config):
        _history = "\n".join(f"{m.role}: {m.content}" for m in messages[:-1][-6:])
        _result = answer(messages[-1].content, _history)
        _sources = "\n".join(
            f"{n}. [{d.metadata['title']}]({d.metadata['source_url']})" for n, d in enumerate(_result["hits"], 1)
        )
        return f"{_result['answer']}\n\n---\n*Searched for:* `{_result['query']}`\n\n**Sources**\n\n{_sources}"


    chat = mo.ui.chat(
        _chat_model,
        prompts=[
            "Joined BCA, cancelling 20 days after the last date. How much do I get back?",
            "What is the minimum attendance to sit the semester-end exam?",
            "Does JAIN have hostels for girls?",
            "Will the HOD sign my attendance form if I look really sad?",
        ],
    )
    chat
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
