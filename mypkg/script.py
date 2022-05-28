from mypkg import operate_git
import os
from mypkg.db_settings import Base, engine
from mypkg.operate_json import make_single_unit_json, make_file_unit_json, construct_data_from_json, set_related_chunks_for_default_mode, get_related_chunks, convert_external_json_to_internal
from mypkg.operate_prompt import run_prompt
import json
import click
import configparser
import subprocess
from subprocess import PIPE
import datetime

@click.command()
@click.option('--all', '-a', 'is_all', is_flag=True, help="Don't perform initial split")
@click.option('--file', '-f', 'is_file', is_flag=True, help="Performs initial split by file.")
@click.option('--path', '-p', 'json_path', type=click.Path(exists=True), help="Performs initial split by specified json file.")
@click.option('--config', '-c', 'config', help="Performs initial split by stdin")
def main(is_all, is_file, json_path, config):
    path = os.getcwd()
    repo = operate_git.get_repo(path)
    diffs = operate_git.get_diffs(repo)
    Base.metadata.create_all(engine)
    
    if is_all:
        initial_split = make_single_unit_json(diffs)
        set_related_chunks_for_default_mode(initial_split)
    elif is_file:
        initial_split = make_file_unit_json(diffs)
        set_related_chunks_for_default_mode(initial_split)
    elif json_path:
        with open(json_path, 'r') as f:
            initial_split = json.load(f)
    elif config:
        initial_split = convert_external_json_to_internal(_load_json_from_config(config), diffs)
    else:
        initial_split = make_file_unit_json(diffs)
        set_related_chunks_for_default_mode(initial_split)

    log_path = 'log/' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')
    # os.mkdir(log_path)
    # with open(log_path + '/input.json', 'w') as f:
    #     json.dump(initial_split, f, indent=4)
    construct_data_from_json(initial_split)
    run_prompt(repo, log_path)
    
def _load_json_from_config(config):
    conf = configparser.ConfigParser()
    conf.read(os.environ['C_FOUR_CONFIG_PATH'])
    section = conf[config]
    cwd = os.getcwd()
    path = section['path']
    os.chdir(path)
    cmd = section['cmd'].split()
    cmd.append(cwd)
    proc = subprocess.run(cmd, shell=False, stdout=PIPE, stderr=PIPE, text=True)
    stdout = proc.stdout
    index = stdout.find('output_for_c-four')
    index += len('output_for_c-four')
    jl = json.loads(stdout[index:])
    return jl
    
if __name__ == '__main__':
    main()
