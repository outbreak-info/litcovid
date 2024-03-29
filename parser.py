import os
import json

import time
import datetime
from xml.etree import ElementTree
from dateutil import parser
from outbreak_parser_tools.addendum import Addendum

from .parser_config import PUBMED_API_KEY

from outbreak_parser_tools import safe_request as requests
from outbreak_parser_tools.logger import get_logger
logger = get_logger('litcovid')
from biothings.utils.common import open_anyfile

CACHE_FILE_PATH = '/data/outbreak/plugins/litcovid/litcovid_cache.p'

def getPubMedDataFor(pmid):
    api_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&rettype=abstract&api_key="
    url     = f"{api_url}{PUBMED_API_KEY}&id={pmid}"

    try:
        r = requests.get(url)
        content = r.content
        remove = [b'<b>', b'</b>', b'<i>', b'</i>']
        for tag in remove:
            content = content.replace(tag, b'')

        doc = parseXMLTree(content, pmid)
        if doc:
            return doc
    except IOError:
        logger.warning("Exceeded request for ID '%s'", pmid)
        raise

def parseXMLTree(res,pmid):
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
        root = ElementTree.fromstring(res)
        has_children = list(root.iter())
        if has_children:
            #Single Value
            publication["_id"] = f"pmid{pmid}"
            publication["curatedBy"] = {"@type":"schema:WebSite",
                                        "name":"litcovid",
                                        "curationDate": datetime.date.today().strftime("%Y-%m-%d"),
                                        "url": f"https://www.ncbi.nlm.nih.gov/research/coronavirus/publication/{pmid}"}
            publication["name"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/ArticleTitle'), 'text',None)
            if publication["name"] is None:
                vernacular_title = getattr(root.find('PubmedArticle/MedlineCitation/Article/VernacularTitle'), 'text',None)
                publication["name"] = vernacular_title
            publication["identifier"] = getattr(root.find('PubmedArticle/MedlineCitation/PMID'), 'text',None)
            publication["pmid"] = getattr(root.find('PubmedArticle/MedlineCitation/PMID'), 'text',None)
            #Abstract

            abs = root.findall('PubmedArticle/MedlineCitation/Article/Abstract/AbstractText')
            abs_str = ""
            for item in abs:
                if("Label" in item.keys()):
                    abs_str = abs_str + item.get("Label") + ": "
                try:
                    abs_str = abs_str + ''.join(item.itertext())
                except:
                    abs_str = abs_str + getattr(root.find('PubmedArticle/MedlineCitation/Article/Abstract/AbstractText'), 'text', None)
                abs_str = abs_str + "\n"
            publication["abstract"] = abs_str

            publication["license"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Abstract/CopyrightInformation'), 'text',None)
            publication["journalName"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/Title'), 'text',None)
            publication["volumeNumber"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/Volume'), 'text',None)
            publication["pagination"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/Pagination/MedlinePgn'), 'text',None)
            publication["journalAbbreviation"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/ISOAbbreviation'), 'text',None)
            publication["issueNumber"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/ISSN'), 'text',None)
            #With fallback

            try:
                ids = root.findall('PubmedArticle/PubmedData/ArticleIdList/ArticleId')
                for item in ids:
                    if item.attrib.get('IdType') == 'doi':
                        publication["doi"] = getattr(item, 'text',None)
            except:
                publication["doi"] = getattr(root.find('PubmedArticle/MedlineCitation/Article/ELocationID'), 'text',None)

            if publication.get('doi'):
                doi = publication["doi"]
                publication["url"]= f"https://www.doi.org/{doi}"
            else:
                publication["url"] = f"https://www.ncbi.nlm.nih.gov/research/coronavirus/publication/{pmid}"

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
            if citations:
                for item in citations:
                    details = item.iter()
                    citObj = {"@type":"Publication"}
                    for cit in details:
                        if cit.tag == "Citation":
                            citObj['citation']= cit.text
                        if cit.tag == "ArticleIdList":
                            cid = cit.find('ArticleId')
                            if cid.text:
                                citObj['identifier']= cid.text
                                if "10." in cid.text:
                                    citObj['doi']= cid.text
                                elif "/" in cid.text:
                                    pass
                                else:
                                    citObj['pmid']= cid.text
                    publication["isBasedOn"].append(citObj)
            else:
                del publication["isBasedOn"]
  
            #Corrections
            try:
                corrlist = parse_corrections(root)
            except:
                corrlist = []
            if len(corrlist) > 0:
                publication['correction'] = corrlist 

            #Pub Date
            mm = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Month'), 'text',None)
            yy = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Year'), 'text',None)
            dd = getattr(root.find('PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Day'), 'text',None)
            dp = ''
            try:
                dp = mm+"/"+dd+"/"+yy
            except:
                try:
                    #Article Date
                    mm = getattr(root.find('PubmedArticle/MedlineCitation/Article/ArticleDate/Month'), 'text',None)
                    yy = getattr(root.find('PubmedArticle/MedlineCitation/Article/ArticleDate/Year'), 'text',None)
                    dd = getattr(root.find('PubmedArticle/MedlineCitation/Article/ArticleDate/Day'), 'text',None)
                    dp = mm+"/"+dd+"/"+yy
                except:
                    pass
            finally:
                if dp:
                    try:
                        d = parser.parse(dp)
                        dp = d.strftime("%Y-%m-%d")
                        publication["datePublished"] = dp
                    except:
                        logger.warning("Publication date '%s' can't be parsed for PubMed ID '%s'", dp, pmid)
            #Date Modified
            try:
                #Date Revised
                mm = getattr(root.find('PubmedArticle/MedlineCitation/DateRevised/Month'), 'text',None)
                yy = getattr(root.find('PubmedArticle/MedlineCitation/DateRevised/Year'), 'text',None)
                dd = getattr(root.find('PubmedArticle/MedlineCitation/DateRevised/Day'), 'text',None)
                dm = mm+"/"+dd+"/"+yy
                d = parser.parse(dm)
                d_mod = d.strftime("%Y-%m-%d")
                publication["dateModified"] = d_mod
            except:
                pass
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
                                try:
                                    d = parser.parse(d_mod)
                                    d_mod = d.strftime("%Y-%m-%d")
                                    publication["dateModified"] = d_mod
                                except:
                                    logger.warning("Modified date '%s' can't be parsed for PubMed ID '%s'", d_mod, pmid)
                #DateCreated
                elif date.attrib.get('PubStatus') == 'pubmed':
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
                                try:
                                    d = parser.parse(d_mod)
                                    d_mod = d.strftime("%Y-%m-%d")
                                    publication["dateCreated"] = d_mod
                                except:
                                    logger.warning("Pubmed creation date '%s' can't be parsed for PubMed ID '%s'", d_mod, pmid)
            #Date Completed
            mm = getattr(root.find('PubmedArticle/MedlineCitation/DateCompleted/Month'), 'text',None)
            yy = getattr(root.find('PubmedArticle/MedlineCitation/DateCompleted/Year'), 'text',None)
            dd = getattr(root.find('PubmedArticle/MedlineCitation/DateCompleted/Day'), 'text',None)
            dc = ''
            try:
                dc = mm+"/"+dd+"/"+yy
            except:
                pass
            finally:
                if dc:
                    try:
                        d = parser.parse(dc)
                        dc = d.strftime("%Y-%m-%d")
                        publication["dateCompleted"] = dc
                    except:
                        logger.warning("Record completion date '%s' can't be parsed for PubMed ID '%s'", dc, pmid)
                        
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
            return False
            logger.warning("No information for PubMed ID '%s'", pmid)
    except ElementTree.ParseError:
        logger.warning("Can't parse XML for PubMed ID '%s'", pmid)
        pass

def parse_corrections(root):
    medline_corrections_dict = {"CommentIn":"comment in",
                                "CommentOn":"comment on",
                                "ErratumIn":"erratum in",
                                "ErratumFor":"erratum for",
                                "CorrectedAndRepublishedIn":"republished in",
                                "CorrectedAndRepublishedFrom":"republished from",
                                "DatasetDescribedIn":"dataset described in",
                                "DatasetUseReportedIn":"dataset use reported in",
                                "ExpressionOfConcernIn":"expression of concern in",
                                "ExpressionOfConcernFor":"expression of concern for",
                                "RepublishedIn":"republished in",
                                "RepublishedFrom":"republished from",
                                "RetractionIn":"retraction in",
                                "RetractionOf":"retraction of",
                                "UpdateIn":"update in",
                                "UpdateOf":"update of"}
    corrs = root.findall('PubmedArticle/MedlineCitation/CommentsCorrectionsList/CommentsCorrections')
    corrlist = []
    for eachcorr in corrs:
        reftype = eachcorr.get('RefType')
        refid = eachcorr.find('PMID').text
        corrdict = {'@type': 'Correction',
                    'identifier':'pmid'+refid,
                    'url':f"https://www.ncbi.nlm.nih.gov/research/coronavirus/publication/{refid}",
                    'pmid':refid}
        corrdict['correctionType']=medline_corrections_dict[reftype]
        corrlist.append(corrdict)
    return(corrlist)

def throttle(response, *args, **kwargs):
    if not getattr(response, 'from_cache', False):
        logger.info('sleeping')
        time.sleep(.2)
    return response

def get_annotations():
    res = requests.get('https://www.ncbi.nlm.nih.gov/research/coronavirus-api/export/tsv?')
    litcovid_data = res.text.split('\n')[34:]

    data = []
    for line in litcovid_data:
        if line.startswith('#') or line.startswith('p'):
            continue
        data.append(line.split('\t')[0])

    doc_id_set = set()
    given_up_ids = []
    data_length = len(data)

    try:
        previous_docs = pickle.load(open(CACHE_FILE_PATH, 'rb'))
        for doc in previous_docs:
            doc_id_set.add(doc['_id'])
            yield doc
        logger.info("Yielded {} documents from cache".format(len(doc_id_set)))
    except Exception:
        logger.warning("Couldn't find litcovid cache file.")
        pass

    for i, pmid in enumerate(data,start=1):
        # NCBI eutils API limits requests to 10/sec
        if i % 100 == 0:
            percent_complete = round(100 * (i / data_length), 3)
            logger.info("litcovid.parser.load_annotations progress {}, {}%".format(i, percent_complete))

        es_id = f"pmid{pmid}"
        if es_id in doc_id_set:
            continue

        try:
            doc = getPubMedDataFor(pmid)
        except IOError:
            given_up_ids.append(pmid)
            logger.warning(f"Giving up on {pmid}, given up on {len(given_up_ids)} docs")
            continue

        if doc:
            yield doc
        doc_id_set.add(es_id)

def load_annotations(data_folder):
    with open('/home/jmullen/litcovid/d.json') as data:
        pubs = [json.loads(i) for i in data]
    Addendum.biorxiv_corrector().update(pubs)
    Addendum.topic_adder().update(pubs)
    Addendum.altmetric_adder().update(pubs)
    yield from pubs
