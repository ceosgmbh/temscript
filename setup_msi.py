#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for MSI All-In-One_installer using cx_freeze (requires python 3.8, 32bit) with packages
  cx_freeze, numpy, aiohttp
Note: Interaction with StdScript.dll will only work for 32-bit Python versions!
"""
import importlib
import pkgutil
from glob import glob
import os
import sys
from datetime import date
from pprint import pprint
import platform

import distutils

from setuptools import Extension, find_packages
from setuptools.command.build_py import build_py
import cx_Freeze
from cx_Freeze import setup, Executable
from numpy.distutils.misc_util import get_numpy_include_dirs

numpy_include_dirs = get_numpy_include_dirs()


def make_extension(ext_file):
    """
    Converts a filename with path to a distutils Extension

    :param ext_file: relative filename
    """
    extName = ext_file[:-len('.py')].replace(os.path.sep, '.').strip('.')
    return Extension(extName, [ext_file])


def seperate_modules_and_inits(src_path, cython_packages):
    """
    Scan given packages for modules and __init__ files  and return them as
    seperate lists.

    :param src_path: parent dir of cythonPackages
    :param cython_packages: iterable of directory names
    """
    modules = []
    inits = [src_path]  # add root init
    for package in cython_packages:
        files = glob(os.path.join(package.replace('.', os.path.sep), '*.py'))
        for file in files:
            if file.endswith('__init__.py'):
                inits.append(file[:-len('.py')])
            elif file.endswith('__main__.py'):
                pass
            else:
                modules.append(file)
    return modules, inits


class QtBuild(build_py):
    def run(self):
        build_py.run(self)


def add_prefix(prefix, names, sep='.'):
    """
    Add prefix + separator to a list of names.

    :param prefix: a string to be added as prefix
    :param names: iterable of strings
    :param sep: the separator to use (default='.')
    """
    return [sep.join((prefix, name)) for name in names if name]

# List all dependencies that are explicitely excluded later if not listed here.
# Also list dependencies cx_freeze does not include automatically for various
# reasons.
default_includes = [
    'appdirs', 'asyncio', 'json', 'numpy', 'socket', 'aiohttp',
    ]

all_packages = find_packages('temscript') + \
               find_packages('_temscript_module')


default_packages = ['temscript', '_temscript_module']

# MSI definitions for Temscripting (Dummy) Server
msi_definitions = {
    'TemScriptServer': {
        'product_name': 'CEOS Temscripting Server',
        'description': 'Temscripting Server.',
        'upgrade_code': '{3F5EB5E6-6934-4465-88BE-F1CA715D4F8D}',
        'scripts': [
            {'script': 'scripts/start-remote-server-with-events.py',
             'shortcut_name': 'Temscripting Server for Titan 7',
             'base': None,  # show console
             'target_name': 'temscript_server.exe'},
            {'script': 'scripts/start-remote-server-with-events-legacy-titan.py',
             'shortcut_name': 'Temscripting Server for Titan 6',
             'base': None,  # show console
             'target_name': 'temscript_server_legacy_titan.exe'},
            {'script': 'scripts/start-remote-dummy-server-with-events.py',
             # 'shortcut_name': 'Temscripting Dummy Server for Titan 7.x',
             'base': None,  # show console
             'target_name': 'temscript_dummy_server.exe'},
            {'script': 'scripts/start-remote-dummy-server-with-events-legacy-titan.py',
             # 'shortcut_name': 'Temscripting Dummy Server for Titan 6.x',
             'base': None,  # show console
             'target_name': 'temscript_dummy_server_legacy_titan.exe'}],
#'includes': [],
        'includes': default_includes,
        'packages': default_packages,
        'data_files': [] },
        #common_data_files },
}


def main(product_name, description, upgrade_code, scripts, packages, includes,
         data_files=None):
    """
    This is is the magic setup routine that does everything.

    :param product_name: Name of the installer
    :param description: Product description for installer
    :param upgrade_code: unique code of product for MSI installer
    :param scripts: dict of the scripts to include, value is the name used for
                    shortcut ...
    :param packages: components of panta-rhei to include
    :param includes: external components to include
    :param data_files: If set contents will be added to 'data_files'
    """
    if not data_files:
        data_files = []

    use_cython = os.environ.get('TEMSCRIPT_SERVER_SETUP_USE_CYTHON', False)
    freeze = os.environ.get('TEMSCRIPT_SERVER_SETUP_FREEZE', False)
    msi_only = os.environ.get('TEMSCRIPT_SERVER_SETUP_MSI_ONLY', False)

    # Note: requires StdScript.dll version >= 7.10 in "temscript\_temscript_module"
    ext_modules = [
        Extension(
            '_temscript',
            sources=glob('_temscript_module/*.cpp'),
            include_dirs=numpy_include_dirs)]

    # license_folder = 'third-party-licenses'
    # license_files = [
        # os.path.join(license_folder, data_file_name)
        # for data_file_name in os.listdir(license_folder)
        # if os.path.isfile(os.path.join(license_folder, data_file_name))]
    # data_files.append((license_folder, license_files))

    setup_args = {
        'name': product_name,
        'description': description,
        'author': 'CEOS GmbH',
        'author_email': 'info@ceos-gmbh.de',
        'long_description': description,
        'version': '2.1.3', ###getVersion(debug=True).release,
        'url': 'http://ceos-gmbh.de/',
        'data_files': data_files,
        'cmdclass': {
            # 'build_ext': build_ext  # Cython
            'build_py': QtBuild},
        'package_data': {}}

    # check all data files exist
    data_file_names = [name for line in data_files for name in line[1]]
    # check all data_files exist
    for data_file_name in data_file_names:
        assert os.path.isfile(data_file_name), \
            'File "%s" is missing ' % data_file_name
    if freeze:
        # use the pyd files compiled in the previous run
        lib_dir = r'build\lib.%s-%s' % \
                  (distutils.util.get_platform(), sys.version[0:3])
        sys.path.insert(0, lib_dir)

        shortcuts = []
        setup_args['executables'] = []
        for script in scripts:
            script.setdefault('base', 'Win32GUI')
            script.setdefault('icon', 'ceoslogo.ico')
            setup_args['executables'].append(Executable(**script))
            # For some reason adding the parameter is not sufficient. Shortcuts
            # have to be added explicitly:
            if 'shortcut_name' in script:
                shortcuts.append(
                    ('Shortcut%s' % script['target_name'],  # Shortcut
                     'ProgramMenuFolder',  # Directory_
                     script['shortcut_name'],  # Name
                     'TARGETDIR',  # Component_
                     '[TARGETDIR]%s' % script['target_name'],  # Target
                     None,  # Arguments
                     None,  # Description
                     None,  # Hotkey
                     None,  # Icon
                     None,  # IconIndex
                     None,  # ShowCmd
                     'TARGETDIR'  # WkDir
                     ))

        setup_args['options'] = {
            'bdist_msi': {
                'upgrade_code': upgrade_code,
                'data': {"Shortcut": shortcuts}}}

        # cx_Freeze 6.1 defaults to per-user installation in %LOCALAPPDATA%
        # instead of a per-machine installation. The all_users option needs
        # to be set get the same behaviour.
        cx_version = [v for v in cx_Freeze.__version__.split('.')]
        if int(cx_version[0]) >= 6 and int(cx_version[1]) >= 1:
            setup_args['options']['bdist_msi']['all_users'] = True

        # Remove some potentially large or unwanted packages unless explicitly
        # added.
        potential_excludes = [
            'tkinter', 'setuptools', 'PySide', 'PyQt5', 'PySide2',
            # workaround for upper-/lowercase confusion on windows
            # see https://github.com/anthony-tuininga/cx_Freeze/issues/233
            'scipy.spatial.cKDTree',
            # unused parts of pywin32
            'adodbapi', 'isapi', 'pythonwin', 'win32', 'win32com',
            'win32comext',
            # if it exists comtypes will try to create files here, which will
            # fail
            'comtypes.gen',
            # Some of these are typically found on existing installation,
            # blacklisting them to avoid accidental inclusion.
            'astroid', 'attrs', 'Automat', 'boltons', 'colorama',
            'decorator', 'dodgy', 'funcsigs', 'hyperlink', 'isort',
            'jsonrpcserver', 'jsonschema', 'lazy_object_proxy', 'mccabe',
            'msgpack', 'msgpack_numpy', 'msgpack_python', 'nose', 'olefile',
            'pep8-naming', 'prospector', 'pycodestyle', 'pydocstyle',
            'pyflakes', 'pylint', 'pylint_celery', 'pylint_django',
            'pylint_flask', 'pylint_plugin_utils', 'Pyro4', 'qimage2ndarray',
            'qt4reactor', 'reloader', 'requirements-detector', 'serpent',
            'setoptconf', 'snowballstemmer', 'typed-ast', 'virtualenv', 'wrapt'

            ]
        excludes = [exclude
                    for exclude in potential_excludes
                    if exclude not in includes]

        # Exclude all compenents of panta-rhei not explicitly added.
        excludes += [exclude
                     for exclude in all_packages
                     if exclude not in packages]

        # set bdist_exe options
        if msi_only:
            external_packages = []
            # remove unnecessary packages
            binary_modules = {
                'cv2', 'scipy', 'PyQt5', 'PIL', 'PIL.ImageDraw',
                'zope.interface', 'matplotlib',
                'pyfftw', 'pywt', 'tifffile'}
            exe_includes = list(set(includes) - binary_modules)
            excludes += list(binary_modules)
        else:
            external_packages = packages
            # ensure everything is in completely in place
            exe_includes = includes + packages
            # TODO: remove unnecessary packages
            for externalPackage in ['asyncio', 'scipy', 'numpy', 'zmq', 'matplotlib']:
                if externalPackage in includes:
                    external_packages.append(externalPackage)

        setup_args['options']['build_exe'] = {
            'excludes': excludes,
            'includes': exe_includes,
            'packages': external_packages,
            'silent': True,
            'include_msvcr': True}
    elif use_cython:
        cython_packages = set(packages)
        non_cython_packages = []

        # they cause compiler errors
        non_compilable = []
        for non_cython in non_compilable:
            if non_cython in packages:
                cython_packages.remove(non_cython)
                non_cython_packages.append(non_cython)
        modules, inits = seperate_modules_and_inits(
            'panta_rhei', cython_packages)

        setup_args['ext_modules'] = ext_modules + \
            [make_extension(extFile) for extFile in modules]
        setup_args['py_modules'] = inits
        setup_args['packages'] = non_cython_packages
    else:
        setup_args['ext_modules'] = ext_modules
        setup_args['packages'] = packages

    pprint(setup_args)
    setup(**setup_args)


if __name__ == "__main__":
    target_msi = os.environ.get('TEMSCRIPT_SERVER_SETUP_PACKAGE', None)

    if target_msi in msi_definitions:
        params = msi_definitions[target_msi]

        main(**params)
    else:
        if target_msi:
            print('Unknown target "%s"' % target_msi)
        print('\nKnown targets:')
        for name in sorted(msi_definitions):
            print('    %s' % name)
        sys.exit(-1)
