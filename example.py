import git
import gitmap
import time


class MyGitMap(gitmap.GitMap):
    def blob_map(self, data_stream, mode, path):
        # keep README and LICENSE
        if path in ['README.md', 'LICENSE.txt']:
            return data_stream.read(), mode, path
        # flatten python dir
        if path.startswith('python/'):
            return data_stream.read(), mode, path[len('python/'):]
        # delete other files
        else:
            return None

    def commit_add(self, old_commit):
        # add .gitignore
        return [
            (b'__pycache__\njittor.egg-info\n', 0o100644, '.gitignore'),
        ]

    def commit_map(self, old_commit, message, author, authored_date, author_tz_offset, committer, committed_date, committer_tz_offset):
        # keep author, update committer
        committer = git.Actor('The committer', 'committer@example.com')
        committed_date = time.time()
        return message, author, authored_date, author_tz_offset, committer, committed_date, committer_tz_offset

    def progress(self, old_commit, new_commit):
        # logging
        print('committed', old_commit, '=>', new_commit)

    remove_empty_commits = True


if __name__ == '__main__':
    # set source git repository
    url = 'https://github.com/Jittor/jittor.git'
    try:
        repo = git.Repo('../jittor')
    except git.exc.NoSuchPathError:
        print('cloning', url)
        repo = git.Repo.clone_from(url, '../jittor', branch='master')
    if 'origin' not in repo.remotes:
        repo.create_remote('origin', url=url)
    for branch in ['master', 'cjld']:
        if branch not in repo.heads:
            repo.remotes.origin.fetch()
        repo.create_head(branch, repo.refs['origin/{:s}'.format(branch)])

    # map source repo to destination repo
    MyGitMap().run('../jittor', '../jittor-python-only')
