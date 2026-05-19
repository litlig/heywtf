import re
import sys

def interactive_prompt(response):
    match = re.search(r'```bash\n(.*?)```', response, re.DOTALL)
    if not match:
        return
    
    cmd = match.group(1).strip()
    if not cmd:
        return
    
    # Prompt the user
    print(f"Action: Run [r], Edit in terminal [e], Cancel [c]: ", end="")
    choice = input().strip().lower()
    if choice == 'r':
        import subprocess
        subprocess.run(cmd, shell=True)
    elif choice == 'e':
        with open("/tmp/buddy_edit_cmd", "w") as f:
            f.write(cmd)

