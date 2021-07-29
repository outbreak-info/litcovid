def get_corrections(general_path,identifier):
    preprintpath = os.path.join(general_path,'outbreak_preprint_matcher/results/update dumps/')
    litcovidpreprint = os.path.join(preprintpath,'litcovid_update_file.json')
    pmatch = None
    if 'pmid' in identifier:
        with open(litcovidpreprint,'rb') as inputfile:
            correctionsfile = json.load(inputfile)
            pmatchlist = [x for x in correctionsfile if x['_id']==identifier]
            if len(pmatchlist)>0:
                pmatch = pmatchlist[0]['correction'][0]
    else:
        preprintlitcovid = os.path.join(preprintpath,'preprint_update_file.json')
        with open(preprintlitcovid,'rb') as inputfile:
            correctionsfile = json.load(inputfile)
            pmatchlist = [x for x in correctionsfile if x['_id']==identifier]
            if len(pmatchlist)>0:
                pmatch = pmatchlist[0]['correction'][0]
    return(pmatch)

    
def get_topics(general_path,identifier):
    tmatch = None
    topicspath = os.path.join(general_path,'topic_classifier/results/')
    topicfile = os.path.join(topicspath,'topicCats.json')    
    with open(topicfile,'rb') as inputfile:
        topicsfile = json.load(inputfile)
        tmatchlist = [x for x in topicsfile if x['_id']==identifier]
        if len(matchlist)>0:
            rawmatch = tmatchlist[0]['topicCategory']
            tmatch = rawmatch.strip('[').strip(']').replace("'","").split(',')
    return(tmatch)


def get_altmetrics(general_path,identifier):
    amatch = None
    altmetricspath = os.path.join(general_path,'covid_altmetrics/results/')    
    altmetricsfile = os.path.join(altmetricspath,'altmetric_annotations.json')
    with open(altmetricsfile,'rb') as inputfile:
        altfile = json.load(inputfile)
        amatchlist = [x for x in altfile if x['_id']==identifier]
        if len(amatchlist)>0:
            amatch = amatchlist[0]['evaluations']
    return(amatch)


def getAdditionalInfo(doc,general_path):
    identifier = doc['_id']
    preprint_corrections = get_corrections(general_path,identifier)
    if preprint_corrections != None:
        try:
            corrlist = doc['correction']
            corrlist.append(preprint_corrections)
            doc['correction'] = corrlist
        except:
            doc['correction'] = [preprint_corrections]
    topics = get_topics(general_path,identifier)
    if topics != None:
        doc['topicCategory'] = topics
    evals = get_altmetrics(general_path,identifier)
    if evals != None:
        doc['evaluations']=evals
    return(doc)