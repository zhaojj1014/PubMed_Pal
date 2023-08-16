import pandas as pd
import numpy as np
import random
import requests
import xml.etree.ElementTree as ET
from IPython.display import JSON
from IPython.display import Markdown

stop_words = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"]


def generate_article_prompt(topic, target_audience):
    return f"Writing an article about {topic} for {target_audience}..."

def count_words(text):
    return len(str(text).split())

# parse keywords provided by user
def parse_keywords(topic):
    
    keywords = []
    # keywords_parsed = []
    
    topic_list = topic.split(',')
    
    for topic in topic_list:
        words = topic.split()
        keywords += words
    
    keywords_parsed = [keyword.lower() for keyword in keywords]
    
    keywords_no_stopwords = [word for word in keywords_parsed if word not in stop_words]
    
    return keywords_no_stopwords


def search_articles (keywords, retmax):
    
    base = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax={retmax}&term='
  
    query = '+AND+'.join(keywords)
    esearch_url = base + query
    print(esearch_url)

    response = requests.get(esearch_url)

    pubmedJson = response.json()

    idlist = pubmedJson['esearchresult']['idlist']

    return idlist

def get_articles_xml (idlist):
    base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&rettype=abstract&sort=relevance&id='

    ids = ','.join(idlist)

    efetch_url = base + ids
    print(efetch_url)
    response = requests.get(efetch_url)
    xml_reponse = response.content

    return xml_reponse

def parse_articles_info (articles_xml, keywords_no_stopwords):
    # Parse the XML
    root = ET.fromstring(articles_xml)

    # Initialize lists to store extracted data
    pub_years = []
    journal_titles = []
    article_titles = []
    article_ids = []
    publication_types = []
    journal_countries = []
    abstract_parts = []
    abstract = []

    # Loop through each PubmedArticle element and extract the required information
    for article in root.findall('.//PubmedArticle'):
        pub_year = article.find('.//PubDate/Year').text if article.find('.//PubDate/Year') is not None else np.NaN
        journal_title = article.find('.//Journal/Title').text if article.find('.//Journal/Title') is not None else np.NaN
        article_title = article.find('.//ArticleTitle').text if article.find('.//ArticleTitle') is not None else np.NaN
        article_id = article.find('.//ArticleId[@IdType="pubmed"]').text if article.find('.//ArticleId[@IdType="pubmed"]') is not None else np.NaN
        pub_type_elements = article.findall('.//PublicationType')
        pub_types = [pub_type.text for pub_type in pub_type_elements]
        # journal_country = article.find('.//MedlineJournalInfo/Country').text if article.find('.//MedlineJournalInfo/Country') is not None else ''

        # Extract AbstractText
        abstract_text_element = article.find('.//Abstract/AbstractText')
        if abstract_text_element is not None:
            if abstract_text_element.text is not None:
                abstract_text = abstract_text_element.text
        else: abstract_text=''


        # Append the extracted data to respective lists
        pub_years.append(pub_year)
        journal_titles.append(journal_title)
        article_titles.append(article_title)
        article_ids.append(article_id)
        publication_types.append(pub_types)
        # journal_countries.append(journal_country)
        # abstract_parts.append(abstract_parts_dict)
        abstract.append(abstract_text)

    # Create a DataFrame
    data = {
        'PubYear': pub_years,
        'JournalTitle': journal_titles,
        'ArticleTitle': article_titles,
        'ArticleId': article_ids,
        'PublicationTypes': publication_types,
        # 'Journal_Country': journal_countries,
        # 'AbstractTextParts': abstract_parts,
        'Abstract': abstract
    }

    df = pd.DataFrame(data)

    df = df.dropna()
    
    # Check if article abstract contains all the keywords.
    df['has_keywords'] = df['Abstract'].apply(lambda x: all(keyword in x.lower() for keyword in keywords_no_stopwords))
    # Keep the records where Abstract contains all the keywords
    df=df[df['has_keywords']==True]
    
    # Flag review articles
    df['review_ind'] = df['PublicationTypes'].apply(lambda x: 1 if 'Meta-Analysis' in x or 'Review' in x else 0)

    # Count abstract words
    df['abstract_word_count'] = df['Abstract'].apply(count_words)
    
    # Convert publication year to integer
    df['PubYear'] = df['PubYear'].astype('int')
    
    '''Filter the abstract based on a few considerations:
    The abstract can't be too short (less than 80 words)
    The article can't be too old (published after 2000)'''
    
    df = df[(df['PubYear']>=2000) & (df['abstract_word_count']>=80)]
    
    return df


