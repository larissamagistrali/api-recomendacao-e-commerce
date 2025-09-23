from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt  # PyJWT
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import traceback

security = HTTPBearer()

# Configuração do JWT
SECRET_KEY = "your-secret-key-here-change-in-production"  # Em produção, usar variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria um token JWT"""
    print(f"[AUTH_UTILS] create_access_token - Criando token para: {data}")
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"[AUTH_UTILS] create_access_token - Token criado com expiração: {expire}")
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifica e decodifica um token JWT"""
    print(f"[AUTH_UTILS] verify_token - Verificando token: {token[:20]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        print(f"[AUTH_UTILS] verify_token - Email extraído do token: '{email}'")
        print(f"[AUTH_UTILS] verify_token - Payload completo: {payload}")
        
        if email is None:
            print(f"[AUTH_UTILS] verify_token - Email não encontrado no token")
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        print(f"[AUTH_UTILS] verify_token - Token expirado")
        return None
    except jwt.JWTError as e:
        print(f"[AUTH_UTILS] verify_token - Erro JWT: {str(e)}")
        return None
    except Exception as e:
        print(f"[AUTH_UTILS] verify_token - Erro inesperado: {str(e)}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtém o usuário atual baseado no token JWT"""
    print(f"[AUTH_UTILS] get_current_user - INÍCIO")
    print(f"[AUTH_UTILS] get_current_user - Token recebido: {credentials.credentials[:20] if credentials.credentials else 'None'}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if not credentials or not credentials.credentials:
            print(f"[AUTH_UTILS] get_current_user - Nenhuma credencial fornecida")
            raise credentials_exception
        
        payload = verify_token(credentials.credentials)
        if payload is None:
            print(f"[AUTH_UTILS] get_current_user - Token inválido ou expirado")
            raise credentials_exception
        
        email = payload.get("sub")
        if email is None:
            print(f"[AUTH_UTILS] get_current_user - Email não encontrado no payload")
            raise credentials_exception
        
        print(f"[AUTH_UTILS] get_current_user - Buscando usuário por email: '{email}'")
        
        # Import local para evitar importação circular
        try:
            from app_setup import auth_service
            print(f"[AUTH_UTILS] get_current_user - Import do auth_service bem-sucedido")
        except ImportError as e:
            print(f"[AUTH_UTILS] get_current_user - ERRO ao importar auth_service: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno: serviço de autenticação indisponível"
            )
        
        user = await auth_service.get_user_by_email(email)
        if user is None:
            print(f"[AUTH_UTILS] get_current_user - Usuário não encontrado no banco para email: '{email}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"[AUTH_UTILS] get_current_user - Usuário encontrado: {user['id']}")
        return user
        
    except HTTPException:
        # Re-raise HTTPExceptions para manter o status code correto
        raise
    except Exception as e:
        print(f"[AUTH_UTILS] get_current_user - ERRO INESPERADO: {str(e)}")
        print(f"[AUTH_UTILS] get_current_user - Tipo do erro: {type(e)}")
        print(f"[AUTH_UTILS] get_current_user - Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno na autenticação: {str(e)}"
        )

# Função auxiliar para criar um usuário de teste
async def create_test_user():
    """Cria um usuário de teste para desenvolvimento"""
    try:
        from app_setup import auth_service
        from schemas.user import UserCreate
        
        test_user = UserCreate(
            email="test@example.com",
            password="test123",
            full_name="Usuário de Teste"
        )
        
        # Verificar se já existe
        existing_user = await auth_service.get_user_by_email(test_user.email)
        if existing_user:
            print(f"[AUTH_UTILS] create_test_user - Usuário de teste já existe: {existing_user['id']}")
            return existing_user
        
        # Criar novo usuário
        user = await auth_service.create_user(test_user)
        print(f"[AUTH_UTILS] create_test_user - Usuário de teste criado: {user['id']}")
        return user
        
    except Exception as e:
        print(f"[AUTH_UTILS] create_test_user - ERRO: {str(e)}")
        return None

# Função para obter token de teste
def get_test_token():
    """Gera um token de teste válido"""
    try:
        token = create_access_token(data={"sub": "test@example.com"})
        print(f"[AUTH_UTILS] get_test_token - Token de teste criado: {token[:20]}...")
        return token
    except Exception as e:
        print(f"[AUTH_UTILS] get_test_token - ERRO: {str(e)}")
        return None