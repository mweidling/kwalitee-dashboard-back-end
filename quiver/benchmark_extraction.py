"""This module is responsible for creating the resulting JSON file of the
benchmarking. It extracts the relevant information from the NextFlow processes. """

import json
import sys
from os import scandir, listdir
from re import search
import xml.etree.ElementTree as ET

METS = '{http://www.loc.gov/METS/}'

#{
 #   "eval_workflow_id": "wf2-data345-eval1",
 #   "label": "Workflow 2 on Data 345",
 #   "metadata": {
 #     "data_creation_workflow": "https://example.org/workflow/2",
 #     "eval_workflow_url": "https://example.org/workflow/eval1",
 #     "eval_data": "https://example.org/workspace/345",
 #     "data_properties": {
 #       "fonts": ["antiqua", "fraktur"],
 #       "publication_year": "19. century",
 #       "number_of_pages": "100",
 #       "layout": "simple"
 #     }
 #   }
 # }

def make_result_json(workspace_path, mets_path):
    data_name = workspace_path.split('/')[-2]
    eval_workflow_id = 'wf-data'+ data_name + '-eval'
    label = 'Workflow on data ' + data_name
    metadata = make_metadata(workspace_path, mets_path)
    benchmarks = extract_benchmarks(workspace_path, mets_path)
    return {
        'eval_workflow_id': eval_workflow_id,
        'label': label,
        'metadata': metadata,
        'evaluation_results': benchmarks
    }

def make_metadata(workspace_path, mets_path):
    data_creation_workflow = ''
    workflow_steps = get_workflow_steps(mets_path)
    workflow_model = get_workflow_model(mets_path)
    eval_workflow_url = ''
    eval_data = ''
    eval_tool = get_eval_tool(mets_path)
    gt_data = get_gt_data_url(workspace_path)
    data_properties = ''
    return {
            'data_creation_workflow': data_creation_workflow,
            'workflow_steps': workflow_steps,
            'workflow_model': workflow_model,
            'eval_workflow_url': eval_workflow_url,
            'eval_data': eval_data,
            'eval_tool': eval_tool,
            'gt_data': gt_data,
            'data_properties': data_properties
        }

def get_element_from_mets(mets_path, xpath):
    with open(mets_path, 'r', encoding='utf-8') as f:
        tree = ET.parse(f)
        return tree.findall(xpath)

def get_workflow_steps(mets_path):
    xpath =f'.//{METS}agent[@ROLE="OTHER"]/{METS}name'
    name_elements = get_element_from_mets(mets_path, xpath)
    formatted_names = []
    for e in name_elements:
        formatted_names.append(e.text.split(' ')[0])

    return formatted_names

def get_workflow_model(mets_path):
    OCRD = '{https://ocr-d.de}'
    xpath = f'.//{METS}agent[@OTHERROLE="layout/segmentation/region"]/{METS}note[@{OCRD}option="parameter"]'
    parameters = get_element_from_mets(mets_path, xpath)[0].text
    params_json = json.loads(parameters)
    return params_json['model']

def get_eval_tool(mets_path):
    xpath = f'.//{METS}agent[@OTHERROLE="recognition/text-recognition"]/{METS}name'
    return get_element_from_mets(mets_path, xpath)[0].text

def get_gt_data_url(workspace_path):
    current_workspace = workspace_path.split('/')[-2]
    url = 'https://github.com/OCR-D/quiver-data/blob/main/' + current_workspace + '.ocrd.zip'
    return url

def extract_benchmarks(workspace_path, mets_path):
    json_dirs = get_eval_jsons(workspace_path)

    result = [
        make_document_wide_eval_results(workspace_path),
        {'by_page': make_eval_results_by_page(json_dirs, mets_path)}
    ]

    return result

def make_document_wide_eval_results(workspace_path):
    return {'document_wide':
        {
            'wall_time': get_nf_completed_stats(workspace_path),
            'cer': get_mean_cer(workspace_path, 'SEG-LINE'),
            'cer_min_max': get_cer_min_max(workspace_path, 'SEG-LINE')
        }
    }

def get_nf_completed_stats(workspace_path):
    result_path = workspace_path + '/../../results/'

    for file_name in listdir(workspace_path + '/../../results'):
        if 'process' not in file_name and 'completed' in file_name:
            completed_file = file_name

    with open(result_path + completed_file, 'r', encoding='utf-8') as f:
        file = json.load(f)
        duration = file['metadata']['workflow']['duration']
    return duration


def get_mean_cer(workspace_path, gt_type):
    cers = get_cers_for_gt_type(workspace_path, gt_type)
    return sum(cers) / len(cers)

def get_cers_for_gt_type(workspace_path, gt_type):
    eval_jsons = []
    eval_dir_path = workspace_path + '/OCR-D-EVAL-' + gt_type + '/'
    for file_name in listdir(eval_dir_path):
        if 'json' in file_name:
            eval_jsons.append(file_name)
    cers = []
    for eval_json in eval_jsons:
        with open(eval_dir_path + eval_json, 'r', encoding='utf-8') as f:
            json_file = json.load(f)
            cers.append(json_file['cer'])
    return cers

def get_cer_min_max(workspace_path, gt_type):
    cers = get_cers_for_gt_type(workspace_path, gt_type)
    return [min(cers), max(cers)]

def make_eval_results_by_page(json_dirs, mets_path):
    result = []
    for d in json_dirs:
        for file_path in json_dirs[d]:
            result.append(get_metrics_for_page(file_path, mets_path))

    return result

def get_eval_dirs(workspace_dir):
    list_subfolders_with_paths = [f.path for f in scandir(workspace_dir) if f.is_dir()]
    eval_dirs = [name for name in list_subfolders_with_paths if search('EVAL', name)]
    return eval_dirs


def get_eval_jsons(workspace_dir):
    eval_dirs = get_eval_dirs(workspace_dir)
    result = {}
    for eval_dir in eval_dirs:
        files_in_dir = [f.path for f in scandir(eval_dir) if f.is_file()]
        json_files = [name for name in files_in_dir if search('json', name)]
        result[eval_dir] = sorted(json_files)
    return result


def get_page_id(json_file_path, mets_path):
    json_file_name = get_file_name_from_path(json_file_path)
    gt_file_name = json_file_name.replace('EVAL', 'GT')
    xpath = f'.//{METS}fptr[@FILEID="{gt_file_name}"]/..'
    return get_element_from_mets(mets_path, xpath)[0].attrib['ID']


def get_file_name_from_path(json_file_path):
    json_file_name = json_file_path.split('/')[-1]
    name_wo_ext = json_file_name.split('.')[0]
    return name_wo_ext


def get_metrics_for_page(json_file_path, mets_path):
    page_id = get_page_id(json_file_path, mets_path)
    with open(json_file_path, 'r', encoding='utf-8') as file:
        eval_file = json.load(file)

        cer = eval_file['cer']
    metrics = {
        'page_id': page_id,
        'cer': cer
    }

    return metrics

if __name__ == '__main__':
    WORKSPACE_PATH = sys.argv[1]
    workflow_name = sys.argv[2].rsplit('/', maxsplit=1)[-1].split('.')[0]
    METS_PATH = WORKSPACE_PATH + 'mets.xml'

    dictionary = make_result_json(WORKSPACE_PATH, METS_PATH)

    json_object = json.dumps(dictionary, indent=4)
    output = WORKSPACE_PATH + '/eval_result_' + workflow_name + '.json'
    # Writing to sample.json
    with open(output, 'w', encoding='utf-8') as outfile:
        outfile.write(json_object)
