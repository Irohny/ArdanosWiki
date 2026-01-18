set shell := ["bash", "-cu"]

default:
    just --list

# run streamlit app
run:
    uv run streamlit run app.py

# linting
lint:
    uv run black .
    uv run ruff check --fix

# create requirements file for deployment
req:
    uv pip freeze > requirements.txt

# create changelog
changelog:
    ./generate_changelog.sh > CHANGELOG.md

# create a well structure git commit
commit msg:
    just lint
    just req
    just changelog
    git add -A
    git commit -m "{{msg}}"
    git push
    git pull
    
# calculate the cost of a trank given material cost and difficulty
trank material sg:
    python3 trank.py {{material}} {{sg}}
