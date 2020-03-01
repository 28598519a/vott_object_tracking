from.ntut_wrapper import NTUT_Wrapper

_sets = {}

# Fill all available datasets, change here to modify / add new datasets.
for split in ['NTUT']:
    name = 'NTUT'
    _sets[name] = (lambda *args, split=split: NTUT_Wrapper(split, *args))

class Datasets(object):
    """A central class to manage the individual dataset loaders.

    This class contains the datasets. Once initialized the individual parts (e.g. sequences)
    can be accessed.
    """

    def __init__(self, dataset, *args):
        """Initialize the corresponding dataloader.

        Keyword arguments:
        dataset --  the name of the dataset
        args -- arguments used to call the dataloader
        """
        assert dataset in _sets, "[!] Dataset not found: {}".format(dataset)

        if len(args) == 0:
            args = [{}]

        self._data = _sets[dataset](*args)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        return self._data[idx]
