"""
This module defines the API endpoint used by NextFlow
since NextFlow allows to get its result as JSON only when posting them to a web server.
"""

import json
from os import getcwd
from pathlib import Path
from typing import Dict, Union

from fastapi import FastAPI

app = FastAPI()


@app.post("/nextflow/")
def save_workflow(item: Dict[str, Union[str, float,Dict]]):
    """
    Defines the POST end point which dumps all the data NextFlow sends to
    $PROJECT_PATH/workflows/nf-results/.

    Args:
        item (Dict): A JSON object produced by NextFlow according to 
        https://www.nextflow.io/docs/latest/tracing.html#weblog-via-http.
    """
    event = item['event']
    output_name = item['runName'] + '_' + item['runId']
    output = getcwd() + '/../nf-results/' + output_name + '_' + event + '.json'
    json_str = json.dumps(item, indent=4, sort_keys=True)
    Path(output).write_text(json_str, encoding='utf-8')
