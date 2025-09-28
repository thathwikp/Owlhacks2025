"""
Startup script for the Nutrition Calculator project.
Provides easy access to different components of the system.
"""

import sys
import subprocess
import os


def run_simple_calculator():
    """Run the simple calculator example."""
    print("Running Simple Nutrition Calculator Example...")
    print("=" * 50)
    subprocess.run([sys.executable, "nutrition_calculator_simple.py"])


def run_cli():
    """Run the command-line interface."""
    print("Starting Nutrition Calculator CLI...")
    print("=" * 50)
    subprocess.run([sys.executable, "cli.py"])


def run_api():
    """Run the FastAPI web server."""
    print("Starting Nutrition Calculator API Server...")
    print("=" * 50)
    print("The API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    subprocess.run([sys.executable, "api.py"])


def run_tests():
    """Run the test examples."""
    print("Running Test Examples...")
    print("=" * 50)
    subprocess.run([sys.executable, "test_examples.py"])


def show_menu():
    """Display the main menu."""
    print("\n" + "=" * 60)
    print("NUTRITION CALCULATOR - MAIN MENU")
    print("=" * 60)
    print("Choose an option:")
    print("1. Run Simple Calculator Example")
    print("2. Run Interactive CLI")
    print("3. Start Web API Server")
    print("4. Run Test Examples")
    print("5. View Project Information")
    print("0. Exit")
    print("=" * 60)


def show_project_info():
    """Display project information."""
    print("\n" + "=" * 60)
    print("PROJECT INFORMATION")
    print("=" * 60)
    print("📁 Files in this project:")
    
    files = [
        ("nutrition_calculator_simple.py", "Core calculator (no dependencies)"),
        ("nutrition_calculator.py", "Full-featured version with Pydantic"),
        ("api.py", "FastAPI web service"),
        ("cli.py", "Command-line interface"),
        ("test_examples.py", "Test scenarios and examples"),
        ("requirements.txt", "Python dependencies"),
        ("README.md", "Comprehensive documentation")
    ]
    
    for filename, description in files:
        status = "✅" if os.path.exists(filename) else "❌"
        print(f"  {status} {filename:<30} - {description}")
    
    print(f"\n🚀 Quick Start Options:")
    print(f"  • Simple: python nutrition_calculator_simple.py")
    print(f"  • CLI: python cli.py")
    print(f"  • API: python api.py")
    print(f"  • Tests: python test_examples.py")
    
    print(f"\n📖 Documentation: README.md")
    print(f"🌐 API Docs: http://localhost:8000/docs (when API is running)")


def main():
    """Main function to handle user choices."""
    while True:
        show_menu()
        
        try:
            choice = input("\nEnter your choice (0-5): ").strip()
            
            if choice == "0":
                print("\nThank you for using the Nutrition Calculator!")
                break
            elif choice == "1":
                run_simple_calculator()
            elif choice == "2":
                run_cli()
            elif choice == "3":
                run_api()
            elif choice == "4":
                run_tests()
            elif choice == "5":
                show_project_info()
            else:
                print("\n❌ Invalid choice. Please enter a number between 0-5.")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
