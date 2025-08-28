import os

structure = {
    "common/aws": ["__init__.py", "ec2_utils.py", "s3_utils.py", "sg_utils.py"],
    "common": ["__init__.py", "config.py", "logger.py", "utils.py"],
    "apps/app1-fastapi": ["main.py", "requirements.txt"],
    "apps/app2-flask": ["main.py", "requirements.txt"],
    "tests/test_common": [],
    "tests/test_app1": [],
    "tests/test_app2": [],
    "scripts": ["run_all.sh", "deploy.sh"],
    "docker": ["app1.Dockerfile", "app2.Dockerfile"],
    "infra": []
}

for path, files in structure.items():
    os.makedirs(path, exist_ok=True)
    for file in files:
        open(os.path.join(path, file), 'w').close()

# Root-level files
for f in ["README.md", ".env.example", "requirements.txt"]:
    open(f, 'w').close()

print("✅ Project structure created!")

