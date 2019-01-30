#!/usr/bin/env python

import argparse
import collections
import functools
import importlib
import inspect

# notation:
# * pkg: string name of package
# * package: loaded package
# * name: string name of package contents (module, class, function, ...)
# * obj: loaded version of `name`

def is_api_member(package, name):
    obj = getattr(package, name)
    ret = not name.startswith('_') and not inspect.ismodule(obj)
    return ret

def import_obj(import_string):
    path = import_string.split('.')
    root = importlib.import_module(path[0])
    current = root
    for mod_name in path[1:]:
        current = getattr(current, mod_name)
    return current

def import_name(prefix, name):
    """Location it was imported from"""
    return prefix + '.' + name

def full_name(package, name):
    """True, fully-qualified name"""
    obj = getattr(package, name)
    try:
        full_name = obj.__module__ + "." + obj.__name__
    except AttributeError:
        # not a package/module/class, so an instance of something
        # note that this doesn't get the case that we import an instance
        # from somewhere else to get the "true" name
        full_name = import_name(package.__name__, name)
    return full_name

def is_cyclical(package_path):
    path = package_path.split('.')
    root = importlib.import_module(path[0])
    modules = {root}
    current = root
    for mod_name in path[1:]:
        current = getattr(current, mod_name)
        modules.add(current)

    return len(modules) < len(path)


def find_all_names(pkg, prefix=None, found=None):
    if found is None:
        found = {}

    if prefix is None:
        package = importlib.import_module(pkg)
        root_package_name = package.__name__
        new_prefix = pkg
    else:
        root_package_name = prefix.split('.')[0]
        package = import_obj(prefix + '.' + pkg)
        new_prefix = prefix + '.' + pkg

    objs = {name: getattr(package, name) for name in dir(package)}
    found_here = {import_name(new_prefix, name): full_name(package, name)
                  for name in dir(package)}
    pkgs = [name for name, obj in objs.items() if inspect.ismodule(obj)]
    pkgs = [name for name in pkgs
            if objs[name].__name__.startswith(root_package_name)]
    pkgs = [name for name in pkgs if not is_cyclical(new_prefix + '.' + name)]
    found.update(found_here)
    for p_name in pkgs:
        found.update(find_all_names(p_name,
                                    new_prefix,
                                    found))
    return found

def select_api_valid_names(name_dict, package_name):
    # split out anything with a _ prefix (hidden API)
    names = {
        import_n: full_n for import_n, full_n in name_dict.items()
        if "._" not in import_n and full_n.startswith(package_name)
    }
    return names

def is_noninstance(obj):
    return (inspect.isclass(obj) or inspect.ismodule(obj)
            or inspect.ismethod(obj) or inspect.isfunction(obj))

def select_non_instance(names):
    return {
        import_n: full_n for import_n, full_n in names.items()
        if is_noninstance(import_obj(import_n))
    }

def select_non_module(names):
    return {
        import_n: full_n for import_n, full_n in names.items()
        if not inspect.ismodule(import_obj(import_n))
    }

def first_appearance(names):
    # well, this is a little magical, isn't it?
    return {
        sorted(appearances, key=lambda s: s.count('.'))[0]: full_n
        for full_n, appearances in all_appearances(names).items()
    }

def all_appearances(names):
    out_names = collections.defaultdict(list)
    for import_n, full_n in names.items():
        out_names[full_n].append(import_n)
    return out_names

def api_directory_sortkey(name, api_directories):
    # return the deepest-nested match to the API
    matches = [api_dir for api_dir in api_directories
               if name.startswith(api_dir)]
    key_1 = max(s.count('.') for s in matches)
    key_2 = name.count('.') - key_1
    return key_2, -key_1


def api_names(names, api_directories):
    sortkey=functools.partial(api_directory_sortkey,
                              api_directories=api_directories)
    return {
        sorted(appearances, key=sortkey)[0]: full_n
        for full_n, appearances in all_appearances(names).items()
    }

def in_api_directory(name, api_directories):
    result = api_directory_sortkey(name, api_directories)[0] == 1
    # print(api_directory_sortkey(name, api_directories))
    return result

def filter_by_in_api(names, api_directories, in_api=True):
    return {
        import_n: full_n
        for import_n, full_n in api_names(names, api_directories).items()
        if in_api_directory(import_n, api_directories) == in_api
    }

def all_api_aliases(names, api_directories):
    api_names = filter_by_in_api(names, api_directories, in_api=True)
    all_names = all_appearances(names)
    all_api_aliases = {
        import_n: sorted(list(set(all_names[full_n]) - set([import_n])),
                         key=lambda s: s.count('.'))
        for import_n, full_n in api_names.items()
    }
    return all_api_aliases

runtype_help = """
Select the type of run. Options are 'first' (return the first found through
breadth-first search), 'all' (return the all possible names), and three
choices that require --api-file: 'api_names' (show the first found with
preference for the API directories), 'in_api' (show only objects in the
API), 'not_in_api' (show only objects not in the API), where "in the API"
means they are in the first level after one of the API directories,
'all_api_aliases' (show all other names, as with 'all', for objects in
'in_api')
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('package_name', type=str)
    parser.add_argument('--allow-non-api', action='store_true')
    parser.add_argument('--hide-instances', action='store_true')
    parser.add_argument('--show-modules', action='store_true')
    parser.add_argument('--runtype', help=runtype_help,
                        choices=['first', 'all', 'api_names', 'in_api',
                                 'not_in_api', 'all_api_aliases'])
    parser.add_argument('--api-file', type=str,
                        help="file with preferred API paths")

    opts = parser.parse_args()

    api_dirs = []
    if opts.api_file:
        with open(opts.api_file, 'r') as api_file:
            api_dirs = api_file.read().splitlines()

    main_function = {
        None: lambda names: names,
        'first': first_appearance,
        'all': all_appearances,
        'api_names': functools.partial(api_names, api_directories=api_dirs),
        'in_api': functools.partial(filter_by_in_api,
                                    api_directories=api_dirs,
                                    in_api=True),
        'not_in_api': functools.partial(filter_by_in_api,
                                        api_directories=api_dirs,
                                        in_api=False),
        'all_api_aliases': functools.partial(all_api_aliases,
                                             api_directories=api_dirs)
    }[opts.runtype]

    print_columns = {
        None: 1,
        'first': 1,
        'all': 2,
        'api_names': 1,
        'in_api': 1,
        'not_in_api': 1,
        'all_api_aliases': 2
    }[opts.runtype]

    names = find_all_names(opts.package_name)
    if not opts.allow_non_api:
        names = select_api_valid_names(names, opts.package_name)

    if opts.hide_instances:
        names = select_non_instance(names)

    if not opts.show_modules:
        names = select_non_module(names)

    names = main_function(names)

    for name, locations in names.items():
        if print_columns == 1:
            print(name)
        elif print_columns == 2:
            print(name, locations)


