import streamlit as st
import requests
import re
import openai
# import os

from search_articles import parse_keywords, search_articles, get_articles_xml, parse_articles_info, select_articles, get_citation_xml, parse_citation

# openai.organization = os.getenv("OPENAI_ORGANIZATION")

def get_completion(messages, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=800,
        temperature=0.7, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


# Sidebar inputs    
st.sidebar.title("PubMed Pal 📝")
    
st.sidebar.write('''👋 Welcome to PubMed Pal! \n\n
I created this app to help small business owners to create educational blog posts for their target customers. \n
This is a project for fun and is not a final product. There's a lot that can be improved to make this app better. 🤗 \n
**Take results with a grain of** 🧂
''')

st.sidebar.markdown("For more on how this app works, check out my [post on Medium](https://medium.com/@zhaojj1014/developing-an-ai-powered-content-generation-app-for-small-businesses-dd3abae358e0) or the source code on [Github](https://github.com/zhaojj1014/PubMed_Pal/tree/main).")

st.sidebar.divider()

st.sidebar.markdown("## How to use\n"
            "1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) below.\n"
            "2. Enter keywords to search research articles.\n"
            "3. Describe the target audience.\n"
            "4. Validate the result.")


api_key = st.sidebar.text_input("Enter your OpenAI API key:",
                                type="password",
                                placeholder="Paste your OpenAI API key here (sk-...)",
                                help="You can get your API key from https://platform.openai.com/account/api-keys."
                               )

st.sidebar.divider()

st.sidebar.markdown("Made by [Jinjing Zhao](https://www.linkedin.com/in/jinjing-zhao-82622254/)")

if api_key:
    openai.api_key = api_key
    
    topic = st.text_input("What topic would you like to write about?",
                         placeholder="acupuncture, menopause")
    audience = st.text_input("Who is the target audience?",
                            placeholder="women")
    generate_button = st.button("Generate article!")
    
    if generate_button:
        st.text("Searching PubMed... ")
        # Code to search articles in PubMed
        keywords = parse_keywords(topic)
        article_id_list = search_articles(keywords, 100)
        articles_xml = get_articles_xml(article_id_list)

        articles_df = parse_articles_info(articles_xml, keywords)
    
    
        # Select articles from search results
        if len(articles_df) >=3: 
            # Display search results in the text area
            st.text(f"Found {len(articles_df)} articles.")

            # Spinner
            with st.spinner('Generating the blog post. Please wait...'): 

                # Select 3 articles from search results
                selected_articles = select_articles(articles_df)
                selected_articles_df = articles_df[articles_df['ArticleId'].isin(selected_articles)]
                selected_articles_df = selected_articles_df[['PubYear', 'Abstract']]
                # st.dataframe(selected_articles_df)
                
                # Get citations
                citation_xml = get_citation_xml(selected_articles)
                references = parse_citation(citation_xml)

                # Put together 3 abstracts as the summary for chatgpt
                all_articles = ''
                PubYear = selected_articles_df['PubYear'].tolist()
                Abstract = selected_articles_df['Abstract'].tolist()

                for i in range(len(selected_articles_df)):
                    article_nr = str(i+1)
                    article = f'Article {article_nr} (published in {PubYear[i]}): {Abstract[i]} '
                    all_articles += article

                # st.text_area("Abstracts for ChatGPT", value=all_articles)

                # Code to generate the article based on user input

                messages = [
                        {'role':'system', 'content':'You are passionate about helping individuals from all walks of life achieve optimal health and wellness. \
                                                    You read about life sciences and biomedical research, then summarize the findings, \
                                                    and share the knowledge in plain English language that\'s easy to understand by a high school student. \
                                                    You want to educate people about the benefits of nutrition, exercise and healthy lifestyle.'},
                        {'role':'user', 'content':f'You are going to write an educational blog post based on the summaries provided below delimited in triple backticks. \
                            You will focus on {topic}. Your writing is tailored to {audience}. \
                            Summaries: ```{all_articles} ``` \
                            Create a proper title for the blog post. \
                            Start the article with a hook that grabs the attention of {audience}. \
                            The article has less than 400 words and no more than 6 paragraphs. \
                            Do not include references at the end. \
                            Do not include any hyperlinks. '
                        }]

                response = get_completion(messages)
#                 response = '''# Can Acupuncture Help with Menopause Symptoms?

#     Are you experiencing menopause symptoms and looking for alternative treatment options? Menopausal symptoms, such as hot flashes, night sweats, vaginal dryness, and mood changes, can significantly impact your quality of life. While hormone therapy is commonly used to manage these symptoms, there is growing interest in exploring other nonpharmacologic treatments, including acupuncture.

#     Recent studies have investigated the effectiveness of acupuncture in relieving menopause symptoms. One study published in 2022 found that percutaneous tibial nerve stimulation (PTNS) and electro-acupuncture near the tibial nerve increased vaginal blood perfusion and serum estrogen levels in a rat model. These findings suggest that acupuncture may have potential benefits for menopausal women by mitigating harmful reproductive and systemic changes associated with reduced ovarian activity and estrogen levels.
#     '''


                st.success('Article Generated!')

                # Display the article text in the text area
                st.text_area("Generated Article:", value=response, height=600, label_visibility="collapsed") 
                
                # Add citations to the end
                st.subheader("References")
                # st.markdown(response)
                for i in range(len(references)):
                    st.markdown(references[i])
                    
                # Warning message at the end
                st.divider()
                st.markdown("**Make sure to validate the generated content by looking up the referenced articles in [PubMed](https://pubmed.ncbi.nlm.nih.gov/)!**")
                


        else: 
            # search_results = "I can't find enough recent articles about this topic. Try another topic!"
            st.text("I can't find enough recent articles about this topic. Try another topic!")

else: st.text("Please enter your OpenAI API key to proceed.")

# topic = st.sidebar.text_input("What topic would you like to write about?", autocomplete="acupuncture, menopause")
# audience = st.sidebar.text_input("Who is the target audience?", autocomplete="women")
# generate_button = st.sidebar.button("Generate article!")


    


