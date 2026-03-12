from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
import datetime
from database import Base

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    plataforma = Column(String(255), nullable=False)
    empresa_nome = Column(String(255), nullable=False)
    vaga_titulo = Column(String(255), nullable=False)
    vaga_url = Column(Text, nullable=False)
    status = Column(String(50), default='Analisando')
    match_score = Column(Integer)
    faixa_salarial = Column(String(100), default="A Combinar")
    job_description_raw = Column(Text)
    respostas_ia_raw = Column(JSON)
    argumentos_match_raw = Column(JSON)
    requer_confirmacao_email = Column(Boolean, default=False)
    
    createdAt = Column(DateTime, default=datetime.datetime.now, nullable=False)
    updatedAt = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)