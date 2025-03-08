import os
import argparse
from pathlib import Path
import sys
import fnmatch
import re

def is_binary_file(file_path):
    """Check if file is binary."""
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)
            return b'\0' in chunk  # A simple heuristic for detecting binary files
    except Exception as e:
        print(f"Error checking if file is binary: {file_path}, Error: {e}", file=sys.stderr)
        return True

def should_ignore_file(file_path, ignore_extensions, ignore_dirs, ignore_patterns, root_path, script_path, output_path):
    """Check if file should be ignored based on extension or directory."""
    # Skip the script itself and the output file
    if os.path.samefile(file_path, script_path) if script_path else False:
        return True
    
    if output_path and os.path.exists(output_path) and os.path.samefile(file_path, output_path):
        return True
    
    # Check if file is in an ignored directory
    for ignore_dir in ignore_dirs:
        if ignore_dir in file_path.parts:
            return True
    
    # Check if file matches an ignored pattern
    rel_path = os.path.relpath(file_path, root_path)
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
    
    # Check file extension
    if file_path.suffix.lower() in ignore_extensions:
        return True
    
    return False

def should_ignore_dir(dir_path, ignore_dirs, ignore_patterns, root_path):
    """Check if directory should be ignored."""
    # Check if directory name is in the ignore list
    dir_name = dir_path.name
    if dir_name in ignore_dirs:
        return True
    
    # Check if directory path matches an ignored pattern
    rel_path = os.path.relpath(dir_path, root_path)
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Also check if any parent directory matches (to handle nested dirs)
        for part in Path(rel_path).parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    
    return False

