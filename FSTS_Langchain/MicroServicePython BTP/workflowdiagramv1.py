"""
This module generates a high-level workflow diagram (MermaidJS) from ABAP code files.
Exposes `generate_workflow_diagram` for external use.
"""

import os
import re
import warnings
from typing import List, Optional, Dict, Any
from tkinter import Tk
from tkinter.filedialog import askdirectory
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv
warnings.filterwarnings("ignore")

def _read_abap_folder(folder_path: str) -> Dict[str, Any]:
    """Read all .txt files from folder and return concatenated code and default html filename."""
    abap_code_example = ""
    all_files = os.listdir(folder_path)
    for filename in all_files:
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                abap_code_example += f"\n\n// File: {filename}\n" + f.read()

    folder_name = os.path.basename(folder_path.rstrip("/\\"))
    parent_folder = os.path.basename(os.path.dirname(folder_path.rstrip("/\\")))
    combined_name = f"{parent_folder}_{folder_name}"
    output_html_filename = re.sub(r'[\\/*?:"<>|]', "_", combined_name) + ".html"
    return {
        "abap_code": abap_code_example,
        "default_html": output_html_filename,
        "files": all_files,
    }

def _build_agents(llm: LLM):
    """Create and return all agents bound to the provided LLM."""
    abap_interpreter = Agent(
        role='ABAP Code Interpreter',
        goal='Analyze the provided ABAP code to understand its structure, main components (like FORMs, METHODs, FUNCTIONs), and the overall program flow including the includes that each abap code contains.',
        backstory=(
            "As a seasoned ABAP developer with decades of experience, you have an unparalleled ability to read and instantly "
            "comprehend even the most complex and archaic ABAP code. You can see beyond the syntax to the underlying business "
            "logic and program structure. Your task is to distill this complex code into a clear, structured summary that "
            "other agents can use."
            "You look several abap codes as one single entity as one single routine can include another routine and you should be able to understand the whole code as one single entity."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

# 2. Logic Reviewer Agent
# This agent takes the structured summary from the interpreter and focuses on the
# business logic. It identifies conditional statements (IF/ELSE, CASE), loops (DO, WHILE),
# and subroutine calls to map out the decision points and processes.
    logic_reviewer = Agent(
        role='Business Logic Analyst',
        goal='Review the structured summary of the ABAP code to identify and map out the core business logic, including conditional paths, loops, and subroutine calls.',
        backstory=(
            "You are a meticulous business analyst who specializes in reverse-engineering legacy systems. You have a keen eye for "
            "detail and can trace the flow of logic through complex code. Your strength is in identifying the decision points, "
            "data transformations, and processes that define how the program achieves its business objective. You translate "
            "technical flow into logical steps."
            "You focus mainly on business logic and you do not focus on the technicalities of the code."
            "You look at the code as a whole and you do not look at the code as a single routine but you look at the whole code as one web of different routines that are connected to each other. "
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

# 3. Diagram Blocks Generator Agent
# This agent translates the logical steps identified by the reviewer into
# abstract diagram blocks. It decides what should be a process, a decision,
# an input/output, etc., without worrying about the final syntax.
    diagram_blocks_generator = Agent(
        role='Workflow Diagram Architect',
        goal='Translate the identified business logic into a list of abstract diagram components (e.g., Start, End, Process, Decision, IO).',
        backstory=(
            "You are a systems architect who thinks visually. You can take a description of a process and immediately see it as a "
            "flowchart. You are an expert in UML and other diagramming methodologies, but your current focus is on defining the "
            "fundamental building blocks of the diagram—the nodes and their types—before they are rendered into a specific format."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

# 4. Diagram Generation Agent
# This agent takes the abstract blocks and generates the final diagram code
# in a specific format, in this case, MermaidJS.
# mermaid_docs_tool = ScrapeWebsiteTool(website_url='https://mermaid.js.org/intro/')

# Define the Mermaid Code Generator agent
    diagram_generator = Agent(
        role='Mermaid Code Generator',
        goal='Generate syntactically correct Mermaid code for various diagrams from a natural language description.',
        backstory=(
            "You are an expert in creating diagrams-as-code using Mermaid. You have a deep understanding of Mermaid's syntax "
            "You know the latest syntax of MermaidJS and its common syntax errors and you have always have been known to give the perfect Mermaid code without any errors especially you should not use parantheses inside the each code block of MemaidJS code. "
            "You also do not make the error of using quote inside the code block of MermaidJS code. "
            "for generating a wide variety of diagrams, including flowcharts, sequence diagrams, Gantt charts, and more. "
            "You can translate natural language descriptions or structured data into clean, readable, and accurate Mermaid code. "
            "You often consult the official Mermaid documentation to ensure you are using the latest and most effective features."
        ),
        # The tool that allows the agent to scrape/read websites
        # tools=[mermaid_docs_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm # Pass your configured LLM instance here
    )


# 5. Manager Agent (Quality Control)
# This agent acts as the final quality gate. It reviews the generated diagram
# against the initial code to ensure it's a faithful representation—not too
# detailed (e.g., diagramming every single line) and not too high-level
# (e.g., missing critical logic branches).
    manager = Agent(
        role='Quality Assurance Manager',
        goal='Review the final MermaidJS diagram to ensure it accurately represents the original ABAP code\'s logic without being overly complex or too simplistic. Provide the final, approved diagram code.',
        backstory=(
            "With a dual background in software development and project management, you are the ultimate quality gatekeeper. "
            "You ensure that the final product meets the initial requirements. Your job is to look at the generated diagram and the "
            "original code and ask: 'Does this diagram help a developer or analyst understand the code's workflow?' You have the final "
            "say on whether the diagram is approved."
            "You as manager expect the diagram to be a high level diagram with no or minimal technicalities for the end user since its just a addition to FS and should not act as replacement for FS. "
        ),
        verbose=True,
        allow_delegation=True,
        llm=llm
    )
    return abap_interpreter, logic_reviewer, diagram_blocks_generator, diagram_generator, manager

def _build_tasks(abap_code_example: str, agents):
    abap_interpreter, logic_reviewer, diagram_blocks_generator, diagram_generator, manager = agents
    interpretation_task = Task(
        description=f"""
        Analyze the following ABAP code. Identify the main program events (like START-OF-SELECTION),
        loops (DO/WHILE), conditional logic (IF/ELSE), and subroutine calls (PERFORM).
        Create a clear, summarized and breif list of these structural components and their sequence.
        You consider all different abap codes for subroutines as a part of a single routine entity.
        Summarize the nested loops to outline the common objective.
        Try to keep the details breif yet concise and summarize the details as much as possible to avoid more technical details.

        ABAP Code:
        ---
        {abap_code_example}
        ---
        """,
        expected_output="A structured text summary outlining the main execution flow, loops, conditions, and subroutine calls in the ABAP code.",
        agent=abap_interpreter
    )

# Task for the Logic Reviewer
    logic_review_task = Task(
        description="""
        Based on the structured summary of the ABAP code, map out the business logic.
        Focus on the sequence of operations and the decisions being made.
        Extract the logic in a step-by-step manner considering all the subroutines as a part of single routine entity.
        Try to keep the details breif yet concise and summarize the details as much as possible to avoid more technical details, keep it very high-level for the end user.

        """,
        expected_output="A step-by-step description of the program's logic flow, highlighting decision points and repeated processes.",
        agent=logic_reviewer,
        context=[interpretation_task]
    )

# Task for the Diagram Blocks Generator
    block_generation_task = Task(
        description="""
        Convert the step-by-step logic flow into a list of abstract diagram blocks.
        Use standard flowchart notation:
        - 'Start' for the beginning
        - 'End' for the end
        - 'Process' for an action (e.g., 'Initialize variables', 'Write message')
        - 'Decision' for a condition (e.g., 'Is counter even?')
        - 'IO' for any input/output operations.
        - 'Loop' for start/end of loops.

        Club multiple Process, Decision, and IO blocks into single blocks where possible to limit the diagram yet showcase a overview.
        Try to reduce the blocks and merge basic blocks of process and decision into single blocks where possible.
        Define the connections between these blocks.
        """,
        expected_output="A list of objects or a structured text defining each diagram block (e.g., {id: 'A', type: 'Start', label: 'Start Program'}), and the connections between them (e.g., 'A --> B').",
        agent=diagram_blocks_generator,
        context=[logic_review_task]
    )

# Task for the Diagram Generator
    diagram_generation_task = Task(
        description="""
        Generate the Mermaid code for a flowchart based on a natural language description.
        The diagram should represent a simple user login process, with correct syntax for nodes and connections.
        The flowchart should start with a user entering their credentials.
        The mermaid JS code produced should avoid basic syntax error like using parentheses inside each Mermaid node blocks which needs to avoided as it is found frequently in the output of the previous agents.
        There should be no parantheses inside the mermaid codes of nodes no matter what, it causes a syntax error in the MermaidJS diagram rendering which needs to be avoided at all costs.
        """,
        expected_output="A single code block containing the complete, syntactically correct  Mermaid code for the UML activity diagram.",
        agent=diagram_generator,
        context=[block_generation_task]
    )

# Task for the Manager
    manager_review_task = Task(
        description=f"""
        Review the generated MermaidJS code. Compare it against the original ABAP code's logic to ensure accuracy and appropriate detail.
        Do check the length and complexity of the diagram as it should neither be too small nor too large or complex but it does not mean that you make it incomplete. The graph should be complete and should not miss any important logic.
        The diagram should clearly show the main loop, the conditional branch (even/odd check), and the subroutine call.
        It should not be cluttered with unnecessary details like variable declarations.
        Also check the final mermaid JS code that it should contain parantheses inside the each code block of MemaidJS code and it should not contain quotes inside the code block of MermaidJS code.
        If the diagram is accurate, provide the final MermaidJS code block as your final answer. If not, provide feedback (though for this run, assume it's correct).
        Do keep in mind that the diagram is a high-level overview and should not include every technical detail.
        The workflow diagram should not act as a replacement for the functional specification (FS) but should be an addition to it.
        Original ABAP Code for reference:
        ---
        {abap_code_example}
        ---
        """,
        expected_output="The final, approved MermaidJS code block, ready for rendering.",
        agent=manager,
        context=[diagram_generation_task]
    )
    return interpretation_task, logic_review_task, block_generation_task, diagram_generation_task, manager_review_task

def generate_workflow_diagram(
    folder_path: str,
    *,
    output_html_filename: Optional[str] = None,
    save_html: bool = True,
    save_png_via_hcti: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Generate a MermaidJS workflow diagram from ABAP code files in a folder.

    Args:
        folder_path: Path to a folder containing .txt ABAP files.
        output_html_filename: Optional output HTML filename. Defaults to a name derived from folder.
        save_html: Whether to save the rendered Mermaid HTML file.
        save_png_via_hcti: Whether to create a PNG via HCTI API (uses env HCTI_USER_ID/HCTI_API_KEY).
        verbose: If True, prints brief progress.

    Returns:
        dict with keys: 'mermaid_code' (str), 'html_path' (Optional[str]), 'png_path' (Optional[str]), 'html_content' (str)
    """
    load_dotenv()
    apiKey = os.getenv("GOOGLE_API_KEY3") or os.getenv("GOOGLE_API_KEY")

    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    read_info = _read_abap_folder(folder_path)
    abap_code_example: str = read_info["abap_code"]
    default_html_name: str = read_info["default_html"]
    if verbose:
        try:
            print(f"Read {len(read_info['files'])} files from folder.")
        except Exception:
            pass

    # Initialize LLM lazily here so imports at module import time are light
    llm = LLM(
        model="gemini/gemini-2.5-pro",
        verbose=True,
        temperature=0.5,
        api_key=apiKey,
    )

    agents = _build_agents(llm)
    tasks = _build_tasks(abap_code_example, agents)
    abap_interpreter, logic_reviewer, diagram_blocks_generator, diagram_generator, manager = agents
    interpretation_task, logic_review_task, block_generation_task, diagram_generation_task, manager_review_task = tasks

    crew = Crew(
        agents=[abap_interpreter, logic_reviewer, diagram_blocks_generator, diagram_generator, manager],
        tasks=[interpretation_task, logic_review_task, block_generation_task, diagram_generation_task, manager_review_task],
        process=Process.sequential,
        verbose=True,
    )

    if verbose:
        print("Starting crew execution...")
    mermaid_code = crew.kickoff(inputs={'abap_code': abap_code_example})
    if verbose:
        print("Crew execution finished.")

    def remove_first_and_last_line(text: str) -> str:
        lines = text.splitlines()
        if len(lines) <= 2:
            return ''
        return '\n'.join(lines[1:-1])

    final_mermaid = remove_first_and_last_line(str(mermaid_code))

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\">
  <title>Mermaid Diagram</title>
  <script type=\"module\">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true }});
  </script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 16px; }}
  </style>
  </head>
<body>
  <div class=\"mermaid\">{final_mermaid}</div>
  </body>
</html>
"""

    html_path = None
    png_path = None
    if save_html:
        html_name = output_html_filename or default_html_name
        html_path = os.path.abspath(html_name)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        if verbose:
            print(f"HTML saved: {html_path}")

    if save_png_via_hcti and html_path:
        import requests
        HCTI_API_USER_ID = os.getenv("HCTI_USER_ID")
        HCTI_API_KEY = os.getenv("HCTI_API_KEY")
        if not (HCTI_API_USER_ID and HCTI_API_KEY):
            if verbose:
                print("HCTI credentials not found in env; skipping PNG generation.")
        else:
            image_filename = os.path.splitext(html_path)[0] + ".png"
            response = requests.post(
                url="https://hcti.io/v1/image",
                data={'html': html_content},
                auth=(HCTI_API_USER_ID, HCTI_API_KEY),
                verify=False,
            )
            if response.status_code == 200:
                image_url = response.json()['url']
                image_data = requests.get(image_url, verify=False).content
                with open(image_filename, "wb") as f:
                    f.write(image_data)
                png_path = os.path.abspath(image_filename)
                if verbose:
                    print(f"PNG saved: {png_path}")
            else:
                if verbose:
                    print(f"HCTI error: {response.status_code} {response.text}")

    return {
        'mermaid_code': str(mermaid_code),
        'html_path': html_path,
        'png_path': png_path,
        'html_content': html_content,
    }

def generate_workflow_html(abap_code_input: str, *, verbose: bool = False) -> str:
    """Generate HTML (with MermaidJS) from provided ABAP code string; do not save to disk.

    Args:
        abap_code_input: The ABAP code content as a single string.
        verbose: If True, print minimal progress.

    Returns:
        HTML string embedding the Mermaid diagram generated from the code.
    """
    load_dotenv()
    apiKey = os.getenv("GOOGLE_API_KEY3") or os.getenv("GOOGLE_API_KEY")

    # Initialize LLM
    llm = LLM(
        model="gemini/gemini-2.5-pro",
        verbose=True,
        temperature=0.5,
        api_key=apiKey,
    )

    agents = _build_agents(llm)
    tasks = _build_tasks(abap_code_input, agents)
    abap_interpreter, logic_reviewer, diagram_blocks_generator, diagram_generator, manager = agents
    interpretation_task, logic_review_task, block_generation_task, diagram_generation_task, manager_review_task = tasks

    crew = Crew(
        agents=[abap_interpreter, logic_reviewer, diagram_blocks_generator, diagram_generator, manager],
        tasks=[interpretation_task, logic_review_task, block_generation_task, diagram_generation_task, manager_review_task],
        process=Process.sequential,
        verbose=True,
    )

    if verbose:
        print("Starting crew execution...")
    mermaid_code = crew.kickoff(inputs={'abap_code': abap_code_input})
    if verbose:
        print("Crew execution finished.")

    def remove_first_and_last_line(text: str) -> str:
        lines = text.splitlines()
        if len(lines) <= 2:
            return ''
        return '\n'.join(lines[1:-1])

    final_mermaid = remove_first_and_last_line(str(mermaid_code))

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\">
  <title>Mermaid Diagram</title>
  <script type=\"module\">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true }});
  </script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 16px; }}
  </style>
  </head>
<body>
  <div class=\"mermaid\">{final_mermaid}</div>
  </body>
</html>
"""
    return html_content

# --- CLI/Script mode: optional interactive folder picker ---
if __name__ == "__main__":
    try:
        folder_path = askdirectory(title="Select Folder Containing ABAP Code Files")
    except Exception:
        folder_path = None

    if not folder_path:
        print("No folder selected.")
    else:
        print("🚀 Starting the ABAP to Diagram Crew with Gemini Pro...")
        print("======================================================")
        result = generate_workflow_diagram(folder_path, save_html=True, save_png_via_hcti=False, verbose=True)
        print("\nFinal Result (MermaidJS Code):")
        print("----------------------------------------")
        print(result['mermaid_code'])
        print("----------------------------------------")
        if result['html_path']:
            print(f"HTML file saved as: {result['html_path']}")