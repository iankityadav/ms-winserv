from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class ServerCreate(BaseModel):
    ip: str
    username: str
    password: str

class Server(BaseModel):
    id: int
    ip: str
    username: str

    class Config:
        from_attributes = True

class Service(BaseModel):
    id: int
    name: str
    status: str

    class Config:
        from_attributes = True
