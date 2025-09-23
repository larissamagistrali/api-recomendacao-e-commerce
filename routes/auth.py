from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
import json
from datetime import timedelta

from schemas.user import UserCreate, User, Token
from app_setup import auth_service  # Import da instância global
from utils.auth import create_access_token, verify_token, get_current_user, create_test_user, get_test_token

router = APIRouter()

@router.post("/create-test-user")
async def create_test_user_endpoint():
    """Criar usuário de teste para desenvolvimento"""
    print(f"[AUTH_ROUTE] create_test_user_endpoint - INÍCIO")
    
    try:
        user = await create_test_user()
        if user:
            token = get_test_token()
            return {
                "message": "Usuário de teste criado/encontrado com sucesso",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user.get("full_name")
                },
                "test_token": token
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Erro ao criar usuário de teste"
            )
    except Exception as e:
        print(f"[AUTH_ROUTE] create_test_user_endpoint - ERRO: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/test-token")
async def test_token_endpoint():
    """Obter um token de teste válido"""
    print(f"[AUTH_ROUTE] test_token_endpoint - INÍCIO")
    
    try:
        # Garantir que o usuário de teste existe
        user = await create_test_user()
        if not user:
            raise HTTPException(
                status_code=500,
                detail="Erro ao criar usuário de teste"
            )
        
        token = get_test_token()
        if not token:
            raise HTTPException(
                status_code=500,
                detail="Erro ao gerar token de teste"
            )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_email": "test@example.com",
            "instructions": [
                "Use este token no header Authorization: Bearer <token>",
                "Exemplo: Authorization: Bearer " + token[:20] + "...",
                "Este token é válido por 30 minutos"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH_ROUTE] test_token_endpoint - ERRO: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.post("/debug-token")
async def debug_login(request: Request):
    """Debug endpoint para capturar dados da requisição"""
    print(f"[DEBUG] debug_login - INÍCIO DO DEBUG")
    print(f"[DEBUG] debug_login - Request method: {request.method}")
    print(f"[DEBUG] debug_login - Request headers: {dict(request.headers)}")
    print(f"[DEBUG] debug_login - Content-Type: {request.headers.get('content-type')}")
    
    try:
        # Tentar ler como form data
        form_data = await request.form()
        print(f"[DEBUG] debug_login - Form data: {dict(form_data)}")
        
        # Tentar ler como JSON
        body = await request.body()
        print(f"[DEBUG] debug_login - Raw body: {body}")
        
        if body:
            try:
                json_data = json.loads(body)
                print(f"[DEBUG] debug_login - JSON data: {json_data}")
            except json.JSONDecodeError:
                print(f"[DEBUG] debug_login - Body não é JSON válido")
        
        return {"status": "debug complete", "form_data": dict(form_data), "body_length": len(body)}
        
    except Exception as e:
        print(f"[DEBUG] debug_login - Erro: {str(e)}")
        return {"error": str(e)}

@router.post("/register")
async def register(user: UserCreate):
    """Registro de novo usuário"""
    print(f"[AUTH_ROUTE] register - INÍCIO DO REGISTRO")
    print(f"[AUTH_ROUTE] register - Dados recebidos: {user}")
    
    try:
        db_user = await auth_service.create_user(user)
        print(f"[AUTH_ROUTE] register - USUÁRIO CRIADO: {db_user['id']} - {db_user['email']}")
        
        return {
            "message": "Usuário criado com sucesso",
            "user": {
                "id": db_user["id"],
                "email": db_user["email"],
                "full_name": db_user.get("full_name"),
                "created_at": db_user["created_at"]
            }
        }
    except ValueError as e:
        print(f"[AUTH_ROUTE] register - ERRO DE VALIDAÇÃO: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[AUTH_ROUTE] register - ERRO DURANTE REGISTRO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login do usuário"""
    print(f"[AUTH_ROUTE] login - INÍCIO DO LOGIN")
    print(f"[AUTH_ROUTE] login - Username: '{form_data.username}'")
    
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        
        if not user:
            print(f"[AUTH_ROUTE] login - FALHA NA AUTENTICAÇÃO para: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"[AUTH_ROUTE] login - AUTENTICAÇÃO SUCESSO para: {form_data.username}")
        access_token = create_access_token(data={"sub": user["email"]})
        print(f"[AUTH_ROUTE] login - Token criado: {access_token[:20]}...")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH_ROUTE] login - ERRO DURANTE LOGIN: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/me", response_model=User, summary="Obter usuário atual")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Retorna informações do usuário atualmente autenticado."""
    return current_user

@router.post("/refresh", response_model=Token, summary="Renovar token")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Renova o token de acesso do usuário autenticado."""
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800
    }

@router.get("/validate-token")
async def validate_token(current_user: User = Depends(get_current_user)):
    """Validar se o token atual é válido"""
    print(f"[AUTH_ROUTE] validate_token - Token válido para usuário: {current_user.get('id') if isinstance(current_user, dict) else current_user}")
    
    return {
        "valid": True,
        "user": {
            "id": current_user.get("id") if isinstance(current_user, dict) else current_user.id,
            "email": current_user.get("email") if isinstance(current_user, dict) else current_user.email,
            "full_name": current_user.get("full_name") if isinstance(current_user, dict) else current_user.full_name
        }
    }