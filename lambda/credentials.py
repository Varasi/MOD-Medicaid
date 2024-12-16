from mod_medicaid.secrets import SecretManager

# Via Credentials
class crendential:
    def __init__(self) -> None:
        self.via_client_id = SecretManager().get_secret_value("via_client_id")
        self.via_client_secret = SecretManager().get_secret_value("via_client_secret")
        self.via_api_key = SecretManager().get_secret_value("via_api_key")
        self.via_auth_url = SecretManager().get_secret_value("via_auth_url")
        self.via_api_url = SecretManager().get_secret_value("via_api_url")

# # Lyft Credentials
lyft_client_id = ''
lyft_client_secret = ''
lyft_program_id = ''
lyft_auth_url = 'https://api.lyft.com/oauth/token'
lyft_api_url = 'https://api.lyft.com/v1/tapi/atms/webhooks'