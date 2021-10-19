import re
from argparse import ArgumentParser
import sys

def parse_diff(lines):
    lines = lines.split('\n')
    added_chunks, removed_chunks = [], []
    added_line_ids, removed_line_ids = [], []
    added_lines, removed_lines = [], []
    regexp = re.compile(',| ')
    
    first_line = lines.pop(0)
    if first_line.startswith('@@'):
        line_id_strs = [token[1:] for token in regexp.split(first_line.split('@@')[1]) if token.startswith(('+', '-'))]
        removed_line_id = int(line_id_strs[0])
        added_line_id = int(line_id_strs[1])
    else:
        return

    for line in lines:
        if line.startswith('+'):
            added_line_ids.append(added_line_id)
            added_line_id += 1
        elif line.startswith('-'):
            removed_line_ids.append(removed_line_id)
            removed_line_id += 1
        else:
            added_line_id += 1
            removed_line_id += 1

    print(added_line_ids)
    print(removed_line_ids)
    
    start_id = added_line_ids.pop(0)
    prev_id = end_id = start_id
    added_line_ids.append(-1)
    for id in added_line_ids:
        if id == prev_id + 1:
            end_id = id
        else:
            added_chunks.append((start_id, end_id))
            start_id = end_id = id
        prev_id = id

    start_id = removed_line_ids.pop(0)
    prev_id = end_id = start_id
    removed_line_ids.append(-1)
    for id in removed_line_ids:
        if id == prev_id + 1:
            end_id = id
        else:
            removed_chunks.append((start_id, end_id))
            start_id = end_id = id
        prev_id = id

    return (added_chunks, removed_chunks)


