# Assignment 0: UserProxyAgent Integration in SoM Teams (Final Version 3)

import asyncio
import os
from typing import Sequence, Union
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent, SocietyOfMindAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage, BaseMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console

# Load environment variables
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

# Configure the model client
model_info = {
    "json_output": True,
    "function_calling": True,
    "vision": True,
    "family": "unknown",
    "structured_output": True,
}
model_client = OpenAIChatCompletionClient(model='gemini-2.5-pro', model_info=model_info, api_key=api_key)

# --- Inner Team Definition ---

developer_agent = AssistantAgent(
    name="DeveloperAgent",
    model_client=model_client,
    system_message="You are a software developer. Your job is to write Python code to accomplish a given task. When you are done, present the code and say 'DEVELOPMENT COMPLETE'."
)

tester_agent = AssistantAgent(
    name="TesterAgent",
    model_client=model_client,
    system_message="You are a software tester. Your job is to write unit tests for the given Python code. When you are done, present the tests and say 'TESTING COMPLETE'."
)

documentation_writer_agent = AssistantAgent(
    name="DocumentationWriterAgent",
    model_client=model_client,
    system_message="You are a technical writer. Your job is to write clear and concise documentation for the given Python code. When you are done, present the documentation and say 'DOCUMENTATION COMPLETE'."
)

inner_user_proxy_agent = UserProxyAgent(
    name="InnerUserProxyAgent",
    input_func=input,
    description="A proxy for the user to provide feedback at critical decision points."
)

def inner_team_selector_func(messages: Sequence[BaseMessage]) -> Union[str, None]:
    if len(messages) <= 1:
        return developer_agent.name
    last_message = messages[-1]
    if last_message.source == developer_agent.name:
        return inner_user_proxy_agent.name
    if last_message.source == inner_user_proxy_agent.name and messages[-2].source == developer_agent.name:
        if "good" in last_message.content.lower() or "approve" in last_message.content.lower():
            return tester_agent.name
        else:
            return developer_agent.name
    if last_message.source == tester_agent.name:
        return inner_user_proxy_agent.name
    if last_message.source == inner_user_proxy_agent.name and messages[-2].source == tester_agent.name:
        if "good" in last_message.content.lower() or "approve" in last_message.content.lower():
            return documentation_writer_agent.name
        else:
            return tester_agent.name
    if last_message.source == documentation_writer_agent.name:
        return inner_user_proxy_agent.name
    if last_message.source == inner_user_proxy_agent.name and messages[-2].source == documentation_writer_agent.name:
        if "good" in last_message.content.lower() or "approve" in last_message.content.lower():
            return None
        else:
            return documentation_writer_agent.name
    return None

inner_team_termination = TextMentionTermination(text="FINALIZE")

inner_team = SelectorGroupChat(
    participants=[developer_agent, tester_agent, documentation_writer_agent, inner_user_proxy_agent],
    model_client=model_client,
    termination_condition=inner_team_termination,
    selector_func=inner_team_selector_func,
    allow_repeated_speaker=True
)

# --- Outer Team Integration ---

inner_team_som = SocietyOfMindAgent(
    name="InnerTeamSoM",
    team=inner_team,
    model_client=model_client,
    description="A Society of Mind agent representing a team of developers, testers, and writers.",
    instruction="You are a self-contained team of software developers. You will be given a plan to execute. Follow the plan and return the final result.",
    response_prompt="Summarize the inner team's work and final output."
)

project_manager_agent = AssistantAgent(
    name="ProjectManagerAgent",
    model_client=model_client,
    system_message="You are a project manager. Your only job is to take a high-level task and create a detailed, step-by-step plan for your team. End your plan with the phrase 'PLAN COMPLETE'."
)

outer_user_proxy_agent = UserProxyAgent(
    name="OuterUserProxyAgent",
    input_func=input,
    description="A proxy for the user to provide high-level oversight and approve project milestones."
)

def outer_team_selector_func(messages: Sequence[BaseMessage]) -> Union[str, None]:
    if len(messages) <= 1:
        return project_manager_agent.name
    last_message = messages[-1]
    if last_message.source == project_manager_agent.name and "PLAN COMPLETE" in last_message.content:
        return outer_user_proxy_agent.name
    if last_message.source == outer_user_proxy_agent.name and "approve" in last_message.content.lower():
        return inner_team_som.name
    if last_message.source == inner_team_som.name:
        return outer_user_proxy_agent.name
    if last_message.source == outer_user_proxy_agent.name:
        return project_manager_agent.name
    return None

outer_team_termination = TextMentionTermination(text="TERMINATE")

outer_team = SelectorGroupChat(
    participants=[project_manager_agent, inner_team_som, outer_user_proxy_agent],
    model_client=model_client,
    termination_condition=outer_team_termination,
    selector_func=outer_team_selector_func,
    allow_repeated_speaker=True
)

async def main():
    task = "Develop a Python function that calculates the factorial of a number, write tests for it, and provide documentation."
    await Console(outer_team.run_stream(task=TextMessage(content=task, source="user")))

if __name__ == "__main__":
    print("--- Starting Final Assignment (v3) ---")
    asyncio.run(main())

# --- Flow Diagram ---
"""
Here is a textual representation of the flow diagram:

Outer Team Flow:
1. User provides a task.
2. `outer_team_selector_func` selects `ProjectManagerAgent`.
3. ProjectManagerAgent creates a plan and emits "PLAN COMPLETE".
4. `outer_team_selector_func` selects `OuterUserProxyAgent`.
5. **[Human Intervention]** OuterUserProxyAgent reviews the plan. If the plan is rejected, the flow returns to the `ProjectManagerAgent`. If approved, it proceeds.
6. `outer_team_selector_func` selects `InnerTeamSoM`.
7. InnerTeamSoM executes its workflow (see below), taking the approved plan as its task.
8. InnerTeamSoM returns the final result to the outer team.
9. `outer_team_selector_func` selects `OuterUserProxyAgent`.
10. **[Human Intervention]** OuterUserProxyAgent validates the final output.
    - User provides feedback (e.g., "Looks good, TERMINATE.").
11. The process ends when the user says "TERMINATE".

Inner Team (InnerTeamSoM) Flow:
1. Receives a task from the Outer Team.
2. `inner_team_selector_func` selects `DeveloperAgent`.
3. DeveloperAgent writes the code and emits "DEVELOPMENT COMPLETE".
4. `inner_team_selector_func` selects `InnerUserProxyAgent`.
5. **[Human Intervention]** InnerUserProxyAgent reviews the code. If feedback is positive, proceeds to testing. If negative, returns to the developer.
6. `inner_team_selector_func` selects `TesterAgent`.
7. TesterAgent tests the code and emits "TESTING COMPLETE".
8. `inner_team_selector_func` selects `InnerUserProxyAgent`.
9. **[Human Intervention]** InnerUserProxyAgent reviews the test results. If feedback is positive, proceeds to documentation. If negative, returns to the tester.
10. `inner_team_selector_func` selects `DocumentationWriterAgent`.
11. DocumentationWriterAgent writes documentation and emits "DOCUMENTATION COMPLETE".
12. `inner_team_selector_func` selects `InnerUserProxyAgent`.
13. **[Human Intervention]** InnerUserProxyAgent performs a final review. If feedback is positive, the inner team's work is done. If negative, returns to the writer.
14. The inner team's work is complete when the user says "FINALIZE", and the result is returned to the outer team.
"""
