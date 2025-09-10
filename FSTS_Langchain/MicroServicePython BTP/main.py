import os
import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from data_processor import DataProcessor
from tasks import analyze_code_task, foreign_dependency_task, functional_spec_task, technical_spec_task, initial_consolidation_task, output_review_feedback_task, final_specification_task
# from agents import abap_code_analyst, functional_spec_drafter, technical_spec_writer, manager_agent, output_reviewer, final_output
from utils import token_usage_history, print_total_token_usage, export_graph_png
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import time
from workflow_graph import build_workflow


# --- User configuration ---
BASE_PATH = os.getcwd()

# --- Data loading ---
data_processor = DataProcessor(BASE_PATH)
RUN_FOLDER = data_processor.get_run_folder()
final_dir = data_processor.get_final_dir()
_, template_text = data_processor.get_data()

# --- LLM initialization ---
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
llm_model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=api_key)


# --- Main function ---
# This function will be called when running the script directly.
# It initializes the data processor, loads the code files, sets up the LLM,
# builds the workflow graph, and runs the workflow.
# The final output is saved to a markdown file in the last run output folder.
def main(code_input_b64=None, task_id=None):
   
    # --- Build the LangGraph StateGraph ---
    workflow = build_workflow()
    app = workflow.compile()

    # Export workflow graph as PNG using provided task_id (from API)
    # graph_png_path = os.path.join(final_dir, f"workflow_graph_{task_id}.png")
    # export_graph_png(app, graph_png_path)
    # print(f"✅ Workflow graph exported to {graph_png_path}")
    
    # --- Prepare data for workflow ---
    code_input_val = data_processor.read_code_files(code_input_b64=code_input_b64)
    template_text_val = data_processor.read_template_pdf()

    # --- Run the workflow ---
    initial_state = {
        "code_input": code_input_val,
        "template_text": template_text_val,
        "analyze_code_task": analyze_code_task,
        "foreign_dependency_agent": foreign_dependency_task,
        "functional_spec_task": functional_spec_task,
        "technical_spec_task": technical_spec_task,
        "initial_consolidation_task": initial_consolidation_task,
        "output_review_feedback_task": output_review_feedback_task,
        "final_specification_task": final_specification_task,
        "model": llm_model,
        "messages": [],
        "review_count": 0,
        "min_output_reviews": 1,
        "max_output_reviews": 2,
    }

    start_time = time.time()
    final_result = app.invoke(initial_state)
    success = True
    end_time = time.time()
    execution_time = end_time - start_time  # in seconds
    print(f"Execution time: {execution_time:.3f} seconds")
    print(token_usage_history)
    print_total_token_usage(token_usage_history)

    return final_result

def generate_final_messages(final_result):
    # Extract message(s) from final_result
    final_messages = final_result.get("manager_output", "")
    if isinstance(final_messages, BaseMessage):
        final_messages = final_messages.content
    elif isinstance(final_messages, list):
        final_messages = "\n\n".join(
            m.content if isinstance(m, BaseMessage) else str(m)
            for m in final_messages
        )
    else:
        final_messages = str(final_messages)
    return final_messages

output_path = os.path.join(final_dir, "final_specifications.md")

# --- For API/static testing and import: always define final_messages from file ---
try:
    with open(output_path, "r", encoding="utf-8") as f:
        final_messages = f.read()
except Exception:
    final_messages = ""

# --- For normal workflow run: Generate and save output ---
if __name__ == "__main__":
    final_result = main()
    final_messages = generate_final_messages(final_result)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_messages)
    print(f"✅ Saved to {output_path}")