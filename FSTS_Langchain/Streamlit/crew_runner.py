import os
import PyPDF2
from crewai import Agent, Task, Crew, Process, LLM

def run_crew(code_folder_path: str, template_pdf_path: str) -> str:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    llm = LLM(model="gemini/gemini-2.5-flash")
    # --- Read code_input from all .txt files in code_folder_path ---
    code_input = ""
    for filename in os.listdir(code_folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(code_folder_path, filename), "r", encoding="utf-8") as f:
                code_input += f.read() + "\n\n"
    # --- Read template_text from template_pdf_path ---
    template_text = ""
    try:
        with open(template_pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                template_text += page.extract_text() or ""
    except Exception as e:
        template_text = ""

    abap_code_analyst = Agent(
        role="Senior ABAP Code Analyst",
        goal="Dissect the provided ABAP  code to extract all technical details and the logic flow of the report."
             "Focus on identifying data sources, selection screens, core logic, and output structures."
             "You need to go through each and every section of report to the extent form where a good Functional and Technical specification document can be derived out of it"
             "This is the ABAP report code : '{code_files}'",
        backstory="""You are an expert ABAP developer with decades of experience. You have an exceptional eye for detail
        and can instantly understand the flow and structure of any ABAP program. Your task is to analyze the
        code and provide a structured, raw analysis for the documentation team.""",
        allow_delegation=False,
        verbose=True,
        llm=llm,
    )
    functional_spec_drafter = Agent(
        role="Business Systems Analyst",
        goal="Translate the technical analysis of an ABAP report into a clear and concise"
             "functional specification document for business stakeholders."
             "Refer to this professional template for creating a business specification document. '{template_text}'"
             "This is the ABAP code : {code_files} ",
        backstory="""You are a bridge between the technical team and the business. You excel at taking complex
        business challenges and oppurtunities and reframing it in terms of business processes and objectives. Your functional
        specifications are legendary for their clarity and business relevance, enabling stakeholders to
        understand exactly what all action items are required as the part of Functional specification of the program.""",
        allow_delegation=True,
        verbose=True,
        llm=llm,
    )
    technical_spec_writer = Agent(
        role="Technical Documentation Specialist",
        goal="""Create a comprehensive and detailed technical specification document based on the
        ABAP code analysis."""
        "Refer to this professional template for creating a business specification document. '{template_text}'",
        backstory="""You are a meticulous technical writer who specializes in creating documentation for developers by analysing the code and functional specifications.
        Your specifications are precise, well-structured, and follow industry best practices. Your work ensures
        that any developer can pick up the report for maintenance or enhancement with complete clarity
        on its internal workings.""",
        allow_delegation=True,
        verbose=True,
        llm=llm,
    )
    foreign_dependency_agent = Agent(
        role = "Foreign dependency Analyst",
        goal = """Foreign Dependency Extraction Specialist: Identify and extract all foreign dependencies from the provided ABAP code.
        This includes identifying any external tables, classes, or Join Queries of tables that the report relies on.
        """,
        backstory = """You are a meticulous analyst who specializes in identifying external dependencies in ABAP code.
        Your task is to extract all foreign dependencies, including external tables, classes, or Join Queries of tables that the report relies on.
        You will provide a structured list of these dependencies, including their names, versions, and any relevant documentation links.""",
        allow_delegation = True,
        verbose = True,
        llm = llm,
    )
    manager_agent = Agent(
        role='Manager Agent',
        goal='Oversee the reverse engineering of Functional and Technical Specifications documentation from ABAP codes, facilitate collaboration amongst your team and iteratively incorporate the feedbacks of Functional and Technical experts while creating this document and ensure final output meets all requirements.'
             'The FS and TS reports must contain all the important information extracted from the code for the business team to understand each and every ascpet of the code easily',
        backstory="""You are an experienced SAP S4 project manager with a deep understanding of software development life cycles and well versed with the good practises of SAP, Business needs and ABAP Development.
        You have good knowledge on SAP Functional processes like MTD, RTR, OTC and PTP.
        You excel at breaking down complex tasks, coordinating teams, incorporating feedback, and ensuring quality deliverables.
        You are adept at communicating with both technical and business stakeholders.""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
    )
    output_reviewer = Agent(
        role='Output Reviewer (Business Knowledge)',
        goal="""Review consolidated Functional and Technical Specifications and provide constructive feedback to the Manager Agent for refinement, focusing on business alignment and completeness.
        You have good knowledge on SAP Functional processes like MTD, RTR, OTC and PTP.
        The Functional and technical specifications document must be ehaustive enough to be able to create abap codes for those processes. So you need to perform all the checks according the best SAP coding practises and industry standards""",
        backstory="""You are a business stakeholder with a keen eye for detail and a deep understanding of the organizational goals and user needs.
        You critically evaluate specifications, ensuring they meet intended business objectives and provide actionable feedback for improvement.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )
    version_history_analyst = Agent(
        role="ABAP Metadata and Versioning Specialist",
        goal="""Accurately extract and structure the complete version history, author details, and related metadata
              from the ABAP code's header comment block (the 'flower box').""",
        backstory="""You are an SAP quality assurance analyst with an obsession for documentation standards and traceability.
                   You specialize in reading the header comments of development objects to understand their history,
                   purpose, and the transport requests associated with them. Your work is critical for creating
                   auditable and professional documentation.""",
        allow_delegation=False,
        verbose=True,
        llm=llm,
    )
    dependency_mapper = Agent(
        role="SAP Object Cross-Reference Analyst",
        goal="""Identify and catalogue all external dependencies referenced within the ABAP code, including database
              tables, views, function modules, classes, BAdIs, and other repository objects.""",
        backstory="""You are an SAP solution architect with a deep understanding of the ABAP repository and its landscape.
                   You can instantly spot cross-object references, creating a clear map of how a program interacts
                   with the wider SAP ecosystem. Your analysis is crucial for impact analysis and understanding the
                   program's true footprint.""",
        allow_delegation=False,
        verbose=True,
        llm=llm,
    )
    analyze_code_task = Task(
        description="""Analyze the following ABAP report code: '{code_files}'.
                       Your analysis must cover these key areas:
                       1.  **Data Sources:** Identify all database tables, views, or structures being used.
                       2.  **Selection Screen:** Detail all SELECT-OPTIONS and PARAMETERS, including their technical IDs and associated data elements.
                       3.  **Core Processing Logic:** Summarize the main logic blocks, including loops, conditionals (IF/CASE statements), and subroutine calls (PERFORM).
                       4.  **Data Output:** Describe how the final data is presented (e.g., ALV grid, classical report WRITE statements) and list the fields being displayed.""",
        expected_output="""A structured text document containing a raw, point-by-point technical breakdown of the ABAP report.
                           This output should be purely technical and serve as the foundational information for other agents.""",
        agent=abap_code_analyst,
    )
    functional_spec_task = Task(
        description="""Using the technical analysis provided by the ABAP Code Analyst, create a functional specification document.
                       The document should explain the report's purpose and functionality from a business user's perspective.
                       It must include:
                       1.  **Report Purpose:** A high-level summary of what the report achieves.
                       2.  **Selection Criteria:** Explain the input fields in simple business terms (e.g., "User can filter by Sales Document Number").
                       3.  **Processing Logic Summary:** Describe what the report does with the data in plain language (e.g., "The report calculates the total net value for the selected sales orders").
                       4.  **Output Description:** Describe the layout and columns of the final report from a user's point of view.""",
        expected_output="""A well-formatted functional specification document in Markdown. The language should be clear,
                           non-technical, and focused on the business value and utility of the report.""",
        agent=functional_spec_drafter,
    )
    foreign_dependency_task = Task(
        description = """Provide all the foreign dependencies of the ABAP code provided. This should include Join queries, external tables/classes/functions/methods references.
        This will help functional analyst to understand the various foreign dependencies of the code and include that in the functional specification document.
        """,
        expected_output = """A comprehensive and exhaustive report containing list of all the foreign dependencies like Tables, Join queries, etc.
        """,
        agent = foreign_dependency_agent
    )
    technical_spec_task = Task(
        description="""Using the detailed technical analysis from the ABAP Code Analyst, create a formal technical specification document.
                       This document must be structured for a developer audience and include:
                       1.  **Program Details:** Program ID, Title, and a brief technical overview.
                       2.  **Data Declarations:** List of key tables, internal tables, and complex variables.
                       3.  **Selection Screen Objects:** A table listing each selection screen field with its technical name and properties.
                       4.  **Detailed Logic Flow:** A step-by-step description of the program's execution logic, referencing specific subroutines and key logic blocks.
                       5.  **Output Details:** A technical breakdown of the output display, including the field catalog for ALV grids or the format of WRITE statements.""",
        expected_output="""A comprehensive technical specification document in Markdown. It should be precise, detailed, and
                           formatted professionally to serve as official technical documentation.""",
        agent=technical_spec_writer,
    )
    initial_consolidation_task = Task(
        description="""Consolidate the initial Functional and Technical Specifications into a single, cohesive document.
        Ensure both specifications are present and well-formatted for review.
        """,
        expected_output="A single Markdown document containing the initial Functional Specification and Technical Specification, clearly separated.",
        agent=manager_agent,
        context=[functional_spec_task, technical_spec_task],
        llm=llm,
    )
    output_review_feedback_task = Task(
        description="""Review the provided consolidated Functional and Technical Specifications.
        Focus on business alignment, clarity, completeness, and accuracy from a business perspective.
        Provide constructive feedback to the Manager Agent, detailing any required changes or improvements.
        The output should be a clear, concise, and structured list of actionable feedback points, not a final report.
        """,
        expected_output="A structured list of feedback points (e.g., bullet points, numbered list) for the Manager Agent to use for refining the specifications. Example: '- Section X needs more detail on Y. - Clarify business impact of Z. - Ensure consistency between FS and TS for ABC.'",
        agent=output_reviewer,
        context=[initial_consolidation_task],
        llm=llm,
    )
    final_specification_task = Task(
        description="""Based on the initial Functional and Technical Specifications and the feedback provided by the Output Reviewer,
        make necessary revisions to both specifications. Your goal is to produce the final, polished, and
        approved Functional and Technical Specifications in a single consolidated document.
        The output must contain the actual Functional Specification and Technical Specification,
        incorporating all valid feedback. Ensure clear separation between the FS and TS sections in the final output.
        """,
        expected_output="A single, comprehensive Markdown document containing the final, refined Functional Specification and Technical Specification, clearly separated (e.g., using distinct headings like '# Functional Specification' and '# Technical Specification') and incorporating all reviewer feedback.",
        agent=manager_agent,
        context=[initial_consolidation_task, output_review_feedback_task],
        llm=llm,
        output_file='final_specifications.md'
    )
    extract_version_history_task = Task(
        description="""Analyze the ABAP code in '{code_files}' to locate the header comment block (flower box).
                       1.  Parse the 'Revision Log' or 'Version History' section.
                       2.  Extract details for each entry: Version/Init. #, Author, Date, Description, and CTS#.
                       3.  Also, extract other key metadata like FS Document ID, TS Document ID, and Object Description.""",
        expected_output="""A structured Markdown section containing two parts:
                           1. A list of key metadata (FS ID, TS ID, Description).
                           2. A table detailing the complete version history with columns for Version, Author, Date,
                              Description, and CTS#. This output must be ready for direct insertion into a specification document.""",
        agent=version_history_analyst,
    )
    map_dependencies_task = Task(
        description="""Conduct a thorough scan of the ABAP code '{code_files}' to identify all external dependencies.
                       Your analysis must categorize these dependencies into the following groups:
                       1.  **Database Objects:** Tables and Views (from SELECT, TABLES, etc.).
                       2.  **Function Modules:** Called using 'CALL FUNCTION'.
                       3.  **Classes/Methods:** Instantiated or called using 'CREATE OBJECT' or 'CALL METHOD'.
                       4.  **Includes & External Subroutines:** References to other ABAP programs.
                       5.  **Data Dictionary (DDIC) Types:** Structures or data elements used in TYPE declarations.""",
        expected_output="""A clearly structured list of all identified foreign dependencies, grouped by category
                           (e.g., ### Database Tables, ### Function Modules). This list will serve as a
                           cross-reference appendix in the technical specification.""",
        agent=dependency_mapper,
    )
    abap_crew = Crew(
        agents=[
            abap_code_analyst,
            foreign_dependency_agent,
            functional_spec_drafter,
            technical_spec_writer,
            version_history_analyst,
            dependency_mapper,
            manager_agent,
            output_reviewer
        ],
        tasks=[
            analyze_code_task,
            foreign_dependency_task,
            functional_spec_task,
            technical_spec_task,
            extract_version_history_task,
            map_dependencies_task,
            initial_consolidation_task,
            output_review_feedback_task,
            final_specification_task
        ],
        process=Process.sequential,
    )
    result = abap_crew.kickoff(
        inputs={
            'code_files': code_input,
            'template_text': template_text
        }
    )
    return result
