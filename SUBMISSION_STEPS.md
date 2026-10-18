# Consolidation: finish and submit step by step

Use the completed News Application in this archive. The original application and
Git history have been preserved; the required documentation and container commits
have been added and merged locally. Do not repeat their branch creation steps.

## 1. Extract into a new folder

Extract the ZIP into a new location, for example:
`C:\Users\henri.katompe\Downloads\News_Consolidation_Ready`

Open its `news-application` subfolder in VS Code. Keep your old project as a backup;
do not combine or overwrite two different `.git` directories.

In Terminal -> New Terminal, navigate to the folder containing manage.py. For the
example location above:

```powershell
Set-Location -LiteralPath "C:\Users\henri.katompe\Downloads\News_Consolidation_Ready\news-application"
Get-Location
Test-Path .\manage.py
Test-Path .\.git
```

Both Test-Path commands must return True. Do not run these steps in System32.

## 2. Check the prepared Git history

```powershell
git status
git branch
git log --graph --oneline --all -15
git remote -v
```

Expected: current branch main; branches docs and container; a clean working tree;
origin points to https://github.com/hkk5cape/news-application.git. The merge graph
shows the original history and the two completed branches. If .git is missing,
extract the ZIP again with a tool that preserves hidden folders rather than
initialising a new history. A backup history bundle is supplied outside the project.

## 3. Check the included documentation

```powershell
Start-Process .\docs\_build\html\index.html
```

Open Installation, User walkthrough and Python reference. Generated HTML is
already committed. You can rebuild it using README section 8.

## 4. Run the application and Docker checks

Follow README sections 2-4 for a virtual environment and MariaDB, or section 5 for
Docker. With Python available and Docker Desktop running, use:

```powershell
python scripts/configure.py --docker
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 240
docker compose ps
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
Start-Process "http://127.0.0.1:8000/"
```

The configuration command is for a fresh extracted folder without .env; it refuses
to overwrite an existing file. README section 5 also has a Docker-only command if
host Python is unavailable. Both services should become healthy.

Register real Editor and Journalist accounts. Create a publisher, add its journalist,
write a draft and approve it as the editor. Register a Reader and confirm that the
approved story can be read. Follow docs/MANUAL_TESTS.md for further checks.
Console emails appear in `docker compose logs web`.

Docker and MariaDB were unavailable in the preparation environment, so this step
is still required before review. If startup fails, capture:

```powershell
docker compose logs --tail 100 db web
```

Do not upload a real .env or database when asking for help. Stop containers with
`docker compose down`; the database volume is retained.

## 5. Publish the prepared commits and branches

The existing public repository is https://github.com/hkk5cape/news-application.
Sign into Git with an account that can push to it, then run from the extracted
project folder:

```powershell
git push origin main
git push origin docs
git push origin container
```

Git may open a browser for sign-in. Use your GitHub credentials in that sign-in
flow, not in capstone.txt or the README. Do not use force push. If Git rejects a
push because the remote changed, stop and retain the message so the histories can
be reconciled. The supplied work is based on commit bcfa69c from your archive.

If the remote is not origin or points elsewhere, inspect git remote -v before
changing it. If your public repository URL changes, update capstone.txt and the
README clone URL, commit those edits and push again.

## 6. Verify GitHub has the completed version

Open https://github.com/hkk5cape/news-application and check:

- main contains this revised README, Dockerfile, compose.yaml and capstone.txt.
- docs and container are visible in the branch selector.
- docs/_build/html/index.html exists (download/open locally to view the HTML).
- the commit history includes separate model/policy/form/service/view documentation
  commits and both merge commits.
- .env, virtual environments, databases and caches are absent from tracked files.

This package has not pushed to GitHub for you. Its connection was read-only when
prepared. Do not assume the online copy includes the fixes until the push succeeds.

For an independent installation check, clone to a different folder:

```powershell
Set-Location ..
git clone https://github.com/hkk5cape/news-application.git news-application-fresh-check
Set-Location .\news-application-fresh-check
```

Follow the README there. Stop the first installation before using port 8000 for
another one. If Docker was already used, use a separate Compose project name for
an independent test, or explicitly keep the existing database configuration.

## 7. Prepare the task submission

The required link file is capstone.txt. It already contains:
https://github.com/hkk5cape/news-application

For the course task folder, submit:

1. The completed News Application project files (the supplied clean source ZIP).
2. capstone.txt as a separate text file for the reviewer to open easily.

The supplied source ZIP already contains the same capstone.txt. The history bundle
is an optional backup for you; GitHub holds the reviewable history once pushed.
A single project ZIP plus the separate link avoids duplicate loose source snippets.
If the portal requires unpacked files, upload the project folder instead of also
uploading a second duplicate copy of its source.

Do not upload .env, local databases, virtual environments or old duplicate project
archives. Generated Sphinx HTML MUST remain included for this assignment.

## 8. Request review

Only after Docker checks, the application walkthrough and GitHub publication
succeed, open the Consolidation task on your course dashboard, confirm the project
files and capstone.txt are present, and select Request review.
