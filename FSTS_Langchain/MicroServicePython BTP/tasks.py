# Task class definition
class Task:
    def __init__(self, description, expected_output, agent=None, context=None, llm=None, output_file=None):
        self.description = description
        self.expected_output = expected_output
        self.context = context or []
        self.output_file = output_file


# Task definitions
foreign_dependency_task = Task(
    description = """Provide all the foreign dependencies of the ABAP code provided. This should include Join queries, external tables/classes/functions/methods references.
    This will help functional analyst to understand the various foreign dependencies of the code and include that in the functional specification document.""",
    expected_output = """A comprehensive and exhaustive report containing list of all the foreign dependencies like Tables, Join queries, etc.""",
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
)

functional_spec_task = Task(
    description="""Using the technical analysis provided by the ABAP Code Analyst, create a functional specification document.
    The document should explain the report's purpose and functionality from a business user's perspective.
                   It must include:
                   1.  **Report Purpose:** A high-level summary of what the report achieves.
                   2.  **Selection Criteria:** Explain the input fields in simple business terms (e.g., \"User can filter by Sales Document Number\").
                   3.  **Processing Logic Summary:** Describe what the report does with the data in plain language (e.g., \"The report calculates the total net value for the selected sales orders\").
                   4.  **Output Description:** Describe the layout and columns of the final report from a user's point of view.""",
    expected_output="""A well-formatted functional specification document in Markdown. The language should be clear,
                       non-technical, and focused on the business value and utility of the report.""",
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
)

initial_consolidation_task = Task(
    description="""Consolidate the initial Functional and Technical Specifications into a single, cohesive document.
    Ensure both specifications are present and well-formatted for review.
    """,
    expected_output="A single Markdown document containing the initial Functional Specification and Technical Specification, clearly separated.",
    context=[functional_spec_task, technical_spec_task],
)

output_review_feedback_task = Task(
    description="""Review the provided consolidated Functional and Technical Specifications.
    Focus on business alignment, clarity, completeness, and accuracy from a business perspective.
    Provide constructive feedback to the Manager Agent, detailing any required changes or improvements.
    The output should be a clear, concise, and structured list of actionable feedback points, not a final report.
    """,
    expected_output="A structured list of feedback points (e.g., bullet points, numbered list) for the Manager Agent to use for refining the specifications. Example: '- Section X needs more detail on Y. - Clarify business impact of Z. - Ensure consistency between FS and TS for ABC.'",
    context=[initial_consolidation_task],
)

final_specification_task = Task(
    description="""Based on the initial Functional and Technical Specifications and the feedback provided by the Output Reviewer,
    make necessary revisions to both specifications. Your goal is to produce the final, polished, and 
    approved Functional and Technical Specifications in a single consolidated document.
    The output must contain the actual Functional Specification and Technical Specification,
    incorporating all valid feedback. Ensure clear separation between the FS and TS sections in the final output.
    """,
    expected_output="A single, comprehensive Markdown document containing the final, refined Functional Specification and Technical Specification, clearly separated (e.g., using distinct headings like '# Functional Specification' and '# Technical Specification') and incorporating all reviewer feedback.",
    context=[initial_consolidation_task, output_review_feedback_task],
    output_file='final_specifications.md'
)
