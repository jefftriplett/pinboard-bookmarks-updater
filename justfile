set dotenv-load := false

@_default:
    just --list

@update:
    pip install --upgrade -r requirements.in
    rm -rf requirements.txt
    pip-compile
