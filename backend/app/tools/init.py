from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage

import app.tools.internal_document as document_tool
import app.tools.web_search as web_tool
import app.tools.planner as planner_tool   
import app.tools.lark_meeting_management.meeting_scheduler as meeting_tool

@tool
async def final_answer(answer: str, tools_used: list[str]) -> dict[str, str | list[str]]:
    """Use this tool to provide a final answer to the user."""
    return {"answer": answer, "tools_used": tools_used}

tool_lists = [
    # document_tool.internaldocs, 
    document_tool.search_internal_documents,
    # document_tool.getDocsRawContent, document_tool.getBaseRawContent, 
    # planner_tool.schedule_meeting,
    # web_tool.serpapi, meeting_tool.schedule_meeting,
    final_answer
]
name2tool = {tool.name: tool.coroutine for tool in tool_lists}

async def execute_tool(tool_call: AIMessage) -> ToolMessage:
    tool_name = tool_call.tool_calls[0]["name"]
    tool_args = tool_call.tool_calls[0]["args"]
    tool_out = await name2tool[tool_name](**tool_args)
    return ToolMessage(
        content=f"{tool_out}",
        tool_call_id=tool_call.tool_calls[0]["id"]
    )
