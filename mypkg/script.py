from mypkg import operate_git
import os
from mypkg.db_settings import Base, engine
from mypkg.operate_json import make_single_unit_json, make_file_unit_json, construct_data_from_json, set_related_chunks_for_default_mode, get_related_chunks
from mypkg.operate_prompt import run_prompt
import json
import click

@click.command()
@click.option('--all', '-a', 'input_type', flag_value='all', help="Don't perform initial split")
@click.option('--file', '-f',  'input_type', flag_value='file', help="Performs initial split by file.")
@click.option('--input', '-i', 'input_type', help="Performs initial split by input json.")
def main(input_type):
    path = os.getcwd()
    repo = operate_git.get_repo(path)
    diffs = operate_git.get_diffs(repo)
    Base.metadata.create_all(engine)
    
    if input_type == 'file':
        initial_split = make_file_unit_json(diffs)
        set_related_chunks_for_default_mode(initial_split)
    elif input_type == 'input':
        with open('./json/sample.json', 'r') as f:
            initial_split = json.load(f)
    else:
        initial_split = make_single_unit_json(diffs)
        set_related_chunks_for_default_mode(initial_split)

    with open('./json/sample.json', 'w') as f:
        json.dump(initial_split, f, indent=4)
    construct_data_from_json(initial_split)
    
    run_prompt(repo)
        
if __name__ == '__main__':
    main()
