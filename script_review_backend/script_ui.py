import streamlit as st
import requests
import io
import re
from typing import List
 
# ------- Configuration -------
BACKEND_VALIDATE_URL = "http://127.0.0.1:8000/validate"  # change if your backend is elsewhere
 
# ------- Utilities -------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
 
def split_and_clean_emails(text: str) -> List[str]:
    """Split a text block into individual email addresses and clean them."""
    if not text:
        return []
    # accept comma, semicolon, whitespace, newline as separators
    parts = re.split(r"[,\n;]+", text)
    return [p.strip() for p in parts if p.strip()]
 
def validate_emails(emails: List[str]) -> (bool, List[str]):
    """Return (is_all_valid, invalid_list)."""
    invalid = [e for e in emails if not EMAIL_RE.match(e)]
    return (len(invalid) == 0, invalid)
 
# ------- Streamlit App -------
st.set_page_config(page_title="RPA Release Validator", page_icon="🧾", layout="centered")
 
st.title("RPA Release Validator")
st.write("Upload release/script files and optionally enter recipient email(s) to receive validation results.")
 
with st.form("upload_form"):
    st.info("Upload one release/script file (e.g. .bprelease, .bpprocess, .py, etc.)")
    uploaded_file = st.file_uploader("Choose release file", type=None, accept_multiple_files=False)
    st.write("Enter recipient email address(es). You can paste multiple emails separated by comma, semicolon, newline or space.")
    emails_text = st.text_area("Recipient email(s)", height=80, placeholder="alice@example.com, bob@example.com")
    # optional CC/BCC fields (if you want)
    cc_text = st.text_input("CC (optional) — comma/semicolon separated", "")
    bcc_text = st.text_input("BCC (optional) — comma/semicolon separated", "")
    submit = st.form_submit_button("Validate & Send")
 
if submit:
    if not uploaded_file:
        st.error("Please upload a release file before submitting.")
    else:
        to_list = split_and_clean_emails(emails_text)
        cc_list = split_and_clean_emails(cc_text)
        bcc_list = split_and_clean_emails(bcc_text)
 
        # Validate emails client-side
        all_ok, invalid = validate_emails(to_list + cc_list + bcc_list)
        if not all_ok:
            st.error(f"Invalid email address(es): {', '.join(invalid)}")
        else:
            # Display summary
            st.write("**File:**", uploaded_file.name)
            st.write("**To:**", ", ".join(to_list) or "—")
            st.write("**CC:**", ", ".join(cc_list) or "—")
            st.write("**BCC:**", ", ".join(bcc_list) or "—")
 
            # Ask user whether to call backend or just save locally
            do_call = st.checkbox("Send file to backend `/validate` endpoint and email results", value=True)
 
            if do_call:
                try:
                    with st.spinner("Uploading file and invoking backend..."):
                        # Prepare multipart form
                        files = {
                            "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")
                        }
                        data = {
                            "to_emails": ",".join(to_list),
                            "cc_emails": ",".join(cc_list),
                            "bcc_emails": ",".join(bcc_list),
                        }
 
                        resp = requests.post(BACKEND_VALIDATE_URL, files=files, data=data, timeout=120)
 
                        if resp.status_code == 200:
                            st.success("Validation completed successfully.")
                            try:
                                json_response = resp.json()
                                st.subheader("Result (preview)")
                                st.json(json_response)
                            except Exception:
                                st.write("Response received but could not parse JSON; raw text below.")
                                st.text(resp.text)
                        else:
                            st.error(f"Backend returned an error: {resp.status_code}")
                            # show helpful details
                            try:
                                st.json(resp.json())
                            except Exception:
                                st.text(resp.text)
                except requests.exceptions.ConnectionError:
                    st.error(f"Could not connect to backend at {BACKEND_VALIDATE_URL}. Is the FastAPI server running?")
                except requests.exceptions.ReadTimeout:
                    st.error("The backend request timed out. Try increasing the timeout or check backend health.")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")
            else:
                # Just save uploaded file locally (optional)
                save_local = st.button("Save file locally")
                if save_local:
                    try:
                        with open(uploaded_file.name, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        st.success(f"Saved to {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"Failed to save file: {e}")
 
