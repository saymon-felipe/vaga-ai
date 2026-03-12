import logging
import sys
import io

def setup_logger():
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')
        
    logger = logging.getLogger("VagaAI_Worker")
    logger.setLevel(logging.INFO)
    logger.propagate = False # <--- NOVA LINHA QUE RESOLVE OS LOGS DUPLICADOS
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%d/%m %H:%M:%S')
        
        file_handler = logging.FileHandler('worker_execucao.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logging.getLogger().addHandler(file_handler)
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().setLevel(logging.INFO)
        
    return logger

logger = setup_logger()