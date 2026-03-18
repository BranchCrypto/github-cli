import subprocess
subprocess.run(["git", "add", "-A"], cwd=r"C:\Users\Administrator\Desktop\github")
subprocess.run(["git", "commit", "-m", "Production v1.0: full rewrite with 72 passing tests"], cwd=r"C:\Users\Administrator\Desktop\github")
r = subprocess.run(["git", "push", "origin", "main"], cwd=r"C:\Users\Administrator\Desktop\github", capture_output=True, text=True)
print(r.stdout)
if r.stderr: print(r.stderr)
