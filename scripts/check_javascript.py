#!/usr/bin/env python3
"""Check every first-party browser/server JS file, including the generated Worker."""
import pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
for folder in ['public','server','workers']:
 for file in sorted((root/folder).glob('*.js')):subprocess.run(['node','--check',str(file)],check=True)
print('All browser and server JavaScript syntax checks passed.')
