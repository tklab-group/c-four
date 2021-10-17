from mypkg import gitpython

def main():
    repo = gitpython.get_repo()
    print(repo.untracked_files)

if __name__ == '__main__':
    main()
