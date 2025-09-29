
# 🚀 FSTS Microservice for SAP BTP

A comprehensive microservice built for SAP Business Technology Platform (BTP) that automatically generates Functional and Technical Specification (FSTS) documents from ABAP code using advanced AI agents powered by Google Gemini.

## 📋 Overview

This microservice is part of the DocReversalEngine project and provides REST API endpoints to:
- Convert ABAP code to comprehensive FSTS documentation
- Generate workflow diagrams from business logic
- Connect to SAP HANA database for data persistence
- Deploy seamlessly on SAP BTP Cloud Foundry

### 🎯 Key Features

- **AI-Powered Documentation**: Uses Google Gemini Pro to analyze ABAP code and generate professional specifications
- **Multi-Agent Workflow**: Employs specialized AI agents for different aspects of documentation
- **SAP BTP Integration**: Native support for SAP HANA and BTP services
- **RESTful API**: Clean API endpoints for external integration
- **Asynchronous Processing**: Background task processing for large code analysis
- **PDF Generation**: Automatic conversion of markdown output to PDF format

---

## 🛠️ Prerequisites

> ⚠️ **Important:** Make sure you have **Python 3.11.x** installed on your system.

### Required Services (for SAP BTP deployment):
- SAP HANA database service
- SAP Destination service  
- SAP Authorization service
- Google Gemini API key

---

## ⚙️ Local Development Setup

### Step 1: Create and Activate a Virtual Environment

**Windows (PowerShell):**
```bash
# Create virtual environment
py -3.11 -m venv venv

# Allow script execution in current terminal session
Set-ExecutionPolicy Unrestricted -Scope Process

# Activate the virtual environment
venv\Scripts\activate
```

**macOS/Linux:**
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_google_gemini_api_key_here

# SAP HANA Configuration (for local testing)
host=your_hana_host
port=443
user=your_hana_user
password=your_hana_password
certificate=path_to_certificate.pem

# Optional: HTML to Image API (for PNG generation)
HCTI_USER_ID=your_hcti_user_id
HCTI_API_KEY=your_hcti_api_key
```

### Step 4: Run the API Server

```bash
# Development mode with auto-reload
uvicorn api_server:app --reload

# Production mode
python api_server.py
```

> 🌐 The API will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
> 
> 📚 API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🌐 API Endpoints

### POST `/code2fsts`
Convert ABAP code to FSTS documentation (asynchronous)

**Request Body:**
```json
{
  "input_b64": "base64_encoded_abap_code"
}
```

**Response:**
```json
{
  "status": "Processing",
  "task_id": "uuid-task-identifier"
}
```

### GET `/code2fsts/status/{task_id}`
Check task status and retrieve results

**Response (Processing):**
```json
{
  "status": "Processing",
  "base64_fsts": null
}
```

**Response (Completed):**
```json
{
  "status": "Completed",
  "base64_fsts": "base64_encoded_pdf_document"
}
```

### GET `/testfsts`
Test endpoint for development and SAP HANA connectivity

---

## 🚀 SAP BTP Deployment

### 1. Update `manifest.yml`

```yaml
---
applications:
- name: your-app-name
  random-route: true
  path: ./
  memory: 256M
  buildpacks: 
  - python_buildpack
  command: python api_server.py
  services:
  - your-hana-service
  - your-destination-service
  - your-auth-service
```

### 2. Deploy to Cloud Foundry

```bash
# Login to SAP BTP
cf login -a https://api.cf.your-region.hana.ondemand.com

# Deploy the application
cf push
```

### 3. Bind Required Services

```bash
# Bind HANA service
cf bind-service your-app-name your-hana-service

# Bind other services as needed
cf bind-service your-app-name your-destination-service
cf bind-service your-app-name your-auth-service

# Restart the application
cf restart your-app-name
```

---

## 🏗️ Architecture

The microservice uses a multi-agent architecture with the following components:

1. **ABAP Code Analyst**: Parses and understands ABAP code structure
2. **Functional Spec Drafter**: Creates business-focused documentation
3. **Technical Spec Writer**: Generates technical implementation details
4. **Manager Agent**: Coordinates the workflow and ensures quality
5. **Output Reviewer**: Validates and formats final output

### Workflow Process:
```
ABAP Code Input → Code Analysis → Foreign Dependencies → 
Functional Spec → Technical Spec → Consolidation → 
Review & Feedback → Final Specification (PDF)
```

---

## 🔧 Configuration Files

- `requirements.txt`: Python dependencies
- `runtime.txt`: Python runtime version for BTP deployment
- `Procfile`: Process definition for deployment
- `manifest.yml`: SAP BTP deployment configuration
- `prompts/*.yaml`: AI agent prompt configurations

---

## 🧪 Testing

```bash
# Run the test suite (if available)
python -m pytest test/

# Test API locally with curl
curl -X POST "http://localhost:8000/code2fsts" \
  -H "Content-Type: application/json" \
  -d '{"input_b64": "your_base64_encoded_abap_code"}'
```

---

## 🐛 Troubleshooting

### Common Issues:

1. **Python Version Mismatch**: Ensure you're using Python 3.11.x as specified in `runtime.txt`

2. **Missing API Key**: Make sure `GEMINI_API_KEY` is set in your environment variables

3. **HANA Connection Issues**: Verify your HANA service credentials and network connectivity

4. **Memory Issues on BTP**: Increase memory allocation in `manifest.yml` if needed

5. **Import Errors**: Run `pip install -r requirements.txt` to ensure all dependencies are installed

### Debugging:

Enable verbose logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

---

## 📁 Project Structure

```
MicroServicePython BTP/
├── api_server.py           # FastAPI application and endpoints
├── main.py                 # Core workflow orchestration
├── agents.py               # AI agent definitions
├── tasks.py                # Task definitions for agents
├── data_processor.py       # Data handling and processing
├── utils.py                # Utility functions
├── workflow_graph.py       # LangGraph workflow definition
├── workflowdiagramv1.py    # Workflow diagram generation
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python version specification
├── manifest.yml            # SAP BTP deployment config
├── Procfile               # Process definition
└── prompts/               # AI agent prompt templates
    ├── abap_code_analyst.yaml
    ├── functional_spec_drafter.yaml
    ├── technical_spec_writer.yaml
    └── ...
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is part of the DocReversalEngine repository. Please refer to the main repository license for details.

---

## 🔗 Related Projects

- **DocReversalEngine**: Main repository for document reverse engineering
- **FSTS_Crew**: CrewAI-based implementation for FSTS generation
- **Workflow**: Workflow diagram generation modules
