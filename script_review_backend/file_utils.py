import json

def detect_tool_type(filename: str, content:str) -> str:
    print("Inside file utils")
    name = (filename or "").lower()
    content = (content or "").lower()

    if name.endswith(".xaml"): 
        return "UiPath"
    elif name.endswith(".bprelease") or name.endwith(".bpprocess") or name.endswith(".bpobject"):
        return "Blue Prism"

    return "Incorrect file"

def extract_json_from_text(text: str) -> dict:
    start = text.find("{")
    if start == -1:
        raise ValueError("JSON not found")


    stack = 0
    for i in range(start, len(text)):
        if text[i] == "{": stack += 1
        elif text[i] == "}": stack -= 1
        if stack == 0:
            return json.loads(text[start:i+1])


    raise ValueError("Unbalanced JSON")