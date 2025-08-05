# %pip install crewai_tools langchain_community langchain_google_genai fpdf2 markdown2

# %pip install crewai agentic-ai

# # Install the google-generativeai package
# %pip install google-generativeai

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Importing langchain libraries
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence

#  Comment starts


# pdf read and write
from fpdf import FPDF
from markdown2 import Markdown

# Warning Control
import warnings
warnings.filterwarnings('ignore')

# # # Import crewAI library
# # from crewai import Agent, Task, Crew, Process
# # from crewai.project import CrewBase, agent, crew, task
# # from crewai.agents.agent_builder.base_agent import BaseAgent
# # from typing import List
# # from crewai.flow.flow import Flow, listen, start

import os
# %pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
apiKey = os.getenv("GOOGLE_API_KEY3")
print(apiKey)

# #setting up LLM

# from crewai import LLM

# llm = LLM(model="gemini/gemini-2.5-pro",
#                              verbose=True,
#                              temperature=0.5,
#                              api_key = apiKey)

llm = ChatGoogleGenerativeAI(
    model="gemini/gemini-2.5-pro",  # Use Gemini 2.5 Pro model
    google_api_key=apiKey,
    temperature=0.5,
    verbose=True
)


# # Tkinter block
# import os
# import re
# from tkinter import Tk
# from tkinter.filedialog import askopenfilename

# # Hide the root tkinter window
# Tk().withdraw()

# # Open file dialog
# file_path = askopenfilename(
#     title="Select ABAP Code File",
#     filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
# )

# abap_code_example = ""
# output_html_filename = ""

# if file_path:
#     with open(file_path, 'r', encoding='utf-8') as f:
#         abap_code_example = f.read()
#     print("File selected:", file_path)
#     print("Code Preview:\n", abap_code_example[:500])  # Show a preview

#     # Get sanitized filename without extension
#     base_filename = os.path.splitext(os.path.basename(file_path))[0]
#     output_html_filename = re.sub(r'[\\/*?:"<>|]', "_", base_filename) + ".html"
# else:
#     print("No file selected.")
    


# 1. ABAP Code Interpreter Agent (Prompt)
abap_interpreter_prompt = ChatPromptTemplate.from_template("""
You are an ABAP Code Interpreter.
Your goal: Analyze the provided ABAP code to understand its structure, main components (like FORMs, METHODs, FUNCTIONs), and the overall program flow.
Backstory: As a seasoned ABAP developer, you distill complex code into a clear, structured summary.

ABAP Code:
---
{abap_code}
---

Return a structured summary outlining the main execution flow, loops, conditions, and subroutine calls.
""")

abap_interpreter_chain = abap_interpreter_prompt | llm

# 2. Logic Reviewer Agent (Prompt)
logic_reviewer_prompt = ChatPromptTemplate.from_template("""
You are a Business Logic Analyst.
Your goal: Review the structured summary of the ABAP code to identify and map out the core business logic, including conditional paths, loops, and subroutine calls.
Backstory: You specialize in reverse-engineering legacy systems and translating technical flow into logical steps.

Structured Summary:
---
{summary}
---

Return a step-by-step description of the program's logic flow, highlighting decision points and repeated processes.
""")

logic_reviewer_chain = logic_reviewer_prompt | llm

# 3. Diagram Blocks Generator Agent (Prompt)
diagram_blocks_generator_prompt = ChatPromptTemplate.from_template("""
You are a Workflow Diagram Architect.
Your goal: Translate the identified business logic into a list of abstract diagram components (e.g., Start, End, Process, Decision, IO).
Backstory: You define the fundamental building blocks of the diagram before rendering.

Logic Flow:
---
{logic_flow}
---

Return a list of objects or structured text defining each diagram block (e.g., {{id: 'A', type: 'Start', label: 'Start Program'}}), and the connections between them (e.g., 'A --> B').
""")

diagram_blocks_generator_chain = diagram_blocks_generator_prompt | llm

# 4. Diagram Generation Agent (Prompt)
diagram_generator_prompt = ChatPromptTemplate.from_template("""
You are a Mermaid Code Generator.
Your goal: Generate syntactically correct Mermaid code for various diagrams from a natural language description.
Backstory: You are an expert in MermaidJS and always produce perfect code.

Diagram Blocks:
---
{diagram_blocks}
---

Return a single code block containing the complete, syntactically correct Mermaid code for the UML activity diagram.
""")

diagram_generator_chain = diagram_generator_prompt | llm

# 5. Manager Agent (Quality Control) (Prompt)
manager_prompt = ChatPromptTemplate.from_template("""
You are a Quality Assurance Manager.
Your goal: Review the final MermaidJS diagram to ensure it accurately represents the original ABAP code's logic without being overly complex or too simplistic.
Backstory: You are the ultimate quality gatekeeper.

MermaidJS Code:
---
{mermaid_code}
---

Original ABAP Code:
---
{abap_code}
---

Return the final, approved MermaidJS code block, ready for rendering. If not accurate, provide feedback.
""")

manager_chain = manager_prompt | llm


# 1. Read code from the 'code_files' folder
import PyPDF2 # Import PyPDF2 here
code_folder_path = 'Workflow/OTC Workflow'
if not os.path.exists(code_folder_path):
    os.makedirs(code_folder_path)
    # Create a dummy file for demonstration if the folder is empty
    with open(os.path.join(code_folder_path, 'sample_code.txt'), 'w') as f:
        f.write("REPORT Z_SAMPLE_REPORT.") # Add some dummy code

abap_code_example = ""
with open('Workflow/OTC Workflow/2.zgnmtd0475_consign_process_top.txt', 'r') as f:
    abap_code_example += f.read() + "\n\n"
