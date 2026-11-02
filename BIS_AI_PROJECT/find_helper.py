import os
import subprocess
from pathlib import Path

# Look for git-credential-manager.exe or git-credential-wincred.exe
paths_to_check = [
    r"C:\Program Files\Git\mingw64\bin",
    r"C:\Program Files\Git\mingw64\libexec\git-core",
    r"C:\Program Files (x86)\Git",
    r"C:\Users\Dell\AppData\Local\Programs\Git",
    r"C:\Program Files\Git",
    r"C:\Users\Dell\AppData\Local\MinGit",
    r"C:\Program Files\GitHub CLI",
    r"C:\Users\Dell\AppData\Local\GitHubDesktop"
]

found = []
for p in paths_to_check:
    if os.path.exists(p):
        for root, dirs, files in os.walk(p):
            for f in files:
                if "credential" in f.lower() and f.endswith(".exe"):
                    found.append(os.path.join(root, f))

print("FOUND CREDENTIAL HELPERS:")
for f in found:
    print(" ", f)

