set -eo pipefail
VERSION=1145141919
pipenv lock
pip install  --target ./hello_world -r requirements.txt
zip -r ${VERSION}.zip ./hello_world
aws s3 cp ${VERSION}.zip s3://ascending-devops/layers/