from setuptools import setup, find_packages

with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()

console_scripts = [
    'auto_split_commits=auto_split_commits.script:main',
]

setup(
    name="auto_split_commits",
    version='1.0',
    description='コミットの自動分割ツール',
    author='Aoi Koga',
    author_email='bluehawaiiouhu@gmail.com',
    url='https://github.com/juniortwelve/auto_split_commits',
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "auto_split_commits=mypkg.script:main",
        ]
    },
)