import os
import datetime

import biothings, config
biothings.config_for_app(config)
from config import DATA_ARCHIVE_ROOT

import biothings.hub.dataload.dumper

class LitCovidDumper(biothings.hub.dataload.dumper.DummyDumper):
    SRC_NAME = "litcovid"
    SRC_ROOT_FOLDER = os.path.join(DATA_ARCHIVE_ROOT, SRC_NAME)

    SCHEDULE = "30 11 * * *"

    __metadata__ = {
        "src_meta": {
            "author":{
                "name": "Marco Cano",
                "url": "https://github.com/marcodarko"
            },
            "code":{
                "branch": "master",
                "repo": "https://github.com/outbreak-info/litcovid.git"
            },
            "url": "https://www.ncbi.nlm.nih.gov/research/coronavirus/ ",
            "license": "https://www.ncbi.nlm.nih.gov/home/about/policies/"
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_release()

    def set_release(self):
        mtime = os.path.getmtime('/home/jmullen/litcovid/d.json')
        release_time = datetime.datetime.fromtimestamp(mtime)
        self.release = release_time.strftime('%Y-%m-%d-%H:%M')
