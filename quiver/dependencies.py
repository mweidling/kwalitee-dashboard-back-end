"""Creates data/dep_conflicts.json on basis of data/deps.json.

 deps.json lists the dependencies for each submodule of ocrd_all.
 to easily detect which submodules use the same dependencies in different versions,
 we aim for a JSON with the structure
 
 [
    { "dependency_1":
       "submodule_1": "version_number_of_dependency",
        "submodule_2": "version_number_of_dependency"
    },
    { "dependency_2":
        "submodule_1": "version_number_of_dependency",
        "submodule_2": "version_number_of_dependency"
    }
 ]

 in the resulting file only the dependency entries are kept in which at least two
 ocrd_all submodule have different version numbers installed.
"""

from pathlib import Path
import json

with open('data/deps.json', 'r', encoding='utf-8') as f:
    deps_json = json.load(f)

    # revert dependency JSON
    result = {}
    for dependency in deps_json:
        deps = deps_json[dependency]
        for pkg, version in deps.items():
            if not pkg in result:
                result[pkg] = {}
                result[pkg][dependency] = version
            else:
                result[pkg][dependency] = version

    # toss every dependency that only has one version.
    # it'll never have any conflicts because a) only one project uses it or b) several projects
    # use the same version.
    filtered = {}
    for pkg in result:
        versions = result[pkg].values()
        versions_wo_duplicates = list(set(versions))
        if not len(result[pkg]) == 1 and not len(versions_wo_duplicates) == 1:
            filtered[pkg] = result[pkg]
    json_str = json.dumps(filtered, indent=4, sort_keys=True)
    Path('data/dep_conflicts.json').write_text(json_str, encoding='utf-8')
