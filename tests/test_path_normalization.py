from pathlib import Path
import os
import urllib.parse
import sys

# Mocking the normalize_path function from the server
def normalize_path(path_str: str) -> Path:
    if not path_str:
        return Path(".")
    if path_str.startswith("file://"):
        path_str = path_str[7:]
        if os.name == 'nt' and path_str.startswith("/"):
            path_str = path_str[1:]
    path_str = urllib.parse.unquote(path_str)
    path_str = os.path.expanduser(path_str)
    return Path(path_str).resolve()

def test_normalization():
    home = os.path.expanduser("~")
    cwd = os.getcwd()
    
    test_cases = [
        ("simple/path/image.jpg", os.path.join(cwd, "simple/path/image.jpg")),
        ("file:///Users/ycs/photo.jpg", "/Users/ycs/photo.jpg"),
        ("file://"+cwd+"/my%20photo.jpg", os.path.join(cwd, "my photo.jpg")),
        ("~/pictures/vacation.jpg", os.path.join(home, "pictures/vacation.jpg")),
        ("./relative/path.png", os.path.join(cwd, "relative/path.png")),
    ]
    
    print("🧪 Testing Path Normalization...")
    all_passed = True
    
    for input_path, expected_output in test_cases:
        actual = str(normalize_path(input_path))
        expected = str(Path(expected_output).resolve())
        
        if actual == expected:
            print(f"✅ PASS: '{input_path}' -> '{actual}'")
        else:
            print(f"❌ FAIL: '{input_path}'")
            print(f"   Expected: {expected}")
            print(f"   Actual:   {actual}")
            all_passed = False
            
    if all_passed:
        print("\n✨ All normalization tests passed!")
    else:
        print("\n⚠️ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_normalization()
