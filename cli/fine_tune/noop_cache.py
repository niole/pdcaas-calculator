class NoopCache:
    def __init__(self, data = []):
        pass

    def add(self, d):
        pass

    def contains(self, d):
        return False

    def backup(self):
        pass

    def maybe_backup(self):
        pass
