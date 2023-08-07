import zipfile
import io
import requests
import re
from difflib import SequenceMatcher
import string
from habanero import Crossref
cr = Crossref()
import numpy as np

def magic_link_from_doi(doi):
    """
    This uses the earthref MagIC api to search for a magic contribution using a doi. 
    Adapted from pmagpy's "ipmag.download_magic_from_doi()"
    
    Input: 
        doi: str beginning with '10.'
        
    Output: 
        earthref_doi_link: http link if found
                           NaN if not found in MagIC database, try using magic_link_from_title to search the title in MagIC
    """
    api = 'https://api.earthref.org/v1/MagIC/{}'
    response = requests.get(api.format('download'), params={'doi': doi, 'n_max_contributions': 1})
    if (response.status_code == 200):
        contribution_zip = zipfile.ZipFile(io.BytesIO(response.content))
        for filename in contribution_zip.namelist():
            if (re.match(r'^\d+\/magic_contribution_\d+\.txt', filename)):
                contribution_text = io.TextIOWrapper(contribution_zip.open(filename)).read()
                file = filename
                with open('magic_contribution.txt', 'wt') as fh:
                    fh.write(contribution_text)
            magic_id = file.split('/')[0]
            #print(file)
            earthref_doi_link = 'http://dx.doi.org/10.7288/V4/MAGIC/' + magic_id
            return earthref_doi_link    
    else:
        earthref_doi_link = np.NaN
    return earthref_doi_link

def is_string_similar(s1, s2, threshold: float = 0.90):
    return SequenceMatcher(a=s1, b=s2).ratio() > threshold

def get_doi(title, cursor_max = 3):
    """
    This function uses the crossref.org API to search for a journal publication based on its title and
    returns its doi. 
    Specifically, it pulls a query of the top 3 results for the title and checks the similarity of the title
    using 'is_string_similar' to verify that the similarity level between the given title and the found title 
    is above the threshold, which is currently set to 90. It returns the doi of the title that fits this criteria
    and it not it returns 0.
    
    Input: 
        title: str
    
    Ouput: 
        doi_result: doi that corresponds to the input title
                    nan if a matching title and doi was not found
    """
    result = cr.works(query = title, cursor = '*', cursor_max = 3, limit = 3, select = ['title', 'DOI','author'])['message']['items']
    result0 = result[0]
    result1 = result[1]
    result2 = result[2]
    title_result = result0['title'][0]
    doi_result = result0['DOI']
    
    if is_string_similar(title,title_result) == False:
        doi_result = np.NaN
        title_result1 = result1['title'][0]
        doi_result1 = result1['DOI']
        if is_string_similar(title,title_result1) == False:
            doi_result = np.NaN
            title_result2 = result2['title'][0]
            doi_result2 = result2['DOI']
            if is_string_similar(title,title_result2) == False:
                doi_result = np.NaN
            else: 
                doi_result = doi_result2
        else: 
            doi_result = doi_result1
    else: 
        doi_result = doi_result
    #print(doi_result)  
    return doi_result

def magic_link_from_title(title):
    """
    This function uses a paper title to search the MagIC interface for a matching contribution link. 
    
    Input: 
        titel:str
    
    Output: 
        earthref_doi_link
        nan: If the title could not be found because there was an error with the Earthref Data DOI link, 
             the title was not found, or the spelling of the title differed.
             Be sure to manually copy and paste the title into MagIC to be sure.
    """
    api = 'https://api.earthref.org/v1/MagIC/{}'
    response = requests.get(api.format('download'), params={'reference_title': title, 'only_latest':'true'})
    
    #print(response.url)
    #print(response.status_code)
    
    if (response.status_code == 200):
        contribution_zip = zipfile.ZipFile(io.BytesIO(response.content))
        for filename in contribution_zip.namelist():
            
            #print(contribution_zip.namelist()) # check contributions found
            
            if (re.match(r'^\d+\/magic_contribution_\d+\.txt', filename)):
                contribution_text = io.TextIOWrapper(contribution_zip.open(filename)).read()
                file = filename
                with open('magic_contribution.txt', 'wt') as fh:
                    fh.write(contribution_text)
            magic_id = file.split('/')[0]
            earthref_doi_link = 'http://dx.doi.org/10.7288/V4/MAGIC/' + magic_id
            return earthref_doi_link
        
    elif (response.status_code == 204): 
        new_title = title.translate(str.maketrans('', '', string.punctuation)) 
        response = requests.get(api.format('download'), params={'reference_title': new_title, 'n_max_contributions': 1, 'only_latest':'true'})
        #print(new_title)
        #print(response.url)
        #print(response.status_code)
        if (response.status_code == 200):
            contribution_zip = zipfile.ZipFile(io.BytesIO(response.content))
            for filename in contribution_zip.namelist():            
                if (re.match(r'^\d+\/magic_contribution_\d+\.txt', filename)):
                    contribution_text = io.TextIOWrapper(contribution_zip.open(filename)).read()
                    file = filename
                    with open('magic_contribution.txt', 'wt') as fh:
                        fh.write(contribution_text)
                magic_id = file.split('/')[0]
                earthref_doi_link = 'http://dx.doi.org/10.7288/V4/MAGIC/' + magic_id
                return earthref_doi_link
        #else: 
            #print("Earthref Data DOI or spelling Error: Try searching this title directly at 'https://www2.earthref.org/MagIC/search'")
    return np.NaN

def magic_link_from_title2(title):
    doi = get_doi(title)
    return magic_link_from_doi(doi)

def is_string_similar(s1, s2, threshold: float = 0.90):
    return SequenceMatcher(a=s1, b=s2).ratio() > threshold

def get_doi_from_title_auth(title, author, num_results = 3):
    """
    This function uses the crossref.org API to search for a journal publication based on its title and author then
    returns its doi. 
    Specifically, it pulls a query of the top results (default 3) for the title and checks the similarity of the title then author
    using 'is_string_similar' to verify that the similarity level between the given title and the found title 
    is above the threshold, which is currently set to 90. It returns the doi of the title that fits this criteria
    and if not, then it returns 0. If the author does not match it will return 1. 
    
    Input: 
        title: str
        author: str
    
    Ouput: 
        doi_result: doi that corresponds to the input title
                    0 if a matching title and doi was not found
                    1 if a matching title was found but the authors do not match
    """
    first_author_last = (author.split(',')[0]).lower()
    result = cr.works(query = title, cursor = '*', cursor_max = num_results, limit = num_results , select = ['title', 'DOI','author'])['message']['items']
 
    for i in range(num_results): 
        result_n  = result[i]
        title_result = result_n['title'][0]
        doi_result = result_n['DOI']
    
        # if found title does not match input title by 90%
        if not is_string_similar(title,title_result): 
            doi_result = 0
        break
    
        if not 'author' in result_n.keys():
             doi_result = 1
        break
        
        first_author_last_result = (result_n['author'][0]['family']).lower()

        #if found author does not match input first author
        if not is_string_similar(first_author_last, first_author_last_result):
            doi_result = 1
        break
    
    return doi_result