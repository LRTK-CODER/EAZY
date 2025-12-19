from sqlalchemy.orm import Session
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigUpdate

class LLMService:
    def get_llm_config(self, db: Session, project_id: int) -> LLMConfig | None:
        return db.query(LLMConfig).filter(LLMConfig.project_id == project_id).first()

    def upsert_llm_config(self, db: Session, project_id: int, config_in: LLMConfigCreate) -> LLMConfig:
        db_config = self.get_llm_config(db, project_id)
        
        if db_config:
            # Update existing
            db_config.model_name = config_in.model_name
            db_config.api_key_id = config_in.api_key_id
        else:
            # Create new
            db_config = LLMConfig(
                project_id=project_id,
                model_name=config_in.model_name,
                api_key_id=config_in.api_key_id
            )
            db.add(db_config)
            
        db.commit()
        db.refresh(db_config)
        return db_config

llm_service = LLMService()
