import base64, os, traceback, uuid, time
from fastapi import FastAPI, Body, BackgroundTasks
from pydantic import BaseModel
from main import main, generate_final_messages
from fastapi.middleware.cors import CORSMiddleware
from utils import process_markdown

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with UI5 domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = "outputs"
os.makedirs(OUTPUTS_DIR, exist_ok=True)
TASK_REGISTRY = os.path.join(OUTPUTS_DIR, "task_registry.txt")

def register_task(task_id: str):
    """Add a task with status 'Processing'."""
    now = int(time.time())
    with open(TASK_REGISTRY, "a", encoding="utf-8") as f:
        f.write(f"{task_id},{now},Processing\n")

def set_task_status(task_id: str, status: str):
    """Update the status of a task in the registry."""
    if not os.path.exists(TASK_REGISTRY):
        return
    lines = []
    with open(TASK_REGISTRY, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) != 3:
                continue
            tid, tstamp, _ = parts
            if tid == task_id:
                lines.append(f"{tid},{tstamp},{status}\n")
            else:
                lines.append(line)
    with open(TASK_REGISTRY, "w", encoding="utf-8") as f:
        f.writelines(lines)

def get_task_status_value(task_id: str):
    """Return the status of a task (Processing / Completed / Failed) or None."""
    if not os.path.exists(TASK_REGISTRY):
        return None
    expire_seconds = 3600 * 48
    now = int(time.time())
    found = None
    keep_lines = []
    with open(TASK_REGISTRY, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) != 3:
                continue
            tid, tstamp, status = parts
            tstamp = int(tstamp)
            if now - tstamp < expire_seconds:
                keep_lines.append(line)
                if tid == task_id:
                    found = status
            else:
                # Clean up expired files
                for ext in [".txt", ".pdf"]:
                    path = os.path.join(OUTPUTS_DIR, f"{tid}{ext}")
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except:
                            pass
    # Rewrite registry with only non-expired tasks
    with open(TASK_REGISTRY, "w", encoding="utf-8") as f:
        f.writelines(keep_lines)
    return found

def is_task_registered(task_id: str) -> bool:
    return get_task_status_value(task_id) is not None


# Response model for task creation
class TaskIdResponse(BaseModel):
    status: str
    task_id: str

