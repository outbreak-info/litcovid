import os

import biothings, config
biothings.config_for_app(config)
from config import DATA_ARCHIVE_ROOT

from biothings.utils.common import uncompressall

import biothings.hub.dataload.dumper


class LitCovidDumper(biothings.hub.dataload.dumper.LastModifiedHTTPDumper):

    SRC_NAME = "litcovid"

    UNCOMPRESS = True
    # override in subclass accordingly
    SRC_NAME = None
    SRC_ROOT_FOLDER = None  # source folder (without version/dates)

    # Should an upload be triggered after dump ?
    AUTO_UPLOAD = True

    # attribute used to generate data folder path suffix
    SUFFIX_ATTR = None

    # Max parallel downloads (None = no limit).
    MAX_PARALLEL_DUMP = None

    # waiting time between download (0.0 = no waiting)
    SLEEP_BETWEEN_DOWNLOAD = 0.5

    # keep all release (True) or keep only the latest ?
    ARCHIVE = True

    SCHEDULE = None  # crontab format schedule, if None, won't be scheduled
    # LitCovid will update docs daily on a schedule TODO

    SRC_URLS = [
        'https://ftp.ncbi.nlm.nih.gov/pub/lu/LitCovid/litcovid2BioCJSON.gz'
    ]

    def post_dump(self, *args, **kwargs):
        if self.__class__.UNCOMPRESS:
            self.logger.info("Uncompress all archive files in '%s'" %
                             self.new_data_folder)
            uncompressall(self.new_data_folder)
