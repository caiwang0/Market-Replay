import json
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel

import app.models.tools.internal_documents as InternalDocsToolsModel
from app.services.lark import get_lark_tenant_token, get_lark_docx_raw_content, get_lark_base_table_records, get_lark_base_view 
from app.services.openai import select_document
from app.services.chromadb import query_collection

@tool
async def internaldocs(
    query: str,
    similarity_threshold: float = 0.5,
    top_k: int = 50
) -> list[InternalDocsToolsModel.DocumentResult]:
    """Use this tool for questions about internal topics, documents, or specific data like 'Novi'."""
    documents, metadatas, distances = await query_collection(query, top_k)

    grouped: dict[str, dict] = {}
    for doc, meta, dist in zip(documents, metadatas, distances):
        if dist > similarity_threshold:
            continue

        # # Metadata filtering: example for 'kpi' files only
        # if meta.get("file_type") and meta["file_type"] not in {"kpi", "report"}:
        #     continue

        token = meta.get("file_token")
        if token not in grouped:
            grouped[token] = {
                "file_token": token,
                "file": meta.get("file"),
                "link": meta.get("link"),
                "distance": dist,
                "chunks": [],
                "match_count": 0,
            }
        grouped[token]["distance"] = min(grouped[token]["distance"], dist)
        grouped[token]["chunks"].append(doc)
        grouped[token]["match_count"] += 1

    results: list[InternalDocsToolsModel.DocumentResult] = []
    for entry in grouped.values():
        content = "\n---\n".join(entry["chunks"])
        limited_content = content[:2000]
        results.append(InternalDocsToolsModel.DocumentResult(
            file_token=entry["file_token"],
            file=entry["file"],
            link=entry["link"],
            distance=entry["distance"],
            content=limited_content,
        ))


    # Rerank by distance and match count
    results.sort(key=lambda r: (r.distance, -grouped[r.file_token]["match_count"]))

    if not results:
        return "No relevant documents found in the database."

    return results

