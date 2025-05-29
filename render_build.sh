
#!/usr/bin/env bash
# exit on error
set -o errexit

# npm install
# npm run build

sudo apt-get update -y && sudo apt-get install -y graphviz libgraphviz-dev

pipenv install

pipenv run upgrade