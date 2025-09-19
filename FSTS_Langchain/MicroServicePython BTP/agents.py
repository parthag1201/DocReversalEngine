# agents.py
import re
# from langchain_core.messages import HumanMessage
# from langgraph.graph import MessagesState
# from tasks import analyze_code_task, functional_spec_task, technical_spec_task, initial_consolidation_task, output_review_feedback_task, final_specification_task
from utils import add_token_usage, load_prompt, format_user_prompt, parse_route
import inspect
from langchain.prompts import ChatPromptTemplate, PromptTemplate


def get_self_name():
    return inspect.currentframe().f_back.f_code.co_name

def generic_run_agent(agent_name, state, output_key, next_node):
    prompt_def = load_prompt(agent_name)

    # Convert YAML prompts into a LangChain ChatPromptTemplate
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_def["system_prompt"]),
        ("user", prompt_def["user_prompt"])
    ])

    print("chat_prompt: ",chat_prompt)

    # Format with state variables
    formatted_prompt = chat_prompt.format_messages(**state)
    
    print("formatted_prompt: ",formatted_prompt)
    # Invoke model
    response = state["model"].invoke(formatted_prompt)
    add_token_usage(response, agent_name)

    state[output_key] = response.content
    state["next_node"] = next_node
    return state

def abap_code_analyst(state):
    agent_name = get_self_name()
    return generic_run_agent(agent_name, state, output_key="abap_analysis", next_node="foreign_dependency_agent")

def foreign_dependency_agent(state):
    agent_name = get_self_name()
    return generic_run_agent(agent_name, state, output_key="foreign_dependencies", next_node="functional_spec_drafter")

def functional_spec_drafter(state):
    agent_name = get_self_name()
    return generic_run_agent(agent_name, state, output_key="fs_output", next_node="technical_spec_writer")

def technical_spec_writer(state):
    agent_name = get_self_name()
    return generic_run_agent(agent_name, state, output_key="ts_output", next_node="manager_agent")

def manager_agent(state):
    agent_name = get_self_name()
    prompt_def = load_prompt(agent_name)

    # --- Determine dynamic blocks based on feedback ---
    output_reviewer_feedback = state.get("review_feedback", "")
    has_feedback = bool(output_reviewer_feedback and output_reviewer_feedback.strip())

    task = prompt_def["final_specification_task"] if has_feedback else prompt_def["initial_consolidation_task"]
    task_description = task.get("description", "")
    task_expected_output = task.get("expected_output", "")

    if has_feedback:
        previous_manager_block = f"--- Manager Previous Output ---\n{state['manager_output']}\n"
        feedback_block = f"Reviewer Feedback:\n{output_reviewer_feedback}\n"
    else:
        fd = state.get("foreign_dependencies", "")
        fs = state.get("fs_output", "")
        ts = state.get("ts_output", "")
        previous_manager_block = ""
        feedback_block = f"--- Functional Spec ---\n{fs}\n\n--- Technical Spec ---\n{ts}\n--- Foreign Dependencies ---\n{fd}\n"

    # Use LangChain ChatPromptTemplate for message formatting
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_def["system_prompt"]),
        ("user", prompt_def["user_prompt"])
    ])
    
    formatted_prompt = chat_prompt.format_messages(
        task_description=task_description,
        task_expected_output=task_expected_output,
        template_text=state["template_text"],
        previous_manager_block=previous_manager_block,
        feedback_block=feedback_block,
    )

    state["last_user_prompt"] = formatted_prompt[1].content

    response = state["model"].invoke(formatted_prompt)
    add_token_usage(response, agent_name)

    # --- Dynamic routing logic ---
    route = parse_route(response.content)
    review_count = state.get("review_count", 0)
    max_reviews = state["max_output_reviews"]
    min_reviews = state["min_output_reviews"]

    if route == "final_output" and review_count < min_reviews:
        route = "output_reviewer"
    elif route == "output_reviewer" and review_count >= max_reviews:
        route = "final_output"

    # --- Update state ---
    state["manager_output"] = response.content
    state["next_node"] = route

    return state

def output_reviewer(state):
    agent_name = get_self_name()
    state = generic_run_agent(agent_name, state, output_key="ts_output", next_node="manager_agent")
    state["review_count"] = state.get("review_count", 0) + 1
    return state

def final_output(state):
    return state
