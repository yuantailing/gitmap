import git
import io
import time

from collections import defaultdict
from gitdb.base import IStream


class GitMap(object):
    def blob_map(self, data_stream, mode, path):
        return data_stream.read(), mode, path

    def commit_add(self, old_commit):
        return []

    def commit_map(self, old_commit, message, author, authored_date, author_tz_offset, committer, committed_date, committer_tz_offset):
        return message, author, authored_date, author_tz_offset, committer, committed_date, committer_tz_offset

    def progress(self, old_commit, new_commit):
        pass

    remove_empty_commits = False

    def run(self, src_path, dst_path):
        src = git.Repo(src_path)
        dst = git.Repo.init(dst_path)

        children = defaultdict(set) # binsha => set(binsha)
        threads = list() # [commit]
        depend = dict() # binsha => set(binsha)
        for head in src.heads:
            st = [head.commit]
            while st:
                commit = st.pop()
                if commit.binsha not in depend:
                    depend[commit.binsha] = {parent.binsha for parent in commit.parents}
                    if not commit.parents:
                        threads.append(commit)
                    for c in commit.parents:
                        if c.binsha not in children:
                            st.append(c)
                        children[c.binsha].add(commit)

        blob_map_cache = dict()
        commit_binsha_map = dict()
        while threads:
            commit = threads.pop()
            index = dst.index
            blobs = set()
            for item in commit.tree.traverse():
                key = item.binsha, item.mode, item.path
                if item.type == 'blob':
                    if key in blob_map_cache:
                        if blob_map_cache[key] is not None:
                            value = blob_map_cache[key]
                            blobs.add(value)
                    else:
                        res = self.blob_map(item.data_stream, item.mode, item.path)
                        if res is not None:
                            data, mode, path = res
                            istream = dst.odb.store(IStream('blob', len(data), io.BytesIO(data)))
                            value = blob_map_cache[key] = istream.binsha, mode, path
                            blobs.add(value)
                        else:
                            blob_map_cache[key] = None
            for data, mode, path in self.commit_add(commit):
                istream = dst.odb.store(IStream('blob', len(data), io.BytesIO(data)))
                blobs.add((istream.binsha, mode, path))

            old_blobs = {(blob[1].binsha, blob[1].mode, blob[1].path) for blob in index.iter_blobs()}
            to_remove = list(old_blobs - blobs)
            to_add = list(blobs - old_blobs)
            if to_remove:
                for i in range(0, len(to_remove), 128):
                    index.remove([git.Blob(dst, *t) for t in to_remove[i:i + 128]])
            if to_add:
                for i in range(0, len(to_add), 128):
                    index.add([git.Blob(dst, *t) for t in to_add[i:i + 128]])

            parent_commits=[commit_binsha_map[parent.binsha] for parent in commit.parents]
            message, author, authored_date, author_tz_offset, committer, committed_date, committer_tz_offset = self.commit_map(commit, commit.message, commit.author, commit.authored_date, commit.author_tz_offset, commit.committer, commit.committed_date, commit.committer_tz_offset)
            author_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(authored_date)) + ' ' + git.objects.util.altz_to_utctz_str(author_tz_offset)
            commit_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(committed_date)) + ' ' + git.objects.util.altz_to_utctz_str(committer_tz_offset)

            skip_flag = False
            if self.remove_empty_commits:
                for parent in parent_commits:
                    if not index.diff(parent):
                        dst_commit = parent
                        skip_flag = True
                        break
            if not skip_flag:
                dst_commit = index.commit(message, parent_commits=parent_commits, author=author, committer=committer, author_date=author_date, commit_date=commit_date)
            commit_binsha_map[commit.binsha] = dst_commit
            self.progress(commit, dst_commit)

            for child in children[commit.binsha]:
                depend[child.binsha].remove(commit.binsha)
                if not depend[child.binsha]:
                    threads.append(child)

        for head in src.heads:
            if not head.name in dst.heads:
                dst.create_head(head.name)
            dst.heads[head.name].commit = commit_binsha_map[head.commit.binsha]
