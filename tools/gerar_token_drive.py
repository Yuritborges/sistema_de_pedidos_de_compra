# tools/gerar_token_drive.py

from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive"]

# tools/ está no mesmo nível que app/
# então subimos 1 nível (.parent) e entramos em app/config/
CREDENTIALS_FILE = Path(__file__).parent.parent / "app" / "config" / "credentials_oauth.json"
TOKEN_FILE = Path(__file__).parent.parent / "app" / "config" / "token.json"

def gerar_token():
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), scopes=SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding='utf-8')
    print(f"\n✅ Token salvo em: {TOKEN_FILE.resolve()}")

if __name__ == "__main__":
    gerar_token()
