from contextlib import asynccontextmanager
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, database, auth, services
from fastapi.security import OAuth2PasswordRequestForm
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    database.init_db()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/signup", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = auth.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/servers/", response_model=schemas.Server)
def create_server(server: schemas.ServerCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    encrypted_password = services.encrypt_password(server.password)
    db_server = models.Server(ip=server.ip, username=server.username, encrypted_password=encrypted_password, description=server.description, owner_id=current_user.id)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server

@app.get("/servers/", response_model=list[schemas.Server])
def create_server(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Server).all()

@app.get("/servers/{server_id}/services", response_model=list[schemas.Service])
def list_services(server_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    password = services.decrypt_password(db_server.encrypted_password)
    remote_manager = services.RemoteServiceManager(db_server.ip, db_server.username, password)
    
    try:
        services_list = remote_manager.list_services()
        return services.save_services_to_db(db, server_id, services_list)
    except Exception as e:
        logger.error(f"Failed to list services for server {db_server.ip}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list services")

@app.post("/servers/{server_id}/services/{service_name}/start")
def start_service(server_id: int, service_name: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_server = db.query(models.Server).filter(models.Server.id == server_id, models.Server.owner_id == current_user.id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    password = services.decrypt_password(db_server.encrypted_password)
    remote_manager = services.RemoteServiceManager(db_server.ip, db_server.username, password)
    
    try:
        message = remote_manager.start_service(service_name)
        logger.info(message)
        return {"message": message}
    except Exception as e:
        logger.error(f"Failed to start service {service_name} on server {db_server.ip}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start service: {e}")

@app.post("/servers/{server_id}/services/{service_name}/stop")
def stop_service(server_id: int, service_name: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_server = db.query(models.Server).filter(models.Server.id == server_id, models.Server.owner_id == current_user.id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    password = services.decrypt_password(db_server.encrypted_password)
    remote_manager = services.RemoteServiceManager(db_server.ip, db_server.username, password)
    
    try:
        message = remote_manager.stop_service(service_name)
        logger.info(message)
        return {"message": message}
    except Exception as e:
        logger.error(f"Failed to stop service {service_name} on server {db_server.ip}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop service: {e}")

@app.get("/users/me", response_model=schemas.User)
def get_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
