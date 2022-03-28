set dotenv-load := false

@_default:
    just --list

@build:
    pip install --upgrade -r requirements.in
    rm -rf requirements.txt
    pip-compile
