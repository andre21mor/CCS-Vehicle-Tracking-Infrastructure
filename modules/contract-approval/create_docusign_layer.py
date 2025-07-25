#!/usr/bin/env python3
"""
Script para crear Lambda Layer con DocuSign SDK
"""

import subprocess
import sys
import os
import tempfile
import zipfile

def create_docusign_layer():
    """Crear layer con DocuSign SDK"""
    
    # Crear directorio temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        python_dir = os.path.join(temp_dir, "python")
        os.makedirs(python_dir)
        
        # Instalar dependencias
        requirements = """${requirements}"""
        
        requirements_file = os.path.join(temp_dir, "requirements.txt")
        with open(requirements_file, 'w') as f:
            f.write(requirements)
        
        # Instalar paquetes
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", requirements_file,
            "-t", python_dir,
            "--no-deps"
        ], check=True)
        
        # Crear ZIP
        layer_zip = "docusign_layer.zip"
        with zipfile.ZipFile(layer_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(python_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Layer creado: {layer_zip}")

if __name__ == "__main__":
    create_docusign_layer()
