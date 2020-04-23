import os

import requests
import json
import time
from xml.etree import ElementTree
from dateutil import parser

from .parser_config import PUBMED_API_KEY

from biothings.utils.common import open_anyfile
from biothings import config
logging = config.logger

def getPubMedDataFor(pmid):
    api_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&rettype=abstract&api_key="+str(PUBMED_API_KEY)+"&id="
    url = api_url+str(pmid)
    r = requests.get(url)

    publication={
        "@context": {
            "schema":"http://schema.org/",
            "outbreak":"https://discovery.biothings.io/view/outbreak/",
        },
        "@type":'Publication',
        "keywords":[],
        "author":[],
        "funding":[],
        "publicationType":[],
        "isBasedOn":[]
    }

    try:
        root = ElementTree.fromstring(r.content)
        has_children = list(root.iter())
        if has_children:
            #Single Value
            publication["_id"] = f"pmid{pmid}"
            publication["curatedBy"] = {"@type":"schema:WebSite",
                                        "name":"litcovid",
                                        "url": f"https://www.ncbi.nlm.nih.gov/research/coronavirus/publication/{pmid}"}
            publication["name"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/ArticleTitle'), 'text',None)
            publication["identifier"] = getattr(root.find('PubmedArticle/MedlineCitation/PMID'), 'text',None)
            publication["pmid"] = getattr(root.find('PubmedArticle/MedlineCitation/PMID'), 'text',None)
            publication["abstract"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Abstract/AbstractText'), 'text',None)
            publication["license"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Abstract/CopyrightInformation'), 'text',None)
            publication["journalName"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/Title'), 'text',None)
            publication["journalAbbreviation"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/ISOAbbreviation'), 'text',None)
            publication["issueNumber"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/ISSN'), 'text',None)
            #With fallback
            publication["doi"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/ELocationID'), 'text',None)
            if not publication.get('doi'):
                ids = root.findall('PubmedArticle/PubmedData/ArticleIdList/ArticleId')
                for item in ids:
                    if item.attrib.get('IdType') == 'doi':
                        publication["doi"] = getattr(item, 'text',None)
            else:
                doi = publication["doi"]
                publication["url"]= f"https://www.doi.org/{doi}"
            #Authors
            auths = root.find('PubmedArticle/MedlineCitation/Article/AuthorList')
            if auths is not None:
                for auth in list(auths):
                    author ={"@type":"outbreak:Person"}
                    auth_details = auth.iter()
                    for det in auth_details:
                        if det.tag == "ForeName":
                            author["givenName"] = getattr(det, 'text',None)
                        if det.tag == "LastName":
                            author["familyName"] = getattr(det, 'text',None)
                        if author.get('givenName') and author.get('familyName'):
                            author["name"] = author.get('givenName')+" "+author.get('familyName')
                        list_aff = det.findall('AffiliationInfo')
                        for aff in list_aff:
                            organization ={"@type":"outbreak:Organization"}
                            author["affiliation"] =[]
                            organization["name"] = getattr(aff.find('Affiliation'), 'text',None)
                            if organization["name"] is not None:
                                author["affiliation"].append(organization)
                    #cleanup author
                    for key in author:
                        if author[key] is None: del author[key]
                publication["author"].append(author)

            #Funding
            grants = root.findall('PubmedArticle/MedlineCitation/Article/GrantList/Grant')
            for grant in grants:
                obj ={"@type":"outbreak:MonetaryGrant",
                      "funder":[]}
                grant_details = grant.iter()
                for det in grant_details:
                    if det.tag == "GrantID":
                        obj["identifier"] = getattr(det, 'text',None)
                    if det.tag == "Agency":
                        org ={"@type":"outbreak:Organization"}
                        org["name"] = getattr(det, 'text',None)
                        obj["funder"].append(org)
                #cleanup grant
                for key in obj:
                    if obj[key] is None: del obj[key]
                publication["funding"].append(obj)

            #Citations
            citations = root.findall('PubmedArticle/PubmedData/ReferenceList/Reference')
            for item in citations:
                details = item.iter()
                for cit in details:
                    if cit.tag == "Citation":
                        publication["isBasedOn"].append(cit.text)
            #Pub Date
            mm = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Month'), 'text',None)
            yy = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Year'), 'text',None)
            dd = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Day'), 'text',None)
            dp = ''
            try:
                dp = mm+"/"+dd+"/"+yy
            except:
                pass
            finally:
                if dp:
                    d = parser.parse(dp)
                    dp = d.strftime("%Y-%m-%d")
                    publication["datePublished"] = dp
            #Date Modified
            dates = root.findall('PubmedArticle/PubmedData/History/PubMedPubDate')
            for date in dates:
                if date.attrib.get('PubStatus') == 'revised':
                    for child in date.iter():
                        if child.tag == "Month": mm = getattr(child, 'text',None)
                        if child.tag == "Day": dd = getattr(child, 'text',None)
                        if child.tag == "Year": yy = getattr(child, 'text',None)
                        d_mod =''
                        try:
                            d_mod = mm+"/"+dd+"/"+yy
                        except:
                            d_mod = None
                        finally:
                            if d_mod:
                                d = parser.parse(d_mod)
                                d_mod = d.strftime("%Y-%m-%d")
                                publication["dateModified"] = d_mod

            #publication Types
            pt = root.findall('PubmedArticle/MedlineCitation/Article/PublicationTypeList/PublicationType')
            for t in pt:
                publication["publicationType"].append(t.text)
            #Keywords
            ks = root.findall('PubmedArticle/MedlineCitation/KeywordList/Keyword')
            for x in ks:
                publication["keywords"].append(x.text)
            #cleanup doc of empty vals
            for key in list(publication):
                if not publication.get(key):del publication[key]
            #final doc
            return publication
        else:
            logging.warning("No information for PubMed ID '%s'", pmid)
    except ElementTree.ParseError:
        logging.warning("Can't parse XML for PubMed ID '%s'", pmid)
        pass

def load_annotations(data_folder):

    infile = os.path.join(data_folder,"litcovid2BioCJSON.gz")
    assert os.path.exists(infile)

    with open_anyfile(infile,mode='r') as file:
        a = file.read()
        data_list = json.loads(a)
        # First item is a comment by provider
        data = data_list[1]

    for i,rec in enumerate(data,start=1):
        # NCBI eutils API limits requests to 10/sec
        if i%10 ==0:
            time.sleep(2)
        yield getPubMedDataFor(rec["pmid"])
