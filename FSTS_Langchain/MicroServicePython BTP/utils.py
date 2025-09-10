from collections import defaultdict
import os
import re
import markdown2
# from weasyprint import HTML, CSS
import logging
from fontTools.misc.loggingTools import configLogger
import yaml
from xhtml2pdf import pisa

# --- Disable fontTools internal logging completely ---
configLogger(level=logging.CRITICAL)

# --- Also silence root-level loggers for good measure ---
logging.getLogger('fontTools').setLevel(logging.CRITICAL)
logging.getLogger('weasyprint').setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

token_usage_history = []  # Global list to collect token usage from all agent steps


def load_prompt(agent_name: str):
    """Load a prompt definition from prompts/{agent_name}.yaml"""
    path = os.path.join("prompts", f"{agent_name}.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def format_user_prompt(prompt_def, state):
    params = {key: state[key] for key in prompt_def.get("parameters", {})}
    return prompt_def["user_prompt"].format(**params)

def parse_route(content):
    """Extract ROUTE directive from model output."""
    if isinstance(content, list):
        if all(isinstance(item, dict) and "text" in item for item in content):
            content = " ".join(item["text"] for item in content)
        else:
            content = " ".join(map(str, content))
    elif not isinstance(content, str):
        content = str(content)

    match = re.search(r"\[ROUTE:\s*(\w+)\]", content)
    return match.group(1) if match else "output_reviewer"

# Utility to export a LangGraph graph to PNG
def export_graph_png(app, filename):
    # Directly get PNG bytes
    print(type(app.get_graph().draw_mermaid_png()))
    png_bytes = app.get_graph().draw_mermaid_png()
    
    with open(filename, "wb") as f:
        f.write(png_bytes)
    
    print(f"✅ Graph exported to {filename}")

def add_token_usage(response, agent_name):
    """
    Adds token usage for an agent step to the global history using usage_metadata.
    """
    usage = getattr(response, "usage_metadata", None)
    if usage:
        token_usage_history.append({'agent': agent_name, 'usage': usage})

def print_total_token_usage(token_usage_history):
    total_tokens = defaultdict(int)
    for entry in token_usage_history:
        usage = entry['usage']
        for k, v in usage.items():
            if isinstance(v, int):
                total_tokens[k] += v
            elif isinstance(v, dict):
                # Flatten nested details like 'input_token_details' and 'output_token_details'
                for sub_k, sub_v in v.items():
                    flat_key = f"{k}.{sub_k}"  # e.g., input_token_details.cache_read
                    total_tokens[flat_key] += sub_v
    print("\nTotal token usage by type:")
    for k, v in total_tokens.items():
        print(f"{k}: {v}")

def logging_wrapper(fn, name):
    def wrapped(state):
        print(f"\n🟦 Running node: {name}")
        print(f"🔷 Input state: {state}")

        before_usage_count = len(token_usage_history)
        result = fn(state)
        
        # Print the last prompt given to the agent, if present (after fn runs)
        last_prompt = result.get('last_user_prompt', None)
        if last_prompt:
            print(f"📝 Prompt sent to agent:\n{last_prompt}\n")

        print(f"🟩 Output from {name}: {result}\n")

        # Print token usage for this run (if any new usage was added)
        new_usages = token_usage_history[before_usage_count:]
        if new_usages:
            print(f"🟨 Token usage for {name}:")
            for entry in new_usages:
                print(f"    {entry['agent']}: {entry['usage']}")
        else:
            print(f"🟨 Token usage for {name}: No new usage recorded.")

        return result

    return wrapped
    # def wrapped(state):
    #     return fn(state)
    # return wrapped

def clean_markdown(md: str) -> str:
    lines = md.splitlines()
    cleaned = []
    removed = []   # keep track of removed lines
    started = False

    ai_phrases = [
        r'as the project manager',
        r'here is the consolidated specification document',
        r'as\s+(an|a)\s+ai',
        r'i have reviewed the feedback',
        r'facilitated discussions',
        r'the following document is',
        r'this version is now ready',
        r'final, consolidated functional',
        r'\*\*\*',
        r'^ai:', r'^assistant:', r'^system:', r'^human:',
    ]
    ai_re = re.compile('|'.join(ai_phrases), re.IGNORECASE)

    for line in lines:
        l = line.strip()
        if l.lower().startswith('[route:'):
            removed.append(line)
            continue

        if started:
            cleaned.append(line)
            continue

        if (
            l.startswith('#')
            or l.startswith('**Page')
            or l.startswith('|')
            or l.lower().startswith('table of contents')
            or l.lower().startswith('###')
        ):
            started = True
            cleaned.append(line)
            continue

        if ai_re.search(l):
            removed.append(line)
            continue

        if not l:
            removed.append(line)
            continue

        started = True
        cleaned.append(line)

    # strip leading/trailing empty lines
    while cleaned and not cleaned[0].strip():
        removed.append(cleaned.pop(0))
    while cleaned and not cleaned[-1].strip():
        removed.append(cleaned.pop())

    # Print what was removed
    if removed:
        print("=== Removed Lines ===")
        for r in removed:
            print(r)
        print("=====================\n")

    return '\n'.join(cleaned) + "\n"

# def convert_markdown_to_pdf_old(markdown_file: str, output_pdf: str):
#     if not os.path.exists(markdown_file):
#         raise FileNotFoundError(f"File not found -> '{markdown_file}'")

#     with open(markdown_file, 'r', encoding='utf-8') as f:
#         markdown_content = f.read()

#     html = markdown2.markdown(markdown_content, extras=[
#         "fenced-code-blocks",
#         "tables",
#         "strike",
#         "cuddled-lists",
#         "header-ids",
#         "code-friendly"
#     ])

#     css = """
# @page {
#     size: A4;
#     margin: 1in 0.7in 1.1in 0.7in;
#     @bottom-center {
#         content: "Page " counter(page) " of " counter(pages);
#         font-size: 11pt;
#         color: #444;
#         font-family: Arial, sans-serif;
#     }
# }
# body {
#     font-family: Arial, sans-serif;
#     padding: 0;
#     line-height: 1.6;
# }
# h1, h2, h3 {
#     color: #111;
# }
# table {
#     width: 100%;
#     border-collapse: collapse;
#     margin: 1em 0;
#     font-size: 11pt;
# }
# th, td {
#     border: 1px solid #bbb;
#     padding: 8px;
#     color: #000;
# }
# th {
#     background-color: #f2f2f2;
# }
# pre {
#     background-color: #f5f5f5;
#     padding: 12px;
#     border-radius: 6px;
#     font-family: monospace;
#     white-space: pre-wrap;
#     font-size: 10pt;
# }
# hr {
#     border: none;
#     height: 1px;
#     background: #ccc;
#     margin: 2em 0;
# }
# ul, ol {
#     margin-left: 1.5em;
# }
# """
#     full_html = f"<html><head><meta charset='utf-8'></head><body>{html}</body></html>"

#     HTML(string=full_html).write_pdf(output_pdf, stylesheets=[CSS(string=css)])
#     return output_pdf

def convert_markdown_to_pdf(markdown_file: str, output_pdf: str):
    """
    Convert markdown to PDF using xhtml2pdf.
    Install: pip install xhtml2pdf markdown2
    Pure Python solution, works everywhere.
    """    
    if not os.path.exists(markdown_file):
        raise FileNotFoundError(f"File not found -> '{markdown_file}'")

    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    html = markdown2.markdown(markdown_content, extras=[
        "fenced-code-blocks",
        "tables",
        "strike",
        "cuddled-lists",
        "header-ids",
        "code-friendly"
    ])

    # xhtml2pdf specific CSS
    css = """
    <style>
    @page {
        size: A4;
        margin: 2.5cm 1.8cm 2.8cm 1.8cm;
        @frame footer {
            -pdf-frame-content: footerContent;
            bottom: 1cm;
            margin-left: 1cm;
            margin-right: 1cm;
            height: 1cm;
        }
    }
    body {
        font-family: Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
    }
    h1 { font-size: 24pt; color: #111; margin-top: 0; }
    h2 { font-size: 18pt; color: #111; }
    h3 { font-size: 14pt; color: #111; }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        -pdf-keep-with-next: true;
    }
    th, td {
        border: 1px solid #bbb;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    pre {
        background-color: #f5f5f5;
        padding: 12px;
        border: 1px solid #ddd;
        font-family: Courier, monospace;
        font-size: 9pt;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    code {
        background-color: #f5f5f5;
        padding: 2px 4px;
        font-family: Courier, monospace;
        font-size: 9pt;
    }
    hr {
        border: none;
        height: 1px;
        background-color: #ccc;
        margin: 2em 0;
    }
    ul, ol {
        margin-left: 1.5em;
    }
    li {
        margin-bottom: 0.5em;
    }
    </style>
    """
    
    full_html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        {css}
    </head>
    <body>
        {html}
        <div id="footerContent" style="text-align: center; font-size: 10pt; color: #444;">
            Page <pdf:pagenumber/> of <pdf:pagecount/>
        </div>
    </body>
    </html>
    """
    
    # Create PDF
    with open(output_pdf, "w+b") as output_file:
        pisa_status = pisa.CreatePDF(
            full_html,
            dest=output_file,
            encoding='utf-8'
        )
    
    if pisa_status.err:
        raise Exception(f"Error creating PDF: {pisa_status.err}")
    
    return output_pdf

def process_markdown(md_file: str):
    # Step 1: Read and clean
    with open(md_file, "r", encoding="utf-8") as f:
        raw = f.read()
    cleaned = clean_markdown(raw)

    # Step 2: Overwrite the cleaned markdown (optional: save separately instead)
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(cleaned)

    # Step 3: Convert to PDF (same folder, same name but .pdf)
    base, _ = os.path.splitext(md_file)   # <-- safe for .txt or .md
    pdf_file = base + ".pdf"
    convert_markdown_to_pdf(md_file, pdf_file)
    print(f"✅ PDF saved at {pdf_file}")