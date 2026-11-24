from pathlib import Path

env_file = Path(".env")
configured = []
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            v = v.strip().strip("'\"")
            if len(v) > 5 and not v.startswith(("your_", "<", "change_")):
                configured.append(k.strip())

print("Configured keys in .env:")
for k in configured:
    print(" -", k)
