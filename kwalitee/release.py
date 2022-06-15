import json, re
import requests

class Release():

    def __init__(self, tag, projects):
        self.tag = tag
        self.projects = projects

    def __str__(self):
        return f'<Release {self.tag}>'

    def to_json(self):
        desc = {}
        desc['tag'] = self.tag
        desc['projects'] = self.projects
        return desc


def get_releases(test_mode=False):
    if test_mode:
        f = open('tests/assets/ocrd_all_releases.json')
        response_json = json.load(f)
    else:
        api_url = "https://api.github.com/repos/OCR-D/ocrd_all/releases"
        header = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(api_url, headers=header)
        response_json = json.loads(response.text)
    
    releases = []
    projects = []
    for entry in response_json:
        tag = entry['tag_name']
        filtered_projects = get_filtered_projects(entry, projects)
        if filtered_projects:
            releases.append(Release(tag, filtered_projects))
    return releases


def get_projects(json_data):
    markdown_desc = json_data['body']
    pattern = r'### \[(.*?)\]'
    return re.findall(pattern, markdown_desc)


def get_filtered_projects(entry, projects):
    entry_projects = get_projects(entry)
    filtered_projects = []
    for project in entry_projects:
        if (project in projects):
            pass
        else:
            filtered_projects.append(project)
            projects.append(project)
    return filtered_projects