def select_articles(df):
    '''Select 3 articles in total:

    first randomly draw 3 articles from review_articles_since_2010.
    If there aren't 3 articles in review_articles_since_2010, then I randomly draw the rest from non_review_articles_2010_to_2015.
    If I still don't have 3 articles, then randomly draw the rest from non_review_articles_2010_to_2015.
    If I still don't have 3 articles, randomly draw the rest from review_articles_2000_to_2010.
    If I still don't have 3 articles, then randomly draw the rest from non_review_articles_2000_to_2010.
    '''
    
    # Put the articles into the following buckets, then draw X number of articles from each bucket randomly

    # Review articles since 2010
    review_articles_since_2010 = df[(df['PubYear'] >= 2010) & (df['review_ind'] == 1)].sort_values(by='PubYear', ascending=False).reset_index()
    print('review_articles_since_2010:', len(review_articles_since_2010))

    # Review articles 2000-2010
    review_articles_2000_to_2010 = df[(df['PubYear'] >= 2000) &(df['PubYear'] < 2010) & (df['review_ind'] == 1)].sort_values(by='PubYear', ascending=False).reset_index()
    print('review_articles_2000_to_2010:', len(review_articles_2000_to_2010))

    # Non-review articles since 2015
    non_review_articles_since_2015 = df[(df['PubYear'] >= 2015) & (df['review_ind'] == 0)].sort_values(by='PubYear', ascending=False).reset_index()
    print('non_review_articles_since_2015:', len(non_review_articles_since_2015))

    # Non-review articles 2010-2015
    non_review_articles_2010_to_2015 = df[(df['PubYear'] >= 2010) & (df['PubYear'] < 2015) & (df['review_ind'] == 0)].sort_values(by='PubYear', ascending=False).reset_index()
    print('non_review_articles_2010_to_2015:', len(non_review_articles_2010_to_2015))

    # Non-review articles 2000-2010
    non_review_articles_2000_to_2010 = df[(df['PubYear'] >= 2000) & (df['PubYear'] < 2010) & (df['review_ind'] == 0)].sort_values(by='PubYear', ascending=False).reset_index()
    print('non_review_articles_2000_to_2010:', len(non_review_articles_2000_to_2010))

    # Combine all dataframes into a single list for easier random selection
    dataframes = [
        review_articles_since_2010,
        non_review_articles_since_2015,
        non_review_articles_2010_to_2015,
        review_articles_2000_to_2010,
        non_review_articles_2000_to_2010
    ]

    # Initialize an empty list to store the randomly selected articles
    selected_articles = []

    # Step 1: Randomly select from review_articles_since_2010
    review_articles = dataframes[0]
    if len(review_articles) >= 3:
        selected_articles.extend(review_articles.sample(n=3)['ArticleId'].tolist())
    else:
        selected_articles.extend(review_articles.sample(n=len(review_articles))['ArticleId'].tolist())

    # Calculate the number of remaining articles needed to reach the total of 3
    remaining_needed = 3 - len(selected_articles)

    # Step 2: Randomly select from non_review_articles_since_2015
    non_review_articles = dataframes[1]
    if remaining_needed > 0:
        if len(non_review_articles) >= remaining_needed:
            selected_articles.extend(non_review_articles.sample(n=remaining_needed)['ArticleId'].tolist())
        else:
            selected_articles.extend(non_review_articles.sample(n=len(non_review_articles))['ArticleId'].tolist())

        # Calculate the number of remaining articles needed to reach the total of 3
        remaining_needed = 3 - len(selected_articles)

    # Step 3: Randomly select from non_review_articles_2010_to_2015
    non_review_articles = dataframes[2]
    if remaining_needed > 0:
        if len(non_review_articles) >= remaining_needed:
            selected_articles.extend(non_review_articles.sample(n=remaining_needed)['ArticleId'].tolist())
        else:
            selected_articles.extend(non_review_articles.sample(n=len(non_review_articles))['ArticleId'].tolist())

        # Calculate the number of remaining articles needed to reach the total of 3
        remaining_needed = 3 - len(selected_articles)

    # Step 4: Randomly select from review_articles_2000_to_2010
    review_articles = dataframes[3]
    if remaining_needed > 0:
        if len(review_articles) >= remaining_needed:
            selected_articles.extend(review_articles.sample(n=remaining_needed)['ArticleId'].tolist())
        else:
            selected_articles.extend(review_articles.sample(n=len(review_articles))['ArticleId'].tolist())

        # Calculate the number of remaining articles needed to reach the total of 3
        remaining_needed = 3 - len(selected_articles)

    # Step 5: Randomly select from non_review_articles_2000_to_2010
    non_review_articles = dataframes[4]
    if remaining_needed > 0:
        if len(non_review_articles) >= remaining_needed:
            selected_articles.extend(non_review_articles.sample(n=remaining_needed)['ArticleId'].tolist())
        else:
            selected_articles.extend(non_review_articles.sample(n=len(non_review_articles))['ArticleId'].tolist())

    # At this point, selected_articles will contain the randomly selected ArticleIDs from the different dataframes.
    return selected_articles


def get_citation_xml(idlist):
    base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=xml&rettype=abstract&id='
    ids = ','.join(idlist)

    efetch_url = base + ids
    print(efetch_url)
    response = requests.get(efetch_url)
    xml_reponse = response.content

    return xml_reponse


def parse_citation(citation_xml):
    # Load and parse the XML
    root = ET.fromstring(citation_xml.decode('utf-8'))

    # Extract required information from XML and generate APA bibliography
    bibliography = []
    for docsum in root.iter('DocSum'):
        data = {}

        # Extract data
        data['ArticleID'] = docsum.findtext("Id")
        data['Authors'] = [item.text for item in docsum.find(".//Item[@Name='AuthorList']")]
        data['PubDate'] = docsum.findtext(".//Item[@Name='PubDate']")
        data['FullJournalTitle'] = docsum.findtext(".//Item[@Name='FullJournalName']")
        data['Title'] = docsum.findtext(".//Item[@Name='Title']")
        data['Volume'] = docsum.findtext(".//Item[@Name='Volume']")
        data['Issue'] = docsum.findtext(".//Item[@Name='Issue']")
        data['Pages'] = docsum.findtext(".//Item[@Name='Pages']")
        # data['DOI'] = docsum.findtext(".//Item[@Name='DOI']")

        # Format bibliography entry in APA style
        # Format: Last name, F. M. (Year). Title of article. Title of Journal, volume(issue), pages.
        authors = ', '.join(data['Authors'])
        pub_year = data['PubDate'].split(' ')[0]
        bibliography_entry = f"{authors} ({pub_year}). {data['Title']} {data['FullJournalTitle']}, {data['Volume']}({data['Issue']}), {data['Pages']}."
        bibliography.append(bibliography_entry)
    
    return bibliography