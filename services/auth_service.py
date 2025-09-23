from typing import Optional, Dict, Any
import hashlib
import uuid
from datetime import datetime
import sys
import os

# Garantir que podemos importar schemas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from schemas.user import UserCreate

class AuthService:
    """Serviço de autenticação usando dados em memória"""
    
    def __init__(self):
        print(f"[AUTH_SERVICE] __init__ - Inicializando AuthService")
        # Simulação de banco de dados em memória
        self.users = {}  # {email: user_data}
        print(f"[AUTH_SERVICE] __init__ - AuthService inicializado")
    
    def _hash_password(self, password: str) -> str:
        """Hash da senha usando SHA256"""
        print(f"[AUTH_SERVICE] _hash_password - Hashing password: {password[:3]}...")
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar se a senha está correta"""
        result = self._hash_password(plain_password) == hashed_password
        print(f"[AUTH_SERVICE] _verify_password - Resultado: {result}")
        return result
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Criar um novo usuário"""
        print(f"[AUTH_SERVICE] create_user - Criando usuário: {user_data.email}")
        
        # Verificar se o usuário já existe
        if user_data.email in self.users:
            print(f"[AUTH_SERVICE] create_user - Usuário já existe: {user_data.email}")
            raise ValueError("Email já está em uso")
        
        # Criar novo usuário
        user_id = str(uuid.uuid4())
        hashed_password = self._hash_password(user_data.password)
        
        user_record = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        self.users[user_data.email] = user_record
        
        print(f"[AUTH_SERVICE] create_user - Usuário criado: {user_id}")
        return user_record
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuário"""
        print(f"[AUTH_SERVICE] authenticate_user - Tentativa de login: {email}")
        
        user = await self.get_user_by_email(email)
        if not user:
            print(f"[AUTH_SERVICE] authenticate_user - Usuário não encontrado: {email}")
            return None
        
        if not self._verify_password(password, user["hashed_password"]):
            print(f"[AUTH_SERVICE] authenticate_user - Senha incorreta para: {email}")
            return None
        
        print(f"[AUTH_SERVICE] authenticate_user - AUTENTICAÇÃO BEM-SUCEDIDA para: {email}")
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Buscar usuário por email"""
        print(f"[AUTH_SERVICE] get_user_by_email - Buscando email: '{email}' (tipo: {type(email)})")
        print(f"[AUTH_SERVICE] get_user_by_email - Emails disponíveis: {list(self.users.keys())}")
        
        user = self.users.get(email)
        if user:
            print(f"[AUTH_SERVICE] get_user_by_email - Usuário encontrado: {user['id']}")
        else:
            print(f"[AUTH_SERVICE] get_user_by_email - Usuário não encontrado")
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Buscar usuário por ID"""
        print(f"[AUTH_SERVICE] get_user_by_id - Buscando ID: {user_id}")
        
        for user in self.users.values():
            if user["id"] == user_id:
                print(f"[AUTH_SERVICE] get_user_by_id - Usuário encontrado: {user['email']}")
                return user
        
        print(f"[AUTH_SERVICE] get_user_by_id - Usuário não encontrado")
        return None