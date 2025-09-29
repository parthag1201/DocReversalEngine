#workflow_graph.py
from langgraph.graph import StateGraph, END
from utils import logging_wrapper
from agents import abap_code_analyst, foreign_dependency_agent, functional_spec_drafter, technical_spec_writer, manager_agent, output_reviewer, final_output
# from typing_extensions import TypedDict

def build_workflow():
    workflow = StateGraph(dict)
    workflow.add_node("abap_code_analyst", logging_wrapper(abap_code_analyst, "abap_code_analyst"))
    workflow.add_node("functional_spec_drafter", logging_wrapper(functional_spec_drafter, "functional_spec_drafter"))
    workflow.add_node("foreign_dependency_agent", logging_wrapper(foreign_dependency_agent, "foreign_dependency_agent"))
    workflow.add_node("technical_spec_writer", logging_wrapper(technical_spec_writer, "technical_spec_writer"))
    workflow.add_node("manager_agent", logging_wrapper(manager_agent, "manager_agent"))
    workflow.add_node("output_reviewer", logging_wrapper(output_reviewer, "output_reviewer"))
    workflow.add_node("final_output", logging_wrapper(final_output, "final_output"))
    workflow.set_entry_point("abap_code_analyst")
    
    # Normal edges
    workflow.add_edge("abap_code_analyst", "foreign_dependency_agent")
    workflow.add_edge("foreign_dependency_agent", "functional_spec_drafter")
    workflow.add_edge("functional_spec_drafter", "technical_spec_writer")
    workflow.add_edge("technical_spec_writer", "manager_agent")
    workflow.add_edge("output_reviewer", "manager_agent")
    workflow.add_edge("final_output", END)

    # Conditional edges from manager_agent
    workflow.add_conditional_edges(
        "manager_agent",
        lambda state: state["next_node"],
        {
            # "functional_spec_drafter": "functional_spec_drafter",
            # "technical_spec_writer": "technical_spec_writer",
            # "foreign_dependency_agent": "foreign_dependency_agent",
            "output_reviewer": "output_reviewer",
            "final_output": "final_output",
        }
    )
    return workflow
