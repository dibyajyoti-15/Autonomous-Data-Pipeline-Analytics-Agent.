#!/usr/bin/env python3
"""
Setup script for AI Data Analytics Copilot
Automates the setup process
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Created directory: {path}")
    else:
        print(f"ℹ️  Directory already exists: {path}")

def create_secrets_file():
    """Create secrets.toml template"""
    secrets_dir = ".streamlit"
    secrets_file = os.path.join(secrets_dir, "secrets.toml")
    
    create_directory(secrets_dir)
    
    if not os.path.exists(secrets_file):
        with open(secrets_file, "w") as f:
            f.write('# Streamlit Secrets Configuration\n')
            f.write('# Replace with your actual OpenAI API key\n\n')
            f.write('OPENAI_API_KEY = "your-openai-api-key-here"\n')
        print(f"✅ Created secrets template: {secrets_file}")
        print("⚠️  Please edit .streamlit/secrets.toml and add your OpenAI API key!")
    else:
        print(f"ℹ️  Secrets file already exists: {secrets_file}")

def main():
    print_header("🤖 AI Data Analytics Copilot - Setup")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Install requirements
    print_header("Installing Dependencies")
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("⚠️  Installation had errors. Please check the output above.")
    
    # Create .streamlit directory and secrets file
    print_header("Setting up Configuration")
    create_secrets_file()
    
    # Initialize database
    print_header("Initializing Database")
    if run_command("python database.py", "Creating and populating database"):
        print("✅ Database initialized with sample data!")
    
    # Final instructions
    print_header("Setup Complete!")
    print("🎉 All set! Here's what to do next:\n")
    print("1. Edit .streamlit/secrets.toml and add your OpenAI API key")
    print("2. Run the application:")
    print("   streamlit run app.py")
    print("\n3. Open your browser at: http://localhost:8501")
    print("\n📚 For more information, see README.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