# for filename in os.listdir(code_folder_path):
#     if filename.endswith(".txt"):
#         with open(os.path.join(code_folder_path, filename), 'r') as f:
#             abap_code_example += f.read() + "\n\n"

# print(abap_code_example)


# --- Task Definitions ---

# Task for ABAP interpreter
abap_interpreter_prompt = ChatPromptTemplate.from_template("""
Analyze the following ABAP code. Identify the main program events (like START-OF-SELECTION),
loops (DO/WHILE), conditional logic (IF/ELSE), and subroutine calls (PERFORM).
Create a clear, summarized list of these structural components and their sequence.

ABAP Code:
---
{abap_code}
---

Return a structured text summary outlining the main execution flow, loops, conditions, and subroutine calls in the ABAP code.
""")

# Create the chain
abap_interpreter_chain = abap_interpreter_prompt | llm

# Run the chain with your ABAP code
interpreter_output = abap_interpreter_chain.invoke({"abap_code": abap_code_example})

print(interpreter_output.content)



# Task for the Logic Reviewer
logic_reviewer_prompt = ChatPromptTemplate.from_template("""
Based on the structured summary of the ABAP code, map out the business logic.
Focus on the sequence of operations and the decisions being made.
For example, describe the flow like: '1. Start. 2. Loop 5 times. 3. Inside loop, check if counter is even. 4. If even, do X. 5. If odd, do Y. 6. End loop. 7. End.'

Structured Summary:
---
{summary}
---

Return a step-by-step description of the program's logic flow, highlighting decision points and repeated processes.
""")

logic_reviewer_chain = logic_reviewer_prompt | llm

# Run the chain with the output from the interpreter
logic_reviewer_output = logic_reviewer_chain.invoke({"summary": interpreter_output.content})

print(logic_reviewer_output.content)

# Task for the Diagram Blocks Generator
diagram_blocks_generator_prompt = ChatPromptTemplate.from_template("""
Convert the step-by-step logic flow into a list of abstract diagram blocks.
Use standard flowchart notation:
- 'Start' for the beginning
- 'End' for the end
- 'Process' for an action (e.g., 'Initialize variables', 'Write message')
- 'Decision' for a condition (e.g., 'Is counter even?')
- 'IO' for any input/output operations.
- 'Loop' for start/end of loops.

Logic Flow:
---
{logic_flow}
---

Define the connections between these blocks.
Return a list of objects or structured text defining each diagram block (e.g., {{id: 'A', type: 'Start', label: 'Start Program'}}), and the connections between them (e.g., 'A --> B').
""")

diagram_blocks_generator_chain = diagram_blocks_generator_prompt | llm

# Run the chain with the output from the logic reviewer
diagram_blocks_output = diagram_blocks_generator_chain.invoke({"logic_flow": logic_reviewer_output.content})

print(diagram_blocks_output.content)



# Task for the Diagram Generator
diagram_generator_prompt = ChatPromptTemplate.from_template("""
Generate the Mermaid code for a flowchart based on a natural language description.
The diagram should represent the described process, with correct syntax for nodes and connections.

Diagram Blocks:
---
{diagram_blocks}
---

Return a single code block containing the complete, syntactically correct Mermaid code for the UML activity diagram.
""")

diagram_generator_chain = diagram_generator_prompt | llm

# Run the chain with the output from the diagram blocks generator
diagram_generator_output = diagram_generator_chain.invoke({"diagram_blocks": diagram_blocks_output.content})

print(diagram_generator_output.content)



# Task for the Manager
manager_prompt = ChatPromptTemplate.from_template("""
Review the generated MermaidJS code. Compare it against the original ABAP code's logic to ensure accuracy and appropriate detail.
Do check the length and complexity of the diagram as it should neither be too small nor too large or complex but it does not mean that you make it incomplete. The graph should be complete and should not miss any important logic.
The diagram should clearly show the main loop, the conditional branch (even/odd check), and the subroutine call.
It should not be cluttered with unnecessary details like variable declarations.
If the diagram is accurate, provide the final MermaidJS code block as your final answer. If not, provide feedback (though for this run, assume it's correct).

Original ABAP Code for reference:
---
{abap_code}
---

MermaidJS Code:
---
{mermaid_code}
---

Return the final, approved MermaidJS code block, ready for rendering. If not accurate, provide feedback.
""")

manager_chain = manager_prompt | llm

# Run the chain with the output from the diagram generator and the original ABAP code
manager_output = manager_chain.invoke({
    "mermaid_code": diagram_generator_output.content,
    "abap_code": abap_code_example
})

print(manager_output.content)

# Comment ends

# Run the workflow step by step
interpreter_output = abap_interpreter_chain.invoke({"abap_code": abap_code_example})
logic_reviewer_output = logic_reviewer_chain.invoke({"summary": interpreter_output.content})
diagram_blocks_output = diagram_blocks_generator_chain.invoke({"logic_flow": logic_reviewer_output.content})
diagram_generator_output = diagram_generator_chain.invoke({"diagram_blocks": diagram_blocks_output.content})
manager_output = manager_chain.invoke({
    "mermaid_code": diagram_generator_output.content,
    "abap_code": abap_code_example
})

print("Final MermaidJS Code:\n", manager_output.content)



# # --- Execution ---

# if __name__ == "__main__":
#     print("🚀 Starting the ABAP to Diagram Crew with Gemini Pro...")
#     print("======================================================")
#     mermaid_code = abap_to_diagram_crew.kickoff(
#     inputs={
#         'abap_code': abap_code_example
#     }
# )

#     print("\n========================================")
#     print("✅ Crew execution finished!")
#     print("\nFinal Result (MermaidJS Code):")
#     print("----------------------------------------")
#     # The final result is the output of the last task
#     print(mermaid_code)
#     print("----------------------------------------")
