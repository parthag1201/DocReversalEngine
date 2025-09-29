import os
import re
from tasks import (
    analyze_code_task,
    foreign_dependency_task,
    functional_spec_task,
    technical_spec_task,
    initial_consolidation_task,
    output_review_feedback_task,
    final_specification_task,
)

# Map state references to task objects
TASK_MAP = {
    "analyze_code_task": analyze_code_task,
    "foreign_dependency_agent": foreign_dependency_task,
    "functional_spec_task": functional_spec_task,
    "technical_spec_task": technical_spec_task,
    "initial_consolidation_task": initial_consolidation_task,
    "output_review_feedback_task": output_review_feedback_task,
    "final_specification_task": final_specification_task,
}

AGENTS_FILE = r"FSTS_Langchain\MicroServicePython BTP\agents.py"
OUTPUT_DIR = r"FSTS_Langchain\MicroServicePython BTP\agents_yaml"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_agents_source():
    with open(AGENTS_FILE, "r", encoding="utf-8") as f:
        return f.read()


def extract_functions(source):
    # returns list of tuples (func_name, block)
    return re.findall(r"def (\w+)\(state\):(.+?)(?=\ndef |\Z)", source, re.S)


def clean(text: str) -> str:
    """Remove escape sequences, normalize indentation, and clean whitespace."""
    if not text:
        return ""
    # Convert escaped \n into actual newlines (in case they are present)
    text = text.replace("\\n", "\n")

    # Split lines, strip right spaces
    lines = [line.rstrip() for line in text.splitlines()]

    # Remove leading/trailing blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    # Normalize indentation (remove common leading indent)
    if lines:
        indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        min_indent = min(indents) if indents else 0
        lines = [line[min_indent:] if line.strip() else "" for line in lines]

    return "\n".join(lines)


def normalize_placeholders(text: str) -> str:
    """Convert {state['x']} → {x}"""
    return re.sub(r"{state\['([^']+)'\]}", r"{\1}", text)


def resolve_task_placeholders(prompt: str) -> str:
    """Replace task description/expected_output placeholders with content from tasks.py"""
    if not prompt:
        return ""
    for key, task in TASK_MAP.items():
        for quote in ("'", '"'):  # handle both cases
            prompt = prompt.replace(
                f"{{state[{quote}{key}{quote}].description}}", clean(task.description)
            )
            prompt = prompt.replace(
                f"{{state[{quote}{key}{quote}].expected_output}}", clean(task.expected_output)
            )
    return prompt


def extract_prompts(block):
    sys_match = re.search(r'"role":\s*"system".*?"content":\s*"""(.*?)"""', block, re.S)
    system_prompt = clean(sys_match.group(1)) if sys_match else ""

    user_match = re.search(r'full_user_prompt\s*=\s*f?"""(.*?)"""', block, re.S)
    user_prompt = clean(user_match.group(1)) if user_match else ""

    # resolve placeholders from tasks and normalize {state['x']} -> {x}
    user_prompt = resolve_task_placeholders(user_prompt)
    user_prompt = normalize_placeholders(user_prompt)

    return system_prompt, user_prompt


def extract_parameters(user_prompt):
    """Return parameter dict mapping name -> placeholder without quotes, e.g. abap_analysis -> {abap_analysis}"""
    if not user_prompt:
        return {}
    params = re.findall(r"{([A-Za-z0-9_]+)}", user_prompt)
    # keep insertion order and unique
    seen = []
    for p in params:
        if p not in seen:
            seen.append(p)
    return {p: f"{{{p}}}" for p in seen}


def write_yaml_manual(func_name, role, sys_prompt, user_prompt, params):
    """
    Write YAML manually to ensure:
     - system_prompt and user_prompt are block scalars (|-)
     - parameters values are unquoted placeholders like {template_text}
    """
    # normalize ROLE capitalization (keep as provided)
    file_path = os.path.join(OUTPUT_DIR, f"{func_name}.yaml")

    def block_scalar(text: str):
        """Return block scalar lines with proper two-space indent for content."""
        if text == "":
            return " |-\n"
        lines = text.splitlines()
        # prepare block with |- and each line indented by two spaces
        out = " |-\n"
        for ln in lines:
            if ln == "":
                out += "  \n"
            else:
                out += "  " + ln + "\n"
        return out

    with open(file_path, "w", encoding="utf-8") as f:
        # role
        f.write(f"role: {role}\n")

        # system_prompt
        f.write("system_prompt:" + block_scalar(sys_prompt))

        # user_prompt
        f.write("user_prompt:" + block_scalar(user_prompt))

        # parameters - write each as: key: {key}
        if params:
            f.write("parameters:\n")
            for k, v in params.items():
                # v is like "{template_text}" ; write without quotes
                f.write(f"  {k}: {v}\n")

    print(f"✅ Generated: {file_path}")


def main():
    source = load_agents_source()
    functions = extract_functions(source)

    for func_name, block in functions:
        sys_prompt, user_prompt = extract_prompts(block)
        # Use original function name but produce a nicer role by title-casing with spaces
        role = func_name.replace("_", " ").title()
        params = extract_parameters(user_prompt)
        write_yaml_manual(func_name, role, sys_prompt, user_prompt, params)


if __name__ == "__main__":
    main()
