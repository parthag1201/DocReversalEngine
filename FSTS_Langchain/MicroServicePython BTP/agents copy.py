# agents.py
import re
# from langchain_core.messages import HumanMessage
# from langgraph.graph import MessagesState
# from tasks import analyze_code_task, functional_spec_task, technical_spec_task, initial_consolidation_task, output_review_feedback_task, final_specification_task
from utils import add_token_usage, load_prompt

def abap_code_analyst(state):
    full_user_prompt = f"""Dissect the provided ABAP code to extract all technical details and the logic flow of the report.
    Focus on identifying data sources, selection screens, core logic, and output structures.
    You need to go through each and every section of report to the extent form where a good Functional and Technical specification document can be derived out of it
    
    --- Task Description ---
    {state['analyze_code_task'].description.format(code_files = state['code_input'])}

    --- Expected Output ---
    {state['analyze_code_task'].expected_output}
"""
    state['last_user_prompt'] = full_user_prompt
    messages = [
        {
            "role": "system",
            "content": """You are an expert ABAP developer with decades of experience.
            You have an exceptional eye for detail and can instantly understand the flow and structure of any ABAP program. 
            Your task is to analyze the code and provide a structured, raw analysis for the documentation team."""
        },
        {
            "role": "user",
            "content": full_user_prompt
        }
    ]
    response = state['model'].invoke(messages)
    add_token_usage(response, 'abap_code_analyst')
    state["abap_analysis"] = response.content
    state["next_node"] = "foreign_dependency_agent"
    return state

def foreign_dependency_agent(state):
    full_user_prompt = f"""Foreign Dependency Extraction Specialist: Identify and extract all foreign dependencies from the provided ABAP code.
    This includes identifying any external tables, classes, or Join Queries of tables that the report relies on.
        
        --- Task Description ---
        {state['foreign_dependency_agent'].description}
        
        --- Expected Output ---
        {state['foreign_dependency_agent'].expected_output}
        
        ABAP code:
        {state['code_input']}"""
    
    state['last_user_prompt'] = full_user_prompt
    messages = [
        {
            "role": "system",
            "content": """You are a meticulous analyst who specializes in identifying external dependencies in ABAP code.
Your task is to extract all foreign dependencies, including external tables, classes, or Join Queries of tables that the report relies on.
You will provide a structured list of these dependencies, including their names, versions, and any relevant documentation links."""
        },
        {
            "role": "user",
            "content": full_user_prompt
        }
    ]
    response = state['model'].invoke(messages)
    add_token_usage(response, 'foreign_dependency_agent')
    state["foreign_dependencies"] = response.content
    state["next_node"] = "functional_spec_drafter"
    return state

def functional_spec_drafter(state):
    full_user_prompt = f"""Business Systems Analyst: Translate the technical analysis of an ABAP report into a clear and concise\nfunctional specification document for business stakeholders.\n\nABAP report: {state['abap_analysis']}\n\nRefer to this professional template for creating a business specification document: {state['template_text']}\n\n--- Task Description ---\n{state['functional_spec_task'].description}\n\n--- Expected Output ---\n{state['functional_spec_task'].expected_output}\n"""
    state['last_user_prompt'] = full_user_prompt
    messages = [
        {
            "role": "system",
            "content": """You are a bridge between the technical team and the business. You excel at taking complex
business challenges and oppurtunities and reframing it in terms of business processes and objectives. Your functional
specifications are legendary for their clarity and business relevance, enabling stakeholders to
understand exactly what all action items are required as the part of Functional specification of the program."""
        },
        {
            "role": "user",
            "content": full_user_prompt
        }
    ]
    response = state['model'].invoke(messages)
    add_token_usage(response, 'functional_spec_drafter')
    state["fs_output"] = response.content
    state["next_node"] = "technical_spec_writer"
    return state

def technical_spec_writer(state):
    full_user_prompt = f"""Technical Documentation Specialist: Create a comprehensive and detailed technical specification document based on the ABAP code analysis.\n\nThis is the ABAP code : {state['code_input']}\n\nABAP code analysis: {state['abap_analysis']}\n\nRefer to this professional template for creating a business technical specification document. '{state['template_text']}'\n\n--- Task Description ---\n{state['technical_spec_task'].description}\n\n--- Expected Output ---\n{state['technical_spec_task'].expected_output}\n"""
    state['last_user_prompt'] = full_user_prompt
    messages = [
        {
            "role": "system",
            "content": """You are a meticulous technical writer who specializes in creating documentation for developers by analysing the code and functional specifications.\n    Your specifications are precise, well-structured, and follow industry best practices. Your work ensures\n    that any developer can pick up the report for maintenance or enhancement with complete clarity\n    on its internal workings."""
        },
        {
            "role": "user",
            "content": full_user_prompt
        }
    ]
    response = state['model'].invoke(messages)
    add_token_usage(response, 'technical_spec_writer')
    state["ts_output"] = response.content
    state["next_node"] = "manager_agent"
    return state

