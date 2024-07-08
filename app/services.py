import winrm
import json
from cryptography.fernet import Fernet
from .models import Server, Service
from .database import SessionLocal
from dotenv import dotenv_values

# Encryption key for passwords
env = dotenv_values(".env")
key = env["ENCRYPTION_KEY"]
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
    existing_services = db.query(Service).filter(Service.server_id == server_id).all()
    existing_services_dict = {service.name: service for service in existing_services}
    services_list=[]
    for service in services:
        service_name = service['Name']
        service_status = service['Status']
        if service_name in existing_services_dict:
            db_service = existing_services_dict[service_name]
            db_service.status = service_status
        else:
            db_service = Service(
                name=service_name,
                status=service_status,
                server_id=server_id
            )
            db.add(db_service)
        services_list.append(db_service)
    db.commit()
    return services_list
