import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from database import Base

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    plataforma = Column(String(255))
    empresa_nome = Column(String(255))
    vaga_titulo = Column(String(255))
    vaga_url = Column(Text)
    status = Column(String(50), default='Analisando')
    match_score = Column(Integer)
    faixa_salarial = Column(String(100), default="A Combinar")
    job_description_raw = Column(Text)
    respostas_ia_raw = Column(JSON)
    argumentos_match_raw = Column(JSON)
    
    createdAt = Column(DateTime, default=datetime.datetime.now, nullable=False)
    updatedAt = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)

class CompanyInsight(Base):
    __tablename__ = "company_insights"

    id = Column(Integer, primary_key=True, index=True)
    dominio = Column(String(255), unique=True)
    nome_empresa = Column(String(255))
    dados_brutos_pesquisa = Column(JSON)
    tech_stack_identificada = Column(JSON)
    
    createdAt = Column(DateTime, default=datetime.datetime.now, nullable=False)
    updatedAt = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)