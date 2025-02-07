#!/usr/bin/env python
import os
import sys
import re
from datetime import datetime
import graphviz
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationChainVisualizer:
    def __init__(self, migrations_dir):
        self.migrations_dir = Path(migrations_dir)
        self.migrations = {}
        self.graph = graphviz.Digraph(comment='Migration Chain')
        self.graph.attr(rankdir='LR')

    def parse_migration_files(self):
        """Parse all migration files to extract revision information"""
        for migration_file in sorted(self.migrations_dir.glob('*.py')):
            if migration_file.name.startswith('__'):
                continue

            with open(migration_file, 'r') as f:
                content = f.read()

            # Extract revision and dependencies
            revision_match = re.search(r"revision = '([^']*)'", content)
            down_revision_match = re.search(r"down_revision = '([^']*)'", content)
            
            if revision_match:
                revision = revision_match.group(1)
                down_revision = down_revision_match.group(1) if down_revision_match else None
                
                # Extract timestamp and description from filename
                timestamp_match = re.match(r'(\d{14})_(.+)\.py', migration_file.name)
                if timestamp_match:
                    timestamp = datetime.strptime(timestamp_match.group(1), '%Y%m%d%H%M%S')
                    description = timestamp_match.group(2).replace('_', ' ').title()
                else:
                    timestamp = None
                    description = migration_file.stem

                self.migrations[revision] = {
                    'down_revision': down_revision,
                    'file': migration_file.name,
                    'timestamp': timestamp,
                    'description': description
                }

    def create_graph(self, output_file='migration_chain'):
        """Create a visual representation of the migration chain"""
        self.parse_migration_files()

        # Add nodes
        for revision, info in self.migrations.items():
            label = f"{info['description']}\n{info['timestamp'].strftime('%Y-%m-%d %H:%M') if info['timestamp'] else ''}"
            self.graph.node(revision, label=label)

        # Add edges
        for revision, info in self.migrations.items():
            if info['down_revision']:
                self.graph.edge(info['down_revision'], revision)

        # Save the graph
        try:
            self.graph.render(output_file, view=True, format='png')
            logger.info(f"Migration chain visualization saved to {output_file}.png")
        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")

    def print_chain(self):
        """Print text representation of the migration chain"""
        self.parse_migration_files()

        # Find head revision(s)
        heads = set(self.migrations.keys()) - {
            m['down_revision'] for m in self.migrations.values() if m['down_revision']
        }

        def print_branch(revision, level=0):
            """Recursively print migration chain"""
            if revision not in self.migrations:
                return

            info = self.migrations[revision]
            indent = '  ' * level
            timestamp = info['timestamp'].strftime('%Y-%m-%d %H:%M') if info['timestamp'] else 'N/A'
            print(f"{indent}├── {info['description']} ({timestamp})")
            
            # Find children
            children = [
                rev for rev, data in self.migrations.items()
                if data['down_revision'] == revision
            ]
            
            for child in sorted(children):
                print_branch(child, level + 1)

        print("\nMigration Chain:")
        print("---------------")
        for head in sorted(heads):
            print_branch(head)

def main():
    if len(sys.argv) != 2:
        print("Usage: python show_migration_chain.py <migrations_directory>")
        sys.exit(1)

    migrations_dir = sys.argv[1]
    if not os.path.exists(migrations_dir):
        print(f"Error: Directory {migrations_dir} does not exist")
        sys.exit(1)

    visualizer = MigrationChainVisualizer(migrations_dir)
    visualizer.print_chain()
    visualizer.create_graph()

if __name__ == '__main__':
    main() 