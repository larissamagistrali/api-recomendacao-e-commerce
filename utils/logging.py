import logging
import sys
from datetime import datetime
import structlog

def setup_logging(level: str = "INFO"):
    """Configura sistema de logging estruturado"""
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging padrão
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )
    
    # Configurar loggers específicos
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

def get_logger(name: str):
    """Retorna logger estruturado"""
    return structlog.get_logger(name)

class RequestLogger:
    """Middleware para logging de requests"""
    
    def __init__(self):
        self.logger = get_logger("api.requests")
    
    async def log_request(self, request, response, processing_time: float):
        """Log de request/response"""
        self.logger.info(
            "API request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            processing_time_ms=round(processing_time * 1000, 2),
            user_agent=request.headers.get("user-agent"),
            timestamp=datetime.utcnow().isoformat()
        )