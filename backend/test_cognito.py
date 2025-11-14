import requests
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CognitoAuth(BaseSettings):
    url: str = Field("https://eu-central-1meowq2nyq.auth.eu-central-1.amazoncognito.com/oauth2/token")
    grant_type: str = Field("client_credentials")
    client_id: str = Field("56a17up5ouquq9jfep9nbh2a0u")
    client_secret: str = Field("14ruc7faalscdcdvgjr8cfveusk88gjaanks7ud50em7na0v3mn5")
    scope: str = Field("default-m2m-resource-server-btncxn/read")

    model_config = SettingsConfigDict(
        env_prefix="COGNITO_",
        env_file=".env",
        case_sensitive=False,
    )

    @property
    def access_token(self) -> str:
        r = requests.post(
            self.url,
            data=f"grant_type={self.grant_type}&client_id={self.client_id}&client_secret={self.client_secret}&scope={self.scope}",
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        return r.json().get('access_token')

    @property
    def headers(self) -> dict:
        return {'Authorization': f'Bearer {self.access_token}'}

    def __repr__(self):
        return f'<Cognito: {self.access_token}>'