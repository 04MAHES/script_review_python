import streamlit as st
import requests
import re
import threading
import time
import socket
import os
from typing import List
 
# -----------------------
# Configuration
# -----------------------
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
BACKEND_BASE = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
BACKEND_VALIDATE_URL = f"{BACKEND_BASE}/validate"
 
# -----------------------
# Utils
# -----------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
 
def split_and_clean_emails(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"[,\n;]+", text)
    return [p.strip() for p in parts if p.strip()]
 
def validate_emails(emails: List[str]) -> (bool, List[str]):
    invalid = [e for e in emails if not EMAIL_RE.match(e)]
    return (len(invalid) == 0, invalid)
 
def is_port_open(host: str, port: int) -> bool:
    """Check whether the given host:port is accepting TCP connections."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False
 
def start_uvicorn_in_thread(module_path: str = "main:app", host: str = BACKEND_HOST, port: int = BACKEND_PORT):
    """
    Start uvicorn server in a daemon thread.
    Uses uvicorn.run with a module path (so it will import your main:app).
    """
    import uvicorn
 
    def _run():
        # Use reload=False when starting programmatically inside Streamlit
        uvicorn.run(module_path, host=host, port=port, log_level="info", reload=False)
 
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
 
# -----------------------
# Streamlit: Start backend if required
# -----------------------
st.set_page_config(page_title="RPA Release Validator", page_icon="🧾", layout="centered")
st.title("RPA Release Validator (Streamlit + Auto-backend)")
 
if "server_started" not in st.session_state:
    st.session_state.server_started = False
    st.session_state.server_thread = None
 
col1, col2 = st.columns([3, 1])
with col1:
    st.write("This app will automatically start the FastAPI backend (`main:app`) on localhost:8000 if it's not already running.")
with col2:
    if is_port_open(BACKEND_HOST, BACKEND_PORT):
        st.success(f"Backend detected on port {BACKEND_PORT}")
        st.session_state.server_started = True
    else:
        st.warning(f"Backend not detected on {BACKEND_PORT} — will start automatically when you click 'Start Backend' or submit the form.")
 
# Manual start button (optional)
if st.button("Start Backend Now (optional)"):
    if st.session_state.server_started:
        st.info("Backend already running.")
    else:
        st.info("Starting backend... (this may take 1–3 seconds)")
        st.session_state.server_thread = start_uvicorn_in_thread("main:app", BACKEND_HOST, BACKEND_PORT)
        # wait a short while for server to come up
        for _ in range(10):
            if is_port_open(BACKEND_HOST, BACKEND_PORT):
                st.success("Backend started.")
                st.session_state.server_started = True
                break
            time.sleep(0.5)
        else:
            st.error("Failed to detect backend after starting. Check Streamlit console for errors.")
 
st.markdown("---")
 
# -----------------------
# Upload form
# -----------------------
with st.form("upload_form"):
    st.info("Upload one release/script file (e.g. .bprelease, .bpprocess, .py, etc.)")
    uploaded_file = st.file_uploader("Choose release file", type=None, accept_multiple_files=False)
 
    st.write("Enter recipient email address(es). You can paste multiple emails separated by comma, semicolon, newline or space.")
    emails_text = st.text_area("Recipient email(s)", height=80, placeholder="alice@example.com, bob@example.com")
    cc_text = st.text_input("CC (optional) — comma/semicolon separated", "")
    bcc_text = st.text_input("BCC (optional) — comma/semicolon separated", "")
 
    submit = st.form_submit_button("Validate & Send (starts backend if needed)")
 
if submit:
    if not uploaded_file:
        st.error("Please upload a release file before submitting.")
    else:
        # ensure backend is running (start if not)
        if not st.session_state.server_started and not is_port_open(BACKEND_HOST, BACKEND_PORT):
            st.info("Backend not running — starting it now...")
            st.session_state.server_thread = start_uvicorn_in_thread("main:app", BACKEND_HOST, BACKEND_PORT)
            # wait briefly for server to be available
            for _ in range(15):
                if is_port_open(BACKEND_HOST, BACKEND_PORT):
                    st.session_state.server_started = True
                    break
                time.sleep(0.5)
 
        if not st.session_state.server_started and not is_port_open(BACKEND_HOST, BACKEND_PORT):
            st.error("Failed to start backend automatically. Check Streamlit console for errors.")
        else:
            to_list = split_and_clean_emails(emails_text)
            cc_list = split_and_clean_emails(cc_text)
            bcc_list = split_and_clean_emails(bcc_text)
 
            all_ok, invalid = validate_emails(to_list + cc_list + bcc_list)
            if not all_ok:
                st.error(f"Invalid email address(es): {', '.join(invalid)}")
            else:
                st.write("**File:**", uploaded_file.name)
                st.write("**To:**", ", ".join(to_list) or "—")
                st.write("**CC:**", ", ".join(cc_list) or "—")
                st.write("**BCC:**", ", ".join(bcc_list) or "—")
 
                # prepare multipart form
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")
                }
                data = {
                    "to_emails": ",".join(to_list),
                    "cc_emails": ",".join(cc_list),
                    "bcc_emails": ",".join(bcc_list),
                }
 
                try:
                    with st.spinner("Uploading file and calling backend..."):
                        resp = requests.post(BACKEND_VALIDATE_URL, files=files, data=data, timeout=120)
                    if resp.status_code == 200:
                        st.success("Validation completed successfully.")
                        try:
                            st.subheader("Result (preview)")
                            st.json(resp.json())
                        except Exception:
                            st.text(resp.text)
                    else:
                        # show backend error details
                        st.error(f"Backend returned status {resp.status_code}")
                        try:
                            st.json(resp.json())
                        except Exception:
                            st.text(resp.text)
                except requests.exceptions.ConnectionError:
                    st.error(f"Could not connect to backend at {BACKEND_VALIDATE_URL}. Check logs.")
                except requests.exceptions.ReadTimeout:
                    st.error("The backend request timed out. Try again or increase timeout.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")