def manager_agent(state):
    output_reviewer_feedback = state.get("review_feedback", "")
    has_feedback = bool(output_reviewer_feedback and output_reviewer_feedback.strip())
    task = state['final_specification_task'] if has_feedback else state['initial_consolidation_task']
    task_description = task.description
    task_expected_output = task.expected_output
    if has_feedback:
        previous_manager_block = f"--- Manager Previous Output ---\n{state['manager_output']}\n"
        feedback_block = f"Reviewer Feedback:\n{output_reviewer_feedback}\n"
    else:
        fd = state.get("foreign_dependencies", "")
        fs = state.get("fs_output", "")
        ts = state.get("ts_output", "")
        previous_manager_block = ""
        feedback_block = f"--- Functional Spec ---\n{fs}\n\n--- Technical Spec ---\n{ts}\n--- Foreign Dependencies ---\n{fd}\n"
    full_user_prompt = f"""Manager Agent: Oversee the generation and refinement of Functional and Technical Specifications.
Ensure that the final deliverables follow the official documentation structure, incorporate all critical content, and meet business and technical standards.

The specifications must allow both business users and developers to clearly understand:
- What the report or enhancement does
- Why it was implemented
- How it behaves functionally and technically
- What exact fields, triggers, and data flows are involved

Refer to this professional template for creating the consolidated document:
{state['template_text']}

{previous_manager_block}
{feedback_block}

--- Task Description ---
{task_description}

--- Expected Output ---
{task_expected_output}

Structure Checklist:
- Include all required FS and TS sections as per the template
- Ensure all key sections such as Executive Summary, Logic Flow, and Unit Test Scenarios are present and relevant
- Maintain alignment between FS and TS so business logic matches technical logic
- The final output must be clean, complete.
 
At the end of your response, include a routing directive using one of these exact keywords based on the Routing Rules:
- [ROUTE: foreign_dependency_agent] if foreign dependencies is unclear, incomplete
- [ROUTE: functional_spec_drafter] if FS is unclear, incomplete, or not aligned with the template
- [ROUTE: technical_spec_writer] if TS is missing logic, incomplete, or missing required sections
- [ROUTE: output_reviewer] if both FS and TS are complete but need a formal review for alignment and structure
- [ROUTE: final_output] only if all feedback is addressed, all sections are complete, and FS and TS are fully aligned

IMPORTANT: The response must contain only the Markdown content itself, with no commentary, preambles, or concluding remarks, EXCEPT the ROUTE: content as required in rules.
"""
    state['last_user_prompt'] = full_user_prompt
    messages = [
        {
            "role": "system",
            "content": """You are an experienced SAP S4 project manager with a deep understanding of software development life cycles and well versed with the good practises of SAP, Business needs and ABAP Development.
            You have good knowledge on SAP Functional processes like MTD, RTR, OTC and PTP.
            You excel at breaking down complex tasks, coordinating teams, incorporating feedback, and ensuring quality deliverables.
            You are adept at communicating with both technical and business stakeholders."""
        },
        {
            "role": "user",
            "content": full_user_prompt
        }
    ]
    
    def parse_route(content):
        # If response.content is a list, flatten to a string
        if isinstance(content, list):
            # If list of dicts with 'text'
            if all(isinstance(item, dict) and "text" in item for item in content):
                content = " ".join(item["text"] for item in content)
            else:
                # assume list of strings
                content = " ".join(map(str, content))
        elif not isinstance(content, str):
            # Fallback: convert to string
            content = str(content)

        match = re.search(r"\[ROUTE:\s*(\w+)\]", content)
        return match.group(1) if match else "output_reviewer"
    
    response = state['model'].invoke(messages)
    
    add_token_usage(response, 'manager_agent')
    
    route = parse_route(response.content)
    max_reviews = state['max_output_reviews']
    min_reviews = state["min_output_reviews"]
    review_count = state.get("review_count", 0)
    
    if route == "final_output" and review_count < min_reviews:
        route = "output_reviewer"
    elif route == "output_reviewer" and review_count >= max_reviews:
        route = "final_output"

    print("[DEBUG response.content type]:", type(response.content))
    print("[DEBUG]: parsed route: ", parse_route(response.content), "routing to: ", route)

    state["manager_output"] = response.content
    state["next_node"] = route
    
    return state

def output_reviewer(state):
    full_user_prompt = f"""Output Reviewer (Business Knowledge): Review consolidated Functional and Technical Specifications and provide constructive feedback to the Manager Agent for refinement, focusing on business alignment and completeness.
    You have good knowledge on SAP Functional processes like MTD, RTR, OTC and PTP.
    The Functional and technical specifications document must be ehaustive enough to be able to create abap codes for those processes. So you need to perform all the checks according the best SAP coding practises and industry standards
    
    Manager Output: {state['manager_output']}
    
    --- Task Description ---
    {state["output_review_feedback_task"].description}
    
    --- Expected Output ---
    {state["output_review_feedback_task"].expected_output}
"""
    state['last_user_prompt'] = full_user_prompt
    messages = [
        {
            "role": "system",
            "content": """You are a business stakeholder with a keen eye for detail and a deep understanding of the organizational goals and user needs.\n    You critically evaluate specifications, ensuring they meet intended business objectives and provide actionable feedback for improvement."""        },
        {
            "role": "user",
            "content": full_user_prompt
        }
    ]
    response = state['model'].invoke(messages)
    add_token_usage(response, 'output_reviewer')
    state["review_feedback"] = response.content
    state["review_count"] = state.get("review_count", 0) + 1
    state["next_node"] = "manager_agent"
    return state

def final_output(state):
    return state
