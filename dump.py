import os

import biothings, config
biothings.config_for_app(config)
from config import DATA_ARCHIVE_ROOT

from biothings.utils.common import uncompressall

import biothings.hub.dataload.dumper


class LitCovidDumper(biothings.hub.dataload.dumper.LastModifiedHTTPDumper):

    SRC_NAME = "litcovid"
    # override in subclass accordingly
    SRC_ROOT_FOLDER = os.path.join(DATA_ARCHIVE_ROOT, SRC_NAME)

    SCHEDULE = None  # crontab format schedule, if None, won't be scheduled
    # LitCovid will update docs daily on a schedule TODO

    SRC_URLS = [
        'https://ftp.ncbi.nlm.nih.gov/pub/lu/LitCovid/litcovid2BioCJSON.gz'
    ]
