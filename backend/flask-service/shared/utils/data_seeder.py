import logging
from flask import Flask
from sqlalchemy.exc import IntegrityError
from typing import List, Type, Any, Dict

logger = logging.getLogger(__name__)

class DataSeeder:
    def __init__(self, app: Flask, db):
        self.app = app
        self.db = db
        self.seeders = []

    def register_seeder(self, model: Type[Any], data: List[Dict[str, Any]], unique_fields: List[str]):
        """Register a seeder for a model"""
        self.seeders.append({
            'model': model,
            'data': data,
            'unique_fields': unique_fields
        })

    def _exists(self, model: Type[Any], data: Dict[str, Any], unique_fields: List[str]) -> bool:
        """Check if a record already exists based on unique fields"""
        filters = {field: data[field] for field in unique_fields if field in data}
        return model.query.filter_by(**filters).first() is not None

    def run_seeder(self, seeder: Dict) -> bool:
        """Run a single seeder"""
        model = seeder['model']
        data_list = seeder['data']
        unique_fields = seeder['unique_fields']
        
        try:
            for data in data_list:
                if not self._exists(model, data, unique_fields):
                    instance = model(**data)
                    self.db.session.add(instance)
            
            self.db.session.commit()
            logger.info(f"Successfully seeded {model.__name__}")
            return True
        except IntegrityError as e:
            self.db.session.rollback()
            logger.error(f"Error seeding {model.__name__}: {str(e)}")
            return False
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Unexpected error seeding {model.__name__}: {str(e)}")
            return False

    def run_all_seeders(self) -> bool:
        """Run all registered seeders"""
        success = True
        with self.app.app_context():
            for seeder in self.seeders:
                if not self.run_seeder(seeder):
                    success = False
        return success

    def run_seeder_for_model(self, model_name: str) -> bool:
        """Run seeder for a specific model"""
        with self.app.app_context():
            for seeder in self.seeders:
                if seeder['model'].__name__ == model_name:
                    return self.run_seeder(seeder)
        logger.warning(f"No seeder found for model: {model_name}")
        return False 