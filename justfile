default:
    just --list

# run streamlit app
run:
    uv run streamlit app.py

# linting
lint:
    uv run black .
    uv run ruff check --fix

# create requirements file for deployment
req:
    uv pip freeze > requirements.txt