def scrape_project(project_path, output_file, ignore_extensions=None, ignore_dirs=None, 
                   ignore_patterns=None, max_file_size_mb=10, verbosity=0):
    """
    Scrape a project directory and create a text file with structure and content.
    
    Args:
        project_path (str): Path to the project directory
        output_file (str): Path to the output text file
        ignore_extensions (list): List of file extensions to ignore
        ignore_dirs (list): List of directory names to ignore
        ignore_patterns (list): List of path patterns to ignore (glob syntax)
        max_file_size_mb (int): Maximum file size in MB to include
        verbosity (int): Level of verbosity (0=quiet, 1=normal, 2=verbose)
    """
    if ignore_extensions is None:
        ignore_extensions = ['.exe', '.dll', '.so', '.pyc', '.pyo', '.jar', '.war', 
                            '.ear', '.zip', '.tar', '.gz', '.rar', '.7z', '.db', 
                            '.sqlite', '.sqlite3', '.mdf', '.ldf', '.jpg', '.jpeg', 
                            '.png', '.gif', '.bmp', '.ico', '.mp3', '.mp4', '.avi', 
                            '.mov', '.wmv', '.flv', '.pdf', '.ps1', '.sh', '.bat', '.cmd']
    
    if ignore_dirs is None:
        ignore_dirs = ['.git', 'node_modules', '__pycache__', 'venv', 'env', 
                      '.venv', '.env', 'dist', 'build', 'target', 'bin', 'obj',
                      '.idea', '.vscode', 'data', 'logs', 'temp', 'cache', 'backup', 'docs', 'test', 'tests', 'tests']
    
    if ignore_patterns is None:
        ignore_patterns = []
    
    # Add patterns to ignore context and temp files
    ignore_patterns.extend(["*_context*.txt", "*_output*.txt", "*.context", "project_contents*.txt"])
    
    max_file_size_bytes = max_file_size_mb * 1024 * 1024
    project_path = Path(project_path).resolve()
    
    # Get absolute paths for script and output
    script_path = Path(__file__).resolve() if '__file__' in globals() else None
    output_path = Path(output_file).resolve() if output_file else None
    
    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: {project_path} does not exist or is not a directory", file=sys.stderr)
        return
    
    skipped_files_count = 0
    total_files_count = 0
    processed_files_count = 0
    
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            out_file.write(f"# PROJECT STRUCTURE AND CONTENTS\n")
            out_file.write(f"# Project: {project_path}\n\n")
            
            # First, write the folder structure
            out_file.write("## FOLDER STRUCTURE\n\n")
            
            for root, dirs, files in os.walk(project_path):
                root_path = Path(root)
                
                # Filter out ignored directories (modifies dirs in-place to affect walk)
                dirs[:] = [d for d in dirs if not should_ignore_dir(root_path / d, ignore_dirs, ignore_patterns, project_path)]
                
                rel_path = os.path.relpath(root, project_path)
                if rel_path == '.':
                    rel_path = ''
                
                # Skip printing the root directory
                if rel_path:
                    depth = rel_path.count(os.path.sep)
                    indent = '  ' * depth
                    dir_name = os.path.basename(root)
                    out_file.write(f"{indent}📁 {dir_name}/\n")
                
                # Sort files for consistency
                files.sort()
                for file in files:
                    file_path = Path(os.path.join(root, file))
                    
                    if should_ignore_file(file_path, ignore_extensions, ignore_dirs, ignore_patterns, project_path, script_path, output_path):
                        continue
                    
                    rel_file_path = os.path.relpath(file_path, project_path)
                    depth = rel_file_path.count(os.path.sep)
                    indent = '  ' * depth
                    out_file.write(f"{indent}📄 {file}\n")
            
            # Then, write the file contents
            out_file.write("\n\n## FILE CONTENTS\n\n")
            
            for root, dirs, files in os.walk(project_path):
                root_path = Path(root)
                
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not should_ignore_dir(root_path / d, ignore_dirs, ignore_patterns, project_path)]
                
                # Sort files for consistency
                files.sort()
                for file in files:
                    file_path = Path(os.path.join(root, file))
                    total_files_count += 1
                    
                    if should_ignore_file(file_path, ignore_extensions, ignore_dirs, ignore_patterns, project_path, script_path, output_path):
                        skipped_files_count += 1
                        if verbosity >= 2:
                            print(f"Skipping ignored file: {file_path}")
                        continue
                    
                    try:
                        # Skip large files
                        file_size = file_path.stat().st_size
                        if file_size > max_file_size_bytes:
                            skipped_files_count += 1
                            if verbosity >= 1:
                                print(f"Skipping large file: {file_path} ({file_size/1024/1024:.2f} MB)")
                            out_file.write(f"\n\n### FILE: {os.path.relpath(file_path, project_path)} (SKIPPED - Size: {file_size/1024/1024:.2f} MB)\n")
                            continue
                        
                        # Skip binary files
                        if is_binary_file(file_path):
                            skipped_files_count += 1
                            if verbosity >= 1:
                                print(f"Skipping binary file: {file_path}")
                            out_file.write(f"\n\n### FILE: {os.path.relpath(file_path, project_path)} (SKIPPED - Binary file)\n")
                            continue
                        
                        # Read and write file content
                        processed_files_count += 1
                        if verbosity >= 2:
                            print(f"Processing file: {file_path}")
                        out_file.write(f"\n\n### FILE: {os.path.relpath(file_path, project_path)}\n")
                        out_file.write("```\n")
                        
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                            out_file.write(content)
                        
                        out_file.write("\n```\n")
                        
                    except Exception as e:
                        skipped_files_count += 1
                        out_file.write(f"\n\n### FILE: {os.path.relpath(file_path, project_path)} (ERROR: {str(e)})\n")
                        print(f"Error processing file: {file_path}, Error: {e}", file=sys.stderr)
            
            # Add summary at the end
            out_file.write(f"\n\n## SUMMARY\n")
            out_file.write(f"- Total files found: {total_files_count}\n")
            out_file.write(f"- Files processed: {processed_files_count}\n")
            out_file.write(f"- Files skipped: {skipped_files_count}\n")
            out_file.write(f"- Script version: 1.1.0\n")
            
            if verbosity >= 1:
                print(f"Project scraping completed. Output saved to {output_file}")
                print(f"Files processed: {processed_files_count}, Files skipped: {skipped_files_count}")
            
    except Exception as e:
        print(f"Error during project scraping: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Scrape a project directory and create a text file with structure and content.')
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('--output', '-o', default='project_contents.txt', help='Output file path')
    parser.add_argument('--ignore-ext', '-i', nargs='+', help='Additional file extensions to ignore')
    parser.add_argument('--ignore-dirs', '-d', nargs='+', help='Additional directories to ignore')
    parser.add_argument('--ignore-patterns', '-p', nargs='+', help='Path patterns to ignore (uses glob syntax, e.g. "*/temp/*")')
    parser.add_argument('--max-size', '-m', type=int, default=10, help='Maximum file size in MB to include')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity (can use multiple times)')
    
    args = parser.parse_args()
    
    # Convert additional ignore extensions to the proper format
    ignore_extensions = None
    if args.ignore_ext:
        ignore_extensions = [f".{ext.lstrip('.')}" for ext in args.ignore_ext]
    
    scrape_project(
        args.project_path, 
        args.output, 
        ignore_extensions=ignore_extensions, 
        ignore_dirs=args.ignore_dirs,
        ignore_patterns=args.ignore_patterns,
        max_file_size_mb=args.max_size,
        verbosity=args.verbose
    )

if __name__ == "__main__":
    main() 