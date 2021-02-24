import os

import biothings, config
biothings.config_for_app(config)
from config import DATA_ARCHIVE_ROOT

import biothings.hub.dataload.dumper


class LitCovidDumper(biothings.hub.dataload.dumper.LastModifiedHTTPDumper):

    SRC_NAME = "litcovid"
    # override in subclass accordingly
    SRC_ROOT_FOLDER = os.path.join(DATA_ARCHIVE_ROOT, SRC_NAME)

    # crontab format schedule, if None, won't be scheduled
    SCHEDULE = "30 3 * * *" # daily at 10:30UTC/3:30PT    

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

    SRC_URLS = [
            'https://www.ncbi.nlm.nih.gov/research/coronavirus-api/export/tsv?'
    ]
