import os
import re

def fix_imports(directory):
    # Regex to match version numbers at the end of import paths
    # Matches @x.y.z just before the closing quote
    pattern = re.compile(r'(@\d+\.\d+\.\d+)("|(\';))')
    
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = re.sub(r'(@\d+\.\d+\.\d+)("|\')', r'\2', content)
                
                if new_content != content:
                    print(f"Fixing {filepath}")
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    count += 1
    
    print(f"Fixed imports in {count} files.")

if __name__ == "__main__":
    fix_imports(r"d:\Mergenlite\frontend\src")
