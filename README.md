# DocReversalEngine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Reverse-engineering comprehensive business and technical documentation from source code using a multi-agent AI system.

---

## 🚀 Overview

Have you ever been handed a piece of legacy code with little to no documentation? The **DocReversalEngine** is a powerful solution designed to tackle this exact problem. It leverages a sophisticated multi-agent system, powered by **Google's Gemini** and the `crewai` framework, to analyze source code (initially ABAP) and automatically generate high-quality **Functional Specification (FS)** and **Technical Specification (TS)** documents.

This engine simulates a real-world documentation team, including analysts, writers, and reviewers, to produce documents that are not only technically accurate but also clear, business-relevant, and professionally formatted.

---

## ✨ Key Features

* **Automated Document Generation**: Translates complex source code into easy-to-understand FS and TS documents.
* **Multi-Agent Workflow**: Utilizes a crew of specialized AI agents to handle analysis, drafting, consolidation, review, and finalization, ensuring a comprehensive and refined output.
* **Iterative Refinement**: Incorporates a built-in review and feedback loop where a "Business Knowledge" agent critiques the documents, which are then revised to meet business requirements.
* **Dynamic & Flexible**: Reads source code from text files and uses professional templates from PDF documents to structure the output.
* **Technology**: Built with Python, `crewai`, `langchain`, and powered by Google's Generative AI models.

---

## ⚙️ How It Works

The engine employs a sequential workflow where each AI agent performs a specific task, building upon the work of the previous agent.

1.  **Code Analysis**: The `Senior ABAP Code Analyst` dissects the provided source code, extracting key details like data sources, selection screens, processing logic, and output structures.
2.  **Initial Drafting**:
    * The `Business Systems Analyst` translates the technical analysis into a business-friendly Functional Specification.
    * The `Technical Documentation Specialist` creates a detailed, developer-focused Technical Specification.
3.  **Consolidation**: The `Manager Agent` merges the initial FS and TS into a single document, preparing it for review.
4.  **Review & Feedback**: The `Output Reviewer`, acting as a business stakeholder, critically evaluates the consolidated document for clarity, business alignment, and completeness, providing actionable feedback.
5.  **Finalization**: The `Manager Agent` orchestrates the final revisions based on the reviewer's feedback, producing a polished, comprehensive, and approved specification document.

---

## 🗂️ Repository Structure

This repository showcases the evolution of the DocReversalEngine through several iterations:

* `FS_TS_Crew.ipynb`: The initial proof-of-concept with hardcoded ABAP code and document templates.
* `FS_TS_Crew_V1.ipynb`: An improved version demonstrating the full sequential workflow with more refined agent interactions.
* `FS_TS_Crew_V2.ipynb`: The latest and most powerful version. It dynamically reads code from a dedicated folder and uses a PDF template for formatting. **This is the main notebook to use.**

---

## 🏁 Getting Started

Follow these steps to run the DocReversalEngine on your own code.

### Prerequisites

* Python 3.x
* Jupyter Notebook
* A Google API Key with access to the Gemini models.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/parthag1201/DocReversalEngine.git](https://github.com/parthag1201/DocReversalEngine.git)
    cd DocReversalEngine
    ```

2.  **Install the required packages:**
    ```bash
    pip install crewai==0.28.8 crewai_tools==0.1.6 langchain_community==0.0.29 langchain_google_genai fpdf2 markdown2 PyPDF2
    ```

### Usage

1.  **Set up your API Key**: Make sure your Google API Key is set as an environment variable or is accessible via your Jupyter environment (e.g., using Colab's secrets manager).

2.  **Add Your Code**: Place the source code you want to analyze into the `code_files` directory. The engine will read all `.txt` files in this folder.

3.  **Provide a Template**: Add a `template.pdf` file to the root directory. This PDF will be used by the AI agents as a reference for structuring the final documents.

4.  **Run the Engine**: Open and run the `FS_TS_Crew_V2.ipynb` notebook.

5.  **Get the Output**: The final, consolidated specification document will be saved as `final_specifications.md` in the root directory.

---

## 📄 Example Output

Here is a snippet of a final generated document, showcasing the level of detail and professional formatting:

```markdown
# Consolidated Final Specification: Sales Analysis Report (Z_MCCAIN_SALES_ANALYSIS)

---

# Part 1: Functional Specification

---

### 1. Enhancement Narrative

#### 1.1 Request Details
This document provides the functional specification for an **enhancement** to the existing custom ABAP report...

#### 2.1.1 Objective
As a sales manager, I want to see the top N highest-value line items for a specific material to quickly identify major sales and support tactical decision-making.

---

# Part 2: Technical Specification

---

### 3.4.2. Subroutine: `get_sales_data`
This subroutine handles all database interaction.
* **Logic:** Executes a single `SELECT` statement to fetch the top N sales items from the `VBAP` table, sorted by net value.
* **ABAP Code Snippet:**
    ```abap
    FORM get_sales_data.
      SELECT vbeln, posnr, matnr, netwr, waerk
        FROM vbap
        INTO CORRESPONDING FIELDS OF TABLE gt_sales_data
        WHERE vbeln IN s_vbeln AND matnr IN s_matnr
        ORDER BY netwr DESCENDING
        UP TO p_top ROWS.
    ENDFORM.
    ```
