from pathlib import Path
from unittest import TestCase
import pandas as pd

from api.short_func import UUID4BasedURLShortener


class Shorten10kURLS(TestCase):

    def test_hash_collisions(self):
        df = pd.read_csv(Path(__file__).parent / "phishing_site_urls.csv")
        ndf = df.drop('Label', axis=1) #.head()
        print(ndf)
        ndf["hashCol"] = ndf.URL.apply(lambda x: UUID4BasedURLShortener.get_shorter_url_for(x))
        print(f"Total entries in hashCol: {len(ndf.hashCol)}")
        print(f"Of those, unique: {len(ndf.hashCol.unique())}")