# Start workflow in background, return task_id (POST, accepts base64 input)
@app.post("/code2fsts", response_model=TaskIdResponse)
def get_fsts_base64(background_tasks: BackgroundTasks, input_b64: str = Body(..., embed=True)):
    task_id = str(uuid.uuid4())
    
    def run_workflow(code_input_b64: str, task_id: str):
        try:
            final_result = main(code_input_b64=code_input_b64, task_id=task_id)
            final_messages = generate_final_messages(final_result)

            output_path = os.path.join(OUTPUTS_DIR, f"{task_id}.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_messages)

            process_markdown(output_path)  # creates PDF
            set_task_status(task_id, "Completed")
        except Exception as e:
            print(f"[ERROR] Workflow failed for task {task_id}")
            traceback.print_exc()  # prints the full error traceback
            set_task_status(task_id, "Failed")
    
    register_task(task_id)
    background_tasks.add_task(run_workflow, code_input_b64=input_b64, task_id=task_id)
    return {"status": "Processing", "task_id": task_id}

# Status/result endpoint
@app.get("/code2fsts/status/{task_id}")
def get_task_status(task_id: str):
    status = get_task_status_value(task_id)
    if status is None:
        return {"status": "NotFound", "detail": "Task does not exist or has expired.", "base64_fsts": None}
    elif status == "Completed":
        output_path = os.path.join(OUTPUTS_DIR, f"{task_id}.pdf")
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return {"status": "Completed", "base64_fsts": encoded}
        else:
            return {"status": "Error", "detail": "PDF missing.", "base64_fsts": None}
    elif status == "Failed":
        return {"status": "Failed", "detail": "Workflow encountered an error.", "base64_fsts": None}
    else:
        return {"status": "Processing", "base64_fsts": None}

# --- POST endpoint to accept base64 input and decode it ---
# @app.post("/code2fstsb64", response_model=FSTSResponse)
# def get_fsts_base64_with_input(input_b64: str = Body(..., embed=True)):
    # Decode base64 to string
    # decoded_str = base64.b64decode(input_b64.encode("utf-8")).decode("utf-8")
    # Example: pass decoded_str as code_input to main.py (requires main to accept arguments)
    # You would need to refactor main() to accept code_input as a parameter for this to work dynamically.
    # For now, just return the decoded string as a test (or adapt as needed):
    # final_result = main(code_input=decoded_str)
    # final_messages = generate_final_messages(final_result)
    # encoded = base64.b64encode(final_messages.encode("utf-8")).decode("utf-8")
    # return {"base64_fsts": encoded}

# --- For API/static testing: Read output from file ---
@app.get("/testfsts")
def get_fsts_base64_test():
    output_path = os.path.join("last_run_output", "final_specifications.md")
    file_encoded = ""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            final_messages = f.read()
        file_encoded = base64.b64encode(final_messages.encode("utf-8")).decode("utf-8")

    # --- HANA DB fetch ---
    hana_row = None
    schemas = []
    connection_info = {}
    rows = []
    rows_serializable = []
    try:
        from hdbcli import dbapi
        from cfenv import AppEnv

        env = AppEnv()
        hana_service = "hana"
        hana = env.get_service(label=hana_service)

        if hana is None:
            hana_row = f"Can't connect to HANA service '{hana_service}' – check service name?"
        else:
            address = hana.credentials["host"]
            port = int(hana.credentials["port"])
            user = hana.credentials["user"]

            # Store connection info
            connection_info = {
                "address": address,
                "port": port,
                "user": user
            }

            conn = dbapi.connect(
                address=address,
                port=port,
                user=user,
                password=hana.credentials["password"],
                encrypt="true",
                sslValidateCertificate="true",
                sslCryptoProvider="openssl",
                sslTrustStore=hana.credentials["certificate"]
            )
            schema_name = "6A8FE460FE1D45DD8782BE10B7EB66FC"
            cursor = conn.cursor()

            # Get current timestamp
            cursor.execute("SELECT CURRENT_UTCTIMESTAMP FROM DUMMY")
            row = cursor.fetchone()
            hana_row = str(row[0]) if row else "No result"

            # Get list of schemas
            cursor.execute("SELECT SCHEMA_NAME FROM SYS.SCHEMAS")
            schemas = [r[0] for r in cursor.fetchall()]

            cursor.execute(f'SET SCHEMA "{schema_name}"')

            # # Create table if not exists
            # cursor.execute(f"""
            # CREATE COLUMN TABLE "{schema_name}"."FSTSHeader" (
            #     "id" NVARCHAR(36),
            #     "content" BLOB,
            #     "taskID" INTEGER,
            #     PRIMARY KEY ("id")
            # )
            # """)
            
            # id = 5
            # content = "Example content"
            # taskID = 1
            # cursor.execute(f"""
            # INSERT INTO "MY_BOOKSHOP_BOOKS" ("ID", "TITLE", "STOCK") VALUES (?, ?, ?)
            # """, (id, content, taskID))

            cursor.execute('SELECT * FROM "MY_BOOKSHOP_BOOKS"')
            rows = cursor.fetchall()
            rows_serializable = [list(r) for r in rows]

            cursor.close()
            conn.close()
    except Exception as e:
        hana_row = f"Error fetching from HANA: {e}"

    return {
        "base64_fsts": file_encoded,
        "hana_sample_row": hana_row,
        "schemas": schemas,
        "connection_info": connection_info,
        "fsts_data": rows_serializable
    }

# To run: uvicorn api_server:app --reload

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 3000))  # Default to 3000 if not set
    uvicorn.run("api_server:app",host='0.0.0.0', port=port)