# test_openai.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from openai import OpenAI
    print("✓ OpenAI import successful")
    
    # Test client creation (without making actual API call)
    client = OpenAI(api_key="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")
    print("✓ OpenAI client creation successful")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
except Exception as e:
    print(f"✓ Import works, but: {e}")