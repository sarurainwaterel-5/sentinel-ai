# Linux For Builders

Linux is our workshop.

The command line is an extension of thought.

Builders spend less time clicking.

More time creating.

Master concepts before commands.

Learn once.

Use forever.

---

# Philosophy

Linux is more than an operating system.

It is an engineering environment where every command is a tool and every tool has a purpose.

A builder should understand **why** a command is used before memorizing its syntax.

Commands become second nature through repetition while building real systems.

---

# Navigation

## Print Working Directory

```bash
pwd
```

Shows your current location.

---

## List Files

```bash
ls
```

Basic directory listing.

```bash
ls -la
```

Shows hidden files and permissions.

---

## Tree View

```bash
tree
tree -L 2
```

Visualize project structure.

---

## Change Directory

```bash
cd folder
cd ..
cd ~
```

Navigate through the filesystem.

---

# Creating Files & Directories

```bash
mkdir project
mkdir -p docs/design
touch README.md
```

---

# Viewing Files

```bash
cat filename.md
less filename.md
head filename.md
tail filename.md
nano filename.md
```

---

# Finding Things

Find empty markdown files

```bash
find docs -type f -name "*.md" -size 0
```

Find Python files

```bash
find . -name "*.py"
```

Find TODOs

```bash
grep -R "TODO" .
```

---

# Git

Repository status

```bash
git status
```

Stage changes

```bash
git add .
```

Commit

```bash
git commit -m "message"
```

View history

```bash
git log --oneline
```

Push

```bash
git push origin main
```

Tags

```bash
git tag -a v0.7.5 -m "Sprint 7.5"
git push origin v0.7.5
```

---

# Python

Virtual environment

```bash
python -m venv venv
source venv/bin/activate
deactivate
```

Run Python

```bash
python
python script.py
```

Quick script

```bash
python - << 'EOF'
print("Hello SentinelAI")
EOF
```

---

# FastAPI

Run backend

```bash
uvicorn app.main:app --reload
```

Test endpoint

```bash
curl http://127.0.0.1:8000/canon/health
```

---

# React

Install packages

```bash
npm install
```

Run development server

```bash
npm run dev
```

Build

```bash
npm run build
```

---

# Docker

Start services

```bash
docker compose up -d
```

Stop services

```bash
docker compose down
```

View running containers

```bash
docker ps
```

Logs

```bash
docker compose logs -f
```

---

# Project Exploration

View project

```bash
tree
```

Backend

```bash
tree backend
```

Frontend

```bash
tree frontend
```

Documentation

```bash
tree docs
```

---

# Engineering Habits

Before every commit:

- Run `git status`
- Review changed files
- Search for empty documentation
- Ensure the application starts successfully
- Update sprint documentation if architecture changed

---

# Closing Principle

Linux is not something to memorize.

It is something to practice.

Every command is another tool in the builder's workshop.

The more systems you build, the more natural the command line becomes.

# Builder's Mindset

Do not measure progress by the number of commands you remember.

Measure progress by the systems you can build.

Commands are temporary.

Understanding is permanent.
