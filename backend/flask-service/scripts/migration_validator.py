#!/usr/bin/env python
import os
import sys
import re
from pathlib import Path
import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationValidator:
    def __init__(self, migrations_dir):
        self.migrations_dir = Path(migrations_dir)
        self.errors = []
        self.warnings = []

    def validate_migration_files(self):
        """Validate all migration files in the directory"""
        migration_files = sorted(self.migrations_dir.glob('*.py'))
        
        for migration_file in migration_files:
            logger.info(f"Validating migration file: {migration_file.name}")
            self.validate_single_migration(migration_file)

        return len(self.errors) == 0

    def validate_single_migration(self, file_path):
        """Validate a single migration file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Parse the Python file
            tree = ast.parse(content)
            
            # Check for basic requirements
            self._check_revision(tree, file_path)
            self._check_upgrade_downgrade(tree, file_path)
            self._check_dangerous_operations(content, file_path)
            self._check_transaction_safety(content, file_path)
            
        except Exception as e:
            self.errors.append(f"Error parsing {file_path.name}: {str(e)}")

    def _check_revision(self, tree, file_path):
        """Check if revision and dependencies are properly defined"""
        revision_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'revision':
                        revision_found = True
                        if not isinstance(node.value, ast.Str):
                            self.errors.append(f"{file_path.name}: revision should be a string")
        
        if not revision_found:
            self.errors.append(f"{file_path.name}: missing revision identifier")

    def _check_upgrade_downgrade(self, tree, file_path):
        """Check if upgrade and downgrade functions are defined"""
        functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.add(node.name)
        
        if 'upgrade' not in functions:
            self.errors.append(f"{file_path.name}: missing upgrade function")
        if 'downgrade' not in functions:
            self.warnings.append(f"{file_path.name}: missing downgrade function")

    def _check_dangerous_operations(self, content, file_path):
        """Check for potentially dangerous operations"""
        dangerous_patterns = [
            (r'drop\s+table', 'table drop'),
            (r'truncate\s+table', 'table truncate'),
            (r'delete\s+from', 'delete without where clause'),
            (r'alter\s+table\s+\w+\s+drop\s+column', 'column drop')
        ]
        
        for pattern, operation in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.warnings.append(
                    f"{file_path.name}: contains potentially dangerous operation: {operation}"
                )

    def _check_transaction_safety(self, content, file_path):
        """Check for transaction safety"""
        if 'op.execute' in content and 'op.get_bind().execute' not in content:
            self.warnings.append(
                f"{file_path.name}: uses raw execute - ensure statements are transaction-safe"
            )

    def print_report(self):
        """Print validation report"""
        if self.errors:
            logger.error("Validation Errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning("Validation Warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            logger.info("All migrations validated successfully!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python migration_validator.py <migrations_directory>")
        sys.exit(1)

    migrations_dir = sys.argv[1]
    if not os.path.exists(migrations_dir):
        print(f"Error: Directory {migrations_dir} does not exist")
        sys.exit(1)

    validator = MigrationValidator(migrations_dir)
    is_valid = validator.validate_migration_files()
    validator.print_report()

    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main() 