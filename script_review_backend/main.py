import io
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

import logging
logger = logging.getLogger(__name__)

from gemini_client import PROMPT_TEMPLATE, call_gemini_api
from file_utils import detect_tool_type, extract_json_from_text
from excel_utils import write_results_to_excel
from email_utils import send_email   # FIXED IMPORT

app = FastAPI(title="RPA Script Validator (Modular)")

@app.post("/validate")
async def validate_workflow(
    file: UploadFile = File(...),
    to_emails: Optional[str] = Form(None),    # comma-separated
    cc_emails: Optional[str] = Form(None),    # comma-separated
    bcc_emails: Optional[str] = Form(None),   # comma-separated
):
    print(file)
    print(to_emails)

    # ===== READ FILE =====
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except:
        content = raw.decode("latin1")

    # ===== DETECT TOOL TYPE =====
    tool_type = detect_tool_type(file.filename, content)

    # ===== PREPARE PROMPT =====
    prompt = PROMPT_TEMPLATE % (tool_type, content)

    # ===== CALL GEMINI =====
    try:
        raw_response = call_gemini_api(prompt)
        json_obj = extract_json_from_text(raw_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ===== CREATE EXCEL IN MEMORY =====
    output = io.BytesIO()
    write_results_to_excel(json_obj, out_path=output)
    excel_bytes = output.getvalue()

    # ===== SEND EMAIL (if provided) =====
    if to_emails:
        print("working to send mail")
        to_list = [e.strip() for e in to_emails.split(",") if e.strip()]
        cc_list = [e.strip() for e in cc_emails.split(",")] if cc_emails else []
        bcc_list = [e.strip() for e in bcc_emails.split(",")] if bcc_emails else []

        try:
            print('calling send mail')
            send_email(
                to_list=to_list,
                cc_list=cc_list,
                bcc_list=bcc_list,
                subject=f"Validation results for {file.filename}",
                body="Attached are the script validation results.",
                attachment_bytes=excel_bytes,
                filename=f"validation_{file.filename}.xlsx",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

    return {"result": json_obj}
