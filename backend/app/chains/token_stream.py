import asyncio
import json

from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from datetime import datetime
from sqlalchemy.orm import Session

import app.config as config
import app.services.openai as services_openai 
import app.services.redis as services_redis
import app.tools.init as tool 
import app.chains.utils as chain_utils
from app.database.chat import ChatDB


# Streaming Handler
class QueueCallbackHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.final_answer_seen = False

    async def __aiter__(self):
        while True:
            if self.queue.empty():
                await asyncio.sleep(0.1)
                continue
            token_or_done = await self.queue.get()
            if token_or_done == "<<DONE>>":
                return
            if token_or_done:
                yield token_or_done
    
    async def on_llm_new_token(self, *args, **kwargs) -> None:
        chunk = kwargs.get("chunk")
        if chunk and chunk.message.additional_kwargs.get("tool_calls"):
            if chunk.message.additional_kwargs["tool_calls"][0]["function"]["name"] == "final_answer":
                self.final_answer_seen = True
        self.queue.put_nowait(kwargs.get("chunk"))
    
    async def on_llm_end(self, *args, **kwargs) -> None:
        if self.final_answer_seen:
            self.queue.put_nowait("<<DONE>>")
        else:
            self.queue.put_nowait("<<STEP_END>>")

# Agent Executor
class CustomAgentExecutor:
    def __init__(self):
        self.max_iterations = config.EXECUTOR_MAX_ITERATIONS
        self.agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", []),
                "time_now": lambda x: x["time_now"]
            }
            | services_openai.prompt
            | services_openai.llm.bind_tools(tool.tool_lists, tool_choice="any")
        )

    async def invoke(self, input: str, streamer: QueueCallbackHandler, user_id: int, chat_id: int, db: Session, verbose: bool = False) -> dict:
        # invoke the agent but we do this iteratively in a loop until
        # reaching a final answer
        count = 0
        final_answer: str | None = None
        agent_scratchpad: list[AIMessage | ToolMessage] = []

        # generate chat history
        chat_history = chain_utils.generate_chat_history(user_id, chat_id, db)
        
        # streaming function
        async def stream(query: str) -> list[AIMessage]:
            response = self.agent.with_config(
                callbacks=[streamer]
            )
            # we initialize the output dictionary that we will be populating with
            # our streamed output
            outputs = []
            # now we begin streaming
            async for token in response.astream({
                "input": query,
                "chat_history": chat_history,
                "agent_scratchpad": agent_scratchpad,
                "time_now": datetime.utcnow().strftime("%A, %Y-%m-%d %H:%M:%S UTC"),
            }):
                tool_calls = token.additional_kwargs.get("tool_calls")
                if tool_calls:
                    # first check if we have a tool call id - this indicates a new tool
                    if tool_calls[0]["id"]:
                        outputs.append(token)
                    else:
                        outputs[-1] += token
                else:
                    pass
            return [
                AIMessage(
                    content=x.content,
                    tool_calls=x.tool_calls,
                    tool_call_id=x.tool_calls[0]["id"]
                ) for x in outputs
            ]

        while count < self.max_iterations:
            # invoke a step for the agent to generate a tool call
            tool_calls = await stream(query=input)
            # gather tool execution coroutines
            tool_obs = await asyncio.gather(
                *[tool.execute_tool(tool_call) for tool_call in tool_calls]
            )
            # append tool calls and tool observations to the scratchpad in order
            id2tool_obs = {tool_call.tool_call_id: tool_obs for tool_call, tool_obs in zip(tool_calls, tool_obs)}
            for tool_call in tool_calls:
                agent_scratchpad.extend([
                    tool_call,
                    id2tool_obs[tool_call.tool_call_id]
                ])
                
            count += 1
            # if the tool call is the final answer tool, we stop
            found_final_answer = False
            for tool_call in tool_calls:
                if tool_call.tool_calls[0]["name"] == "final_answer":
                    final_answer_call = tool_call.tool_calls[0]
                    final_answer = final_answer_call["args"]["answer"]
                    found_final_answer = True
                    break
            
            # Only break the loop if we found a final answer
            if found_final_answer:
                break
        
        # Save message to database
        tools_used = []
        steps = []
        for msg in agent_scratchpad:
            if isinstance(msg, AIMessage):
                for tool_call in msg.tool_calls:
                    if (tool_call["name"] != "final_answer"):
                        tools_used.append(tool_call["name"])
                        steps.append({
                            "name": tool_call["name"],
                            "result": tool_call["args"]
                        })
        
        result = json.dumps({
            "answer": final_answer if final_answer else "No answer found",
            "tools_used": tools_used
        })
        chat_db = ChatDB(db)
        chat_db.add_message(
            chat_id=chat_id,
            query=input,
            result=result,
            steps=steps
        )

        # Update Redis memory
        human_msg = HumanMessage(content=input)
        ai_msg = AIMessage(content=final_answer or "No answer found")
        chat_history_key = chain_utils.CHAT_HISTORY_REDIS_KEY.format(user_id, chat_id)
        services_redis.append_list(chat_history_key, chain_utils.serialize_history_message(human_msg), chain_utils.CHAT_HISTORY_MAX_MESSAGES, chain_utils.CHAT_HISTORY_TTL_SECONDS)
        services_redis.append_list(chat_history_key, chain_utils.serialize_history_message(ai_msg), chain_utils.CHAT_HISTORY_MAX_MESSAGES, chain_utils.CHAT_HISTORY_TTL_SECONDS)
        
        # return the final answer in dict form
        return final_answer_call if final_answer else {"answer": "No answer found", "tools_used": []}

agent_executor = CustomAgentExecutor()  

async def token_generator(content: str, streamer: QueueCallbackHandler, chat_id: int, user_id:int, db: Session):
    task = asyncio.create_task(agent_executor.invoke(
        input=content,
        streamer=streamer,
        chat_id=chat_id,
        user_id=user_id,
        db=db,
        verbose=True # set to True to see verbose output in console
    ))

    async for token in streamer:
        try:
            if token == "<<STEP_END>>":
                yield "</step>"
            elif tool_calls := token.message.additional_kwargs.get("tool_calls"):
                if tool_name := tool_calls[0]["function"]["name"]:
                    yield f"<step><step_name>{tool_name}</step_name>"
                if tool_args := tool_calls[0]["function"]["arguments"]:
                    yield tool_args
        except Exception as e:
            print(f"Error streaming token: {e}")
            continue

    await task