@tool
async def search_internal_documents(query: str) -> list[InternalDocsToolsModel.DocumentResult]:
    """
        Search across internal documents for relevant information related to a user query.
        This tool returns a list of documents that are most relevant to the question, with metadata and extracted content chunks.
        Each returned document includes:
        - `file`: the name of the source document
        - `link`: a direct URL to the document
        - `content`: a list of extracted content, which can be:
            • json structure, each item is a table rows with column name as the key and cell value as the value
            • unstructured text chunks with `text` key containing the text content chunks
    """
    similarity_threshold = 0.5
    top_k = 100

    # get relevant chunks (rc) data
    rc_documents, rc_metadatas, rc_distances = await query_collection(query, top_k)

    # Fetch unique file tokens
    rc_file_tokens = []
    rc_file_tokens_map: dict[str, dict] = {}
    for doc, meta, dist in zip(rc_documents, rc_metadatas, rc_distances):
        if dist > similarity_threshold:
            continue
        
        file_token = meta.get("file_token")
        if file_token is None:
            continue

        if file_token not in rc_file_tokens_map:
            rc_file_tokens_map[file_token] = {"distance": dist}
            rc_file_tokens.append(file_token)

    if len(rc_file_tokens) == 0:
        return "No relevant documents found in the database."
    
    # get relevant chunks summaries (rcs) data
    rcs_documents, rcs_metadatas, rcs_distances = await query_collection(
        query, 
        top_k,
        where={'$and': [
            {"chunk_type": "summary"},
            {"file_token": {'$in': rc_file_tokens}},
        ]}
    )

    # Sort relevant_chunks_summary by relevant_chunk distance (lowest first)
    summary_item_zip = list(zip(rcs_documents, rcs_metadatas, rcs_distances))
    summary_item_zip.sort(key=lambda x: rc_file_tokens_map.get(x[1].get("file_token"), {}).get("distance", x[2]))

    # Unzip back to lists, already sorted by distance
    summary_item_documents, summary_item_metadatas, summary_item_distances = zip(*summary_item_zip) if summary_item_zip else ([], [], [])
    rcs_documents = list(summary_item_documents)
    rcs_metadatas = list(summary_item_metadatas)
    rcs_distances = list(summary_item_distances)

    # Prepare summaries for OpenAI selection
    batch_summaries = []
    selected_file_tokens = None
    batch_size = 10 # send per 10 batch of summaries
    for i in range(0, len(summary_item_zip), batch_size):
        for doc, meta, dist in zip(rcs_documents[i:i+batch_size], rcs_metadatas[i:i+batch_size], rcs_distances[i:i+batch_size]):
            chunk_file_token = meta.get("file_token")
            chunk_file_name = meta.get("file")
            
            batch_summaries.append({
                "file_token": chunk_file_token,
                "file": chunk_file_name,
                "summary": doc[:500],
            })

        # Call select_document after each batch
        selected_file_tokens = await select_document(query, batch_summaries)
        if selected_file_tokens:
            break

    if len(selected_file_tokens) == 0:
        return "No relevant documents found in the database."

    # get filtered relevant chunks (frc) data
    frc_documents, frc_metadatas, frc_distances = await query_collection(
        query, 
        top_k,
        where={'$and': [
            {"file_token": {'$in': selected_file_tokens}},
            {"chunk_type": {'$nin': ["summary"]}},
        ]}
    )

    # Prepare results as a list of InternalDocsToolsModel.DocumentResult objects for LangChain tool consumption
    # Group by file_token, sort by chunk_index, and concatenate content for same file_token
    grouped_results: dict[str, dict] = {}
    for doc, meta, dist in zip(frc_documents, frc_metadatas, frc_distances):
        file_token = meta.get("file_token")
        chunk_index = meta.get("chunk_index", 0)
        if file_token not in grouped_results:
            grouped_results[file_token] = {
                "file": meta.get("file"),
                "link": meta.get("link"),
                "chunks": []
            }
        grouped_results[file_token]["chunks"].append({
            "index": chunk_index,
            "content": normalize_content(doc)
        })

    results: list[InternalDocsToolsModel.DocumentResult] = []
    for entry in grouped_results.values():
        # Sort chunks by chunk_index
        sorted_chunks = sorted(entry["chunks"], key=lambda x: x["index"])

        # Concatenate content
        # Concatenate chunk contents, extracting "text" if present, else converting to string
        content = []

        for chunk in sorted_chunks:
            content.append(chunk["content"])

        results.append(InternalDocsToolsModel.DocumentResult(
            file=entry["file"],
            link=entry["link"],
            content=content,
        ))

    return results

def normalize_content(raw_content: str) -> dict:
    try:
        # Try to parse it as JSON
        content = json.loads(raw_content)
        if isinstance(content, dict):
            return content  # valid parsed JSON object
        else:
            return {"text": raw_content[:2000]}  # not a dict, fallback to text
    except json.JSONDecodeError:
        # Not JSON – treat it as plain text
        return {"text": raw_content[:2000]}

@tool
async def getDocsRawContent(document_token: str):
    """
    From links like: https://heygotrade.sg.larksuite.com/docx/RjvRdeGiuoZiL8xPLCTlxedwgWd, extract the document_code: RjvRdeGiuoZiL8xPLCTlxedwgWd.
    Use this tool to summarise Lark docx content. 
    """
    # Get access token
    access_token = get_lark_tenant_token()
    print("Got Access Token")

    # Retrieve raw content from the Lark Docx
    output = get_lark_docx_raw_content(access_token, document_token)
    return output

@tool
async def getBaseRawContent(app_token: str, table_token: str, view_token: str):
    """
    The links can be long like: "https://heygotrade.sg.larksuite.com/base/N2SbbUJe1a8A1YsRFc3lHNnAgke?table=tblwgzcZAjTA1A2M&view=vewnflDv44"
    I want to extract out the app_token: N2SbbUJe1a8A1YsRFc3lHNnAgke, table_token: tblwgzcZAjTA1A2M, view_token: vewnflDv44. Always check for a view token.
    Summarise the output and use other tools to search linked_docs if necessary. Only include relevant information.
    """
    # Get access token
    access_token = get_lark_tenant_token()
    
    # Retrieve Data from the Lark Base
    lark_base_view = get_lark_base_view(access_token, app_token, table_token, view_token)
    lark_base_table_records = get_lark_base_table_records(access_token, app_token, table_token)

    output = {
        "overview": lark_base_view,
        "content": lark_base_table_records,
    }

    return output