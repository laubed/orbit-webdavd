import os, functools

class BaseOperator(object):
    def begin(self, user):
        raise NotImplementedError()

    def end(self, user):
        raise NotImplementedError()


class NoneOperator(object):
    def begin(self, user):
        pass

    def end(self, user):
        pass


class UnixOperator(BaseOperator):
    def __init__(self, umask):
        import pwd
        self.pwd = pwd
        self.counter = 0
        self.umask = umask

    @functools.lru_cache(maxsize=512)
    def get_groups(self, username):
        os.initgroups(username, self.pwd.getpwnam(username)[3])
        g = os.getgroups()
        os.initgroups("root", 0)

        return g

    @functools.lru_cache(maxsize=512)
    def get_pwnam(self, username):
        return self.pwd.getpwnam(username)

    def begin(self, user):
        if self.counter > 1024:
            self.get_groups.cache_clear()
            self.counter = 0

        os.setgroups(self.get_groups(user))
        os.setegid(self.get_pwnam(user)[3])
        os.seteuid(self.get_pwnam(user)[2])
        os.umask(self.umask)

    def end(self, user):
        os.umask(0o022)
        os.seteuid(0)
        os.setegid(0)
        os.setgroups(self.get_groups("root"))

    def get_home(self, user):
        return self.get_pwnam(user)[5]