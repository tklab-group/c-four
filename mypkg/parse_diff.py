import re
from argparse import ArgumentParser
import sys

def main():
    added_chunks, removed_chunks = parse_diff(sys.stdin.readlines())
    print("added_chunks: {0}".format(added_chunks))
    print("removed_chunks: {0}".format(removed_chunks))

def parse_diff(diff_str):
    print("diff_str: {0}".format(diff_str))
    # lines = diff_str.split('\n')
    lines = diff_str[4:]
    line_iterator = iter(lines)
    added_chunks = []
    removed_chunks = []
    regexp = re.compile(',| ')

    try:
        line = next(line_iterator)
        while True:
            if line.startswith('@@'):
                line_id_strs = [token[1:] for token in regexp.split(line.split('@@')[1]) if token.startswith(('+', '-'))]
                removed_line_id = int(line_id_strs[0])
                added_line_id = int(line_id_strs[1])
                line = next(line_iterator)
            elif line.startswith('+'):
                chunk_start = added_line_id
                try:
                    while line.startswith('+'):
                        line = next(line_iterator)
                        added_line_id += 1
                except StopIteration:
                    added_chunks.append((chunk_start, added_line_id))
                    break
                added_chunks.append((chunk_start, added_line_id - 1))
            elif line.startswith('-'):
                chunk_start = removed_line_id
                try:
                    while line.startswith('-'):
                        line = next(line_iterator)
                        removed_line_id += 1
                except StopIteration:
                    removed_chunks.append((chunk_start, removed_line_id))
                    break
                removed_chunks.append((chunk_start, removed_line_id - 1))
            else:
                line = next(line_iterator)
                added_line_id += 1
                removed_line_id += 1

    except StopIteration:
        pass

    return (added_chunks, removed_chunks)


if __name__ == '__main__':
    main()
