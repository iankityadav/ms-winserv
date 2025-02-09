from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    name: str
    email: str

    class Config:
        from_attributes = True

class ServerCreate(BaseModel):
    ip: str
    username: str
    password: str
    description: str

class Server(BaseModel):
    id: int
    ip: str
    username: str
    description: str

    class Config:
        from_attributes = True

class Service(BaseModel):
    id: int
    name: str
    status: str

    class Config:
        from_attributes = True
