set -eo pipefail
pipenv lock
pip3 install  --target ./hello_world_dependencies -r requirements.txt
zip -r ${VERSION}.zip ./hello_world_dependencies
aws s3 cp ${VERSION}.zip s3://xiaoyao-sandbox/layers/
rm -rf ./hello_world_dependencies
rm -f ${VERSION}.zip