
# 🚀 Project Setup Guide

This guide explains how to set up and run the project locally.

> ⚠️ **Prerequisite:** Make sure you have **Python 3.8** installed on your system.

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

## ✅ Step 3: Run the API Server

Start the FastAPI server with:

```bash
uvicorn api_server:app --reload
```

> The API will be live at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🛠️ Notes

- Use `deactivate` to exit the virtual environment when you're done.
- If you face issues, make sure your Python version is exactly **3.8**.
