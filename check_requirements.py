import re
import requests

def get_latest_version(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()["info"]["version"]
    except Exception:
        pass
    return None

def update_requirements(requirements_text):
    pattern = re.compile(r'^([^#\n]+?)([ \t]*#[^\n]*)?$')
    updated_lines = []
    update_log = []

    for line in requirements_text.splitlines():
        match = pattern.match(line)
        if not match:
            updated_lines.append(line)
            continue

        pkg_line, comment = match.groups()
        comment = comment or ''
        pkg_line = pkg_line.strip()

        if not pkg_line or pkg_line.startswith('#'):
            updated_lines.append(line)
            continue

        if '==' in pkg_line:
            pkg, current_version = pkg_line.split('==')
            pkg = pkg.strip()
            current_version = current_version.strip()
            latest_version = get_latest_version(pkg)
            if latest_version and latest_version != current_version:
                updated_lines.append(f"{pkg}=={latest_version}{comment}")
                update_log.append(f"{pkg} updated from {current_version} to {latest_version}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    return '\n'.join(updated_lines), update_log

# Load requirements.txt
with open('requirements.txt', 'r') as f:
    content = f.read()

# Update and get log
updated_content, logs = update_requirements(content)

# Save updated file
with open('requirements.txt', 'w') as f:
    f.write(updated_content)

# Log updates
if logs:
    print("Updated Packages:")
    for log in logs:
        print(log)
else:
    print("All packages are up to date.")
