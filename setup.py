from setuptools import setup, find_packages

setup(
    name="c-four",
    version='1.0',
    description='コミットの自動分割ツール',
    author='Aoi Koga',
    author_email='bluehawaiiouhu@gmail.com',
    url='https://github.com/juniortwelve/c-four',
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "c-four=mypkg.script:main",
        ]
    },
    install_requires=[
        'GitPython',
        'prompt-toolkit',
        'SQLAlchemy',
    ]
)
