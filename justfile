set dotenv-load := false

@_default:
    just --list

@bootstrap:
    pip install -U -r requirements.in

@build:
    cog -P -r README.md

@fmt:
    just --fmt --unstable

@update:
    pip install --upgrade -r requirements.in
    rm -rf requirements.txt
    pip-compile
