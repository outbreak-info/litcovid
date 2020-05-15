import os
import biothings.hub.dataload.uploader

import biothings
import config
biothings.config_for_app(config)


# when code is exported, import becomes relative
try:
    from litcovid.parser import load_annotations as parser_func
except ImportError:
    from .parser import load_annotations as parser_func


class LitCovidUploader(biothings.hub.dataload.uploader.BaseSourceUploader):

    name = "litcovid"
    __metadata__ = {
        "src_meta": {
            "author":{
                "name": "Marco Cano",
                "url": "https://github.com/marcodarko"
            },
            "code":{
                "branch": "master",
                "repo": "https://github.com/marcodarko/litcovid.git"
            },
            "url": "https://www.ncbi.nlm.nih.gov/research/coronavirus/ ",
            "license": "https://www.ncbi.nlm.nih.gov/home/about/policies/"
        }
    }
    idconverter = None
    storage_class = biothings.hub.dataload.storage.BasicStorage

    def load_data(self, data_folder):
        self.logger.info("Load data from directory: '%s'" % data_folder)
        return parser_func(data_folder)

    def getMappingFile():
        r = requests.get('https://raw.githubusercontent.com/SuLab/outbreak.info-resources/master/outbreak_resources_es_mapping.json').text
        return r

    @classmethod
    def get_mapping(klass):
        return {
            'fields': {
                'type': 'text'
            },
            'abstract': {
                'type': 'text'
            },
            '@type': {
                'type': 'text'
            },
            'pmid': {
                'type': 'integer'
            },
            'author': {
                'properties': {
                    'name': {
                        'type': 'text'
                    },
                    'givenName': {
                        'type': 'text'
                    },
                    'familyName': {
                        'type': 'text'
                    },
                    'affiliation': {
                        'properties': {
                            'name': {
                                'type': 'text'
                            }
                        }
                    }
                }
            },
            "isBasedOn": {
                "properties": {
                    "@type": {
                        "normalizer": "keyword_lowercase_normalizer",
                        "type": "keyword"
                    },
                    "identifier": {
                        "type": "text"
                    },
                    "name": {
                        "type": "text"
                    },
                    "description": {
                        "type": "text"
                    },
                    "url": {
                        "type": "text"
                    },
                    "datePublished": {
                        "type": "text"
                    }
                }
            },
            "relatedTo": {
                "properties": {
                    "@type": {
                        "normalizer": "keyword_lowercase_normalizer",
                        "type": "keyword"
                    },
                    "identifier": {
                        "type": "text"
                    },
                    "pmid": {
                        "type": "text"
                    },
                    "url": {
                        "type": "text"
                    },
                    "citation": {
                        "type": "text"
                    }
                }
            },
            'funding': {
                'properties': {
                    'funder': {
                        'properties': {
                            'name': {
                                'type': 'text'
                            }
                        }
                    },
                    'identifier': {
                        'type': 'text'
                    }
                }
            },
            'license': {
                'type': 'text'
            },
            'keywords': {
                'normalizer': 'keyword_lowercase_normalizer',
                'type': 'keyword',
                        'copy_to': ['all']
            },
            'publicationType': {
                'normalizer': 'keyword_lowercase_normalizer',
                'type': 'keyword',
                        'copy_to': ['all']
            },
            'name': {
                'type': 'text'
            },
            'journalName': {
                'type': 'text'
            },
            'identifier': {
                'type': 'text'
            },
            'doi': {
                'type': 'text'
            },
            'datePublished': {
                'type': 'keyword'
            },
            'dateModified': {
                'type': 'keyword'
            },
            'issueNumber': {
                'type': 'text'
            },
            'volumeNumber': {
                'type': 'text'
            },
            "curatedBy": {
                "properties": {
                    "@type": {
                        "normalizer": "keyword_lowercase_normalizer",
                        "type": "keyword"
                    },
                    "name": {
                        "type": "text"
                    },
                    "url": {
                        "type": "text"
                    },
                    "versionDate": {
                        "normalizer": "keyword_lowercase_normalizer",
                        "type": "keyword"
                    },
                }
            },
        }
