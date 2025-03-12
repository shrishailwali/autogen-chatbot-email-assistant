import autogen
import os
import base64
from fastapi import FastAPI
from pydantic import BaseModel,Field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import openai
from openai import AzureOpenAI

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
    
def fetch_emails(count=5):
    """Fetches the latest 'count' draft emails from the Gmail inbox."""
    try:
        service = authenticate_gmail()  # Ensure authentication function is working
        results = service.users().drafts().list(userId="me", maxResults=count).execute()
        drafts = results.get("drafts", [])

        if not drafts:
            return "No draft emails found."

        draft_list = []

        for draft_meta in drafts:
            draft = service.users().drafts().get(userId="me", id=draft_meta["id"]).execute()
            msg = draft.get("message", {})
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            subject = next((header["value"] for header in headers if header["name"] == "Subject"), "No Subject")
            body = ""

            # Extract text/plain body
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        try:
                            body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        except Exception:
                            body = "Unable to decode email body."
                        break

            draft_list.append(f"Subject: {subject}\n\n{body}")

        return "\n\n---\n\n".join(draft_list)
    except Exception as e:
        return f"Error fetching draft emails: {str(e)}"


# FastAPI Routes
@app.post("/chatBot")
async def chat_with_ai(request: ChatRequest):
    """Handles chatbot requests via Azure OpenAI."""
    try:
        response = assistant.generate_reply(messages=[{"role": "user", "content": request.message}])
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}

def generate_response(prompt, user_prompt):
    try:
        # Configure Azure OpenAI client
        client = AzureOpenAI(
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_API_BASE
        )
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content  # Fix applied here
    except openai.APIError as e:
        raise ValueError("OpenAI API returned an API Error: " + str(e))
    except Exception as e:
        raise ValueError("Error occurred during response generation: " + str(e))
    
class EmailRequest(BaseModel):
    email_content: str  # Ensure this field matches the JSON structure of the request

@app.post("/email_chatBot")
async def chat_with_ai(request: EmailRequest):
    """Generates an AI-assisted email reply."""
    try:
        print(EmailRequest,'EmailRequest')
        prompt = f"""
        You are an AI email assistant. Read the following email and generate a professional and context-aware reply:\n\n
        Email: {request.email_content}\n\n
        Reply professionally:
        """
        user_prompt = "You are an AI email assistant. Read the following email and generate a professional and context-aware reply."
        ai_reply = generate_response(prompt, user_prompt)
        print(ai_reply,'aiiii')
        return {"response": ai_reply}
    except Exception as e:
        return {"error": "Failed to generate a response. Please try again."}


@app.post("/generate-email-response")
async def generate_email_response(request: EmailRequest):
    """Generates an AI-powered response for the given email."""
    try:
        email_content = request.email_content  # Extract the email content

        if "Error" in email_content:
            return {"error": "Invalid email content"}

        # Generate AI response
        response = assistant.generate_reply(messages=[{"role": "user", "content": f"Reply to this email:\n\n{email_content}"}]) 
        print(response,'kkkk')
        return {"email_response": response}
    except Exception as e:
        print(e,'llllllll')
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
    
from db_helper import execute_query

# Define an AutoGen agent with database query capability
class DatabaseAgent(autogen.AssistantAgent):
    def handle_query(self, query):
        return execute_query(query)

# Initialize AI agent
db_assistant = DatabaseAgent(name="AzureAI_Assistant")

def get_database_schema():
    from db_helper import connect_to_db
    """Fetches the schema of all tables in the database."""
    conn = connect_to_db()
    if conn is None:
        return "Database connection failed."

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            schema_data = cursor.fetchall()

            schema_dict = {}
            for table_name, column_name, data_type in schema_data:
                if table_name not in schema_dict:
                    schema_dict[table_name] = []
                schema_dict[table_name].append(f"{column_name} ({data_type})")

            schema_description = "\n".join(
                [f"Table: {table}\nColumns: {', '.join(columns)}" for table, columns in schema_dict.items()]
            )
            return schema_description
    except Exception as e:
        return f"Error fetching schema: {e}"
    finally:
        conn.close()

def query_database_with_ai(natural_language_query):
    """Converts natural language query into SQL and executes it."""
    
    # Get database schema dynamically
    schema_info = get_database_schema()
    prompt = f"""
    You are an AI SQL assistant. Convert the following natural language query into a valid PostgreSQL SQL query.
    Here is the database schema:
    {schema_info}
    Example:
    - Natural Language: "How many work orders are there in the work_order table?"
    - SQL: SELECT COUNT(*) FROM work_order;

    Now convert this request: "{natural_language_query}"
    """
    user_prompt = "You are an AI SQL assistant. Convert the following natural language query into a valid PostgreSQL SQL query"
    ai_response = generate_response(prompt, user_prompt)
    if not ai_response.strip():
        return "Error: AI generated an empty query."
    return execute_query(ai_response)


class QueryRequest(BaseModel):
    query: str

@app.post("/query-database-nl")
async def query_database_nl(request: QueryRequest):
    """Handles natural language queries and converts them into SQL queries."""
    try:
        result = query_database_with_ai(request.query)
        print(result)
        return {"result": result[0][0]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent:app", host="127.0.0.1", port=8000, reload=True)
