from os import listdir
from os.path import isfile, join, isdir
from torch.utils.data import Dataset

from .ntut_sequence import NTUT_Sequence

class NTUT_Wrapper(Dataset):
    """A Wrapper for the MOT_Sequence class to return multiple sequences."""

    def __init__(self, split, dataloader):
        """Initliazes all subset of the dataset.

        Keyword arguments:
        split -- the split of the dataset to use
        dataloader -- args for the MOT_Sequence dataloader
        """
        dir = '/home/ntut-drone/NTUTAction/Image'

        test_sequences = [f for f in listdir(dir) if isdir(join(dir, f))]
        test_sequences = sorted(test_sequences)
        
        sequences = test_sequences

        self._data = []

        for s in sequences:
            self._data.append(NTUT_Sequence(seq_name=s, **dataloader))

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        return self._data[idx]
