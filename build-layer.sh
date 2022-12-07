set -eo pipefail
pipenv lock
pip3 install  --target ./python -r requirements.txt
zip -r ${VERSION}.zip ./python
aws s3 cp ${VERSION}.zip s3://xiaoyao-sandbox/layers/
rm -rf ./python
rm -f ${VERSION}.zip