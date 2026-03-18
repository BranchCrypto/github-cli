import subprocess
subprocess.run(["git", "add", "-A"], cwd=r"C:\Users\Administrator\Desktop\github")
subprocess.run(["git", "commit", "-m", "Fix repo list view: action routing, encoding, null safety"], cwd=r"C:\Users\Administrator\Desktop\github")
result = subprocess.run(["git", "push", "origin", "main"], cwd=r"C:\Users\Administrator\Desktop\github", capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)
