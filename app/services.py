import winrm
import json
from cryptography.fernet import Fernet
from .models import Server, Service
from .database import SessionLocal

# Encryption key for passwords
key = Fernet.generate_key()
cipher_suite = Fernet(key)

class RemoteServiceManager:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session = winrm.Session(f'http://{host}:5985/wsman', auth=(username, password), transport='basic')

    def list_services(self):
        ps_script = 'Get-Service | Select-Object Name, Status | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        if result.status_code == 0:
            return json.loads(result.std_out)
        else:
            raise Exception(f"Failed to list services: {result.std_err}")

    def start_service(self, service_name):
        ps_script = f'Start-Service -Name {service_name}'
        result = self.session.run_ps(ps_script)
        if result.status_code == 0:
            return f"Service '{service_name}' started successfully."
        else:
            raise Exception(f"Failed to start service '{service_name}': {result.std_err}")

    def stop_service(self, service_name):
        ps_script = f'Stop-Service -Name {service_name}'
        result = self.session.run_ps(ps_script)
        if result.status_code == 0:
            return f"Service '{service_name}' stopped successfully."
        else:
            raise Exception(f"Failed to stop service '{service_name}': {result.std_err}")

def encrypt_password(password):
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

def save_services_to_db(db, server_id, services):
    for service in services:
        db_service = Service(
            name=service['Name'],
            status=service['Status'],
            server_id=server_id
        )
        db.add(db_service)
    db.commit()