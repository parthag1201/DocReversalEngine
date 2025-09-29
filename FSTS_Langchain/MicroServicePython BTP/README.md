
# 🚀 Project Setup Guide

This guide explains how to set up and run the project locally.

> ⚠️ **Prerequisite:** Make sure you have **Python 3.11** installed on your system.

---

## ✅ Step 1: Create and Activate a Virtual Environment

Open a terminal (e.g., PowerShell on Windows) and run the following commands:

```bash
# Create virtual environment
py -3.11 -m venv venv

# Allow script execution in current terminal session
Set-ExecutionPolicy Unrestricted -Scope Process

# Activate the virtual environment
venv\Scripts\activate
```

---

## ✅ Step 2: Install Dependencies

Install all required Python packages using:

```bash
pip install -r requirements.txt
```

---

## ✅ Step 3: 📦 WeasyPrint Installation

### On Windows

1. **Install MSYS2**

    - Download and install from [MSYS2 Installation](https://www.msys2.org/) using default options.

2. **Install Pango via MSYS2**

    - Open the MSYS2 shell and run:
      ```bash
      pacman -S mingw-w64-x86_64-pango
      ```

3. **Set Environment Variable**

    - Open `cmd.exe` and set the folder where DLLs are located:
      ```cmd
      set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin
      ```

### On Linux

- No additional steps are needed. All required dependencies are included in `requirements.txt`.
- Simply proceed with the standard installation instructions above.

---

## ✅ Step 4: Run the API Server

Start the FastAPI server with:

```bash
uvicorn api_server:app --reload
```

> The API will be live at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
> 
> 📚 API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🌐 API Endpoints

The server provides the following endpoints:
- **POST** `/code2fsts` - Convert ABAP code to FSTS documentation (asynchronous)
- **GET** `/code2fsts/status/{task_id}` - Check task status and retrieve results
- **GET** `/testfsts` - Test endpoint for development

### 📖 Postman Documentation

Complete API documentation with examples is available in our Postman workspace:
[FSTS Microservice API Documentation](https://dhruvkejri9mccain-3468531.postman.co/workspace/dhruv-kejriwal's-Workspace~86696e18-0d97-4b71-894f-f53f6232c608/collection/47354697-cee79f4a-9c41-49f1-9cfb-8716fd592b0d?action=share&creator=47354697)

---

## ⚙️ Customizing AI Agents

### Agent Prompts Configuration

The AI agents use configurable YAML prompt templates located in the `prompts/` directory:

```
prompts/
├── abap_code_analyst.yaml      # Code analysis prompts
├── functional_spec_drafter.yaml # Business specification prompts
├── technical_spec_writer.yaml  # Technical documentation prompts
├── foreign_dependency_agent.yaml # Dependency analysis prompts
├── manager_agent.yaml          # Workflow coordination prompts
└── output_reviewer.yaml        # Quality review prompts
```

### Editing Agent Prompts

1. **Navigate to the prompts directory**: `cd prompts/`

2. **Edit the desired agent's YAML file**: 
   ```bash
   # Example: Edit the functional spec drafter
   nano functional_spec_drafter.yaml
   ```

3. **Modify the prompt structure**: Each YAML file contains role definitions, goals, and backstory for the AI agents.

4. **Test your changes**: Restart the API server to apply the new prompts:
   ```bash
   uvicorn api_server:app --reload
   ```

### Prompt Template Structure

Each agent prompt file follows this structure:
```yaml
role: "Agent Role Name"
goal: "Primary objective of this agent"
backstory: |
  Detailed background and context for the agent's behavior
  and expertise area.
```

### Adding New Agents

1. Create a new YAML file in the `prompts/` directory
2. Update `agents.py` to include the new agent definition
3. Modify `tasks.py` to add tasks for the new agent
4. Update `workflow_graph.py` to include the agent in the workflow

---

## 🛠️ Notes

- Use `deactivate` to exit the virtual environment when you're done.
- If you face issues, make sure your Python version is exactly **Python 3.11**.
- The system requires a Google Gemini API key for AI functionality.
- PDF generation requires WeasyPrint to be properly installed.
