import autogen
import os
import base64
from fastapi import FastAPI
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# FastAPI app instance
app = FastAPI()

# Azure AI Config
from config import AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION, AZURE_DEPLOYMENT, AZURE_API_TYPE

config_list = [{
    "model": AZURE_DEPLOYMENT,
    "api_key": AZURE_API_KEY,
    "api_type": AZURE_API_TYPE,
    "api_version": AZURE_API_VERSION,
    "azure_endpoint": AZURE_API_BASE,
}]

assistant = autogen.AssistantAgent(name="AzureAI_Assistant", llm_config={"config_list": config_list})

user_proxy = autogen.UserProxyAgent(
    name="User", 
    human_input_mode="NEVER", 
    code_execution_config=False
)

# Gmail API Configuration
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def authenticate_gmail():
    """Authenticate with Gmail API and return the service instance."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class EmailRequest(BaseModel):
    num_emails: int = 1  # Default fetch 1 latest email

# Fetch latest email from Gmail API
def fetch_latest_email():
    """Fetches the latest email from the Gmail inbox."""
    try:
        service = authenticate_gmail()
        results = service.users().messages().list(userId="me", maxResults=1).execute()
        messages = results.get("messages", [])

        if not messages:
            return "No emails found."

        msg = service.users().messages().get(userId="me", id=messages[0]["id"]).execute()
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        subject = next((header["value"] for header in headers if header["name"] == "Subject"), "No Subject")
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    try:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    except Exception:
                        body = "Unable to decode email body."
                    break

        return f"Subject: {subject}\n\n{body}"
    
    except Exception as e:
        return f"Error fetching email: {str(e)}"
    
def fetch_emails(count=10):
    """Fetches the latest 'count' emails from the Gmail inbox."""
    try:
        service = authenticate_gmail()
        results = service.users().messages().list(userId="me", maxResults=count).execute()
        messages = results.get("messages", [])

        if not messages:
            return "No emails found."

        email_list = []

        for msg_meta in messages:
            msg = service.users().messages().get(userId="me", id=msg_meta["id"]).execute()
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            subject = next((header["value"] for header in headers if header["name"] == "Subject"), "No Subject")
            body = ""

            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        try:
                            body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        except Exception:
                            body = "Unable to decode email body."
                        break

            email_list.append(f"Subject: {subject}\n\n{body}")

        return "\n\n---\n\n".join(email_list)
    
    except Exception as e:
        return f"Error fetching emails: {str(e)}"

# FastAPI Routes
@app.post("/chatBot")
async def chat_with_ai(request: ChatRequest):
    """Handles chatbot requests via Azure OpenAI."""
    try:
        response = assistant.generate_reply(messages=[{"role": "user", "content": request.message}])
        return {"response": response}
    except Exception as e:
        print(e,'eee')
        return {"error": str(e)}

@app.post("/generate-email-response")
async def generate_email_response(request: EmailRequest):
    """Fetches the latest email and generates an AI-powered response."""
    try:
        email_content = fetch_latest_email()
        if "Error" in email_content:
            return {"error": email_content}
        response = assistant.generate_reply(messages=[{"role": "user", "content": f"Reply to this email:\n\n{email_content}"}]) 
        return {"email_response": response}
    except Exception as e:
        return {"error": str(e)}
    

@app.post("/get_email")
async def get_email_response():
    """Fetches the latest 10 emails and returns their subjects and bodies."""
    try:
        emails = fetch_emails(count=10)
        if "Error" in emails:
            return {"error": emails}
        return {"latest_emails": emails}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("aiagent:app", host="127.0.0.1", port=8000, reload=True)
