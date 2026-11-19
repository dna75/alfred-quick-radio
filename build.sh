#!/bin/bash
# Builds "Quick Radio.alfredworkflow" from the workflow/ folder.
cd "$(dirname "$0")/workflow" || exit 1
rm -f "../Quick Radio.alfredworkflow"
zip -q -r -X "../Quick Radio.alfredworkflow" . -x '.DS_Store' -x '__pycache__/*'
echo "Built: Quick Radio.alfredworkflow"
