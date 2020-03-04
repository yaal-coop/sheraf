try:  # pragma: no cover
    from tqdm import tqdm
except ImportError:  # pragma: no cover

    def tqdm(x, *args, **kwargs):
        return x
