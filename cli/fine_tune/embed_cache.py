import traceback
from numpyencoder import NumpyEncoder
from defaultModel import model
from sentence_transformers import util
import numpy as np
import json

"""
a vector embedding cache backed by a list

data - the data to initialize the cache with
outpath - optional, a path to save the serialized cache to when it's backed up
should_hydrate - optional, whether or not to hydrate the cache from the backup file
backup_chunk_size - optional, every time this much data is saved, the cache will be backed up, defaults to 100
"""
class EmbedArrayCache:
    def __init__(self, data = [], outpath = None, should_hydrate = False, backup_chunk_size = 100):
        self.data = data
        self.outpath = outpath
        self.backup_chunk_size = backup_chunk_size

        if should_hydrate:
            self._hydrate()

    def add(self, d):
        try:
            self.data.append(model.encode(d))
        except Exception as e:
            traceback.print_exc()
            print(f"There was an error while adding item to cache: {e}")

    def contains(self, d):
        try:
            embed_d = model.encode(d)

            for previous_d in self.data:
                similarity = util.pytorch_cos_sim(embed_d, previous_d).item()
                if similarity >= 0.5:
                    return True
        except Exception as e:
            traceback.print_exc()
            print(f"There was an error while determining set membership: {e}")

        return False

    def maybe_backup(self):
        if len(self.data) % self.backup_chunk_size == 0:
            self.backup()

    def backup(self):
        try:
            if self.outpath is not None:
                with open(self.outpath, 'w') as file:
                    file.write(json.dumps(self.data, cls=NumpyEncoder))
        except Exception as e:
            traceback.print_exc()
            print(f"Failed backup cache: {e}")

    def _hydrate(self):
        """
        try to read from outpath
        """
        try:
            with open(self.outpath, 'r') as file:
                self.data = [np.array(d) for d in json.loads(file.read())]
        except Exception as e:
            traceback.print_exc()
            print(f"There was an error while hydrating EmbedArrayCache from file: {e}")
