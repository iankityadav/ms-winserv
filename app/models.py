from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, unique=True, index=True)
    username = Column(String)
    encrypted_password = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship("User", back_populates="servers")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
    server_id = Column(Integer, ForeignKey('servers.id'))

    server = relationship("Server", back_populates="services")

User.servers = relationship("Server", back_populates="owner")
Server.services = relationship("Service", back_populates="server")
