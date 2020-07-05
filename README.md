# gitmap
Map git commits to new commits, preserving history.

## Usage

1. Install dependencies, `pip install -r requirements.txt`. (python2 is currently not supported.)
1. Inherit the class `gitmap.GitMap`, and override `blob_map` and `commit_map`. The `blob_map` function maps a source path to a destination path, etc. The `commit_map` function maps a commit message to a new message, etc.
1. Call `run(src_repo_path, dst_repo_path)`. All heads will be mapped.
1. Set `remove_empty_commits` to `True` if you want to remove empty commits. (A non-empty commit may be mapped to an empty commit, depending on your map function.)
1. Moreover, you can add blobs to each commit by overriding `commit_add`, and print progress by override `progress`. The `commit_add` returns a list of blobs, each of which is in the same scheme as `blob_map`. `progress` is called after each commit is mapped.

## Example

See [example.py](example.py).

```python3
class MyGitMap(gitmap.GitMap):
    def blob_map(self, data_stream, mode, path):
        # keep README and LICENSE
        if path in ['README.md', 'LICENSE.txt']:
            return data_stream.read(), mode, path
        # flatten python dir
        if path.startswith('python/'):
            return data_stream.read(), mode, path.lstrip('python/')
        # delete other files
        else:
            return None

    def commit_add(self, old_commit):
        # add .gitignore
        return [
            (b'__pycache__\njittor.egg-info\n', 0o100644, '.gitignore'),
        ]

    def commit_map(self, old_commit, message, author, committer, author_date, commit_date):
        # keep author, update committer
        committer = git.Actor('Tailing Yuan', 'yuantailing@gmail.com')
        commit_date = time.time()
        return message, author, committer, author_date, commit_date

    def progress(self, old_commit, new_commit):
        # logging
        print('committed', old_commit, '=>', new_commit)

    remove_empty_commits = True

MyGitMap().run('../jittor', '../jittor-python-only')
```
