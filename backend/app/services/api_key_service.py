from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from app.core.config import settings
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate

class ApiKeyService:
    def __init__(self):
        self.fernet = Fernet(settings.ENCRYPTION_KEY)

    def _encrypt(self, text: str) -> str:
        return self.fernet.encrypt(text.encode()).decode()

    def _decrypt(self, text: str) -> str:
        return self.fernet.decrypt(text.encode()).decode()

    def create_api_key(self, db: Session, key_in: ApiKeyCreate) -> ApiKey:
        # Check for duplicates
        existing_key = db.query(ApiKey).filter(ApiKey.name == key_in.name).first()
        if existing_key:
            raise ValueError(f"API Key with name '{key_in.name}' already exists.")

        encrypted_key = self._encrypt(key_in.key)
        db_key = ApiKey(
            name=key_in.name,
            provider=key_in.provider,
            key=encrypted_key,
            api_base=key_in.api_base,
            category=key_in.category
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        return db_key

    def get_api_keys(self, db: Session, skip: int = 0, limit: int = 100) -> list[ApiKey]:
        return db.query(ApiKey).offset(skip).limit(limit).all()

    def get_api_key(self, db: Session, key_id: int) -> ApiKey | None:
        return db.query(ApiKey).filter(ApiKey.id == key_id).first()
    
    def update_api_key(self, db: Session, key_id: int, key_in: ApiKeyUpdate) -> ApiKey | None:
        db_key = self.get_api_key(db, key_id)
        if not db_key:
            return None
        
        update_data = key_in.dict(exclude_unset=True)
        if "key" in update_data and update_data["key"]:
             update_data["key"] = self._encrypt(update_data["key"])
        
        for field, value in update_data.items():
            setattr(db_key, field, value)
            
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        return db_key

    def delete_api_key(self, db: Session, key_id: int) -> bool:
        db_key = self.get_api_key(db, key_id)
        if not db_key:
            return False
        db.delete(db_key)
        db.commit()
        return True

    def get_decrypted_key(self, db: Session, key_id: int) -> str | None:
        db_key = self.get_api_key(db, key_id)
        if db_key:
            return self._decrypt(db_key.key)
        return None

api_key_service = ApiKeyService()
