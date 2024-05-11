#!/usr/bin/env python
# coding: utf-8

# ## Setup

# In[1]:


import pandas as pd
import numpy as np
import os
import sys
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PyPDFium2Loader
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import random

from helpers.df_helpers import documents2Dataframe
from helpers.df_helpers import df2Graph
from helpers.df_helpers import graph2Df

import networkx as nx
import seaborn as sns
from pyvis.network import Network

import logging

# Logger setup
logger = logging.getLogger("__name__")
logger.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.CRITICAL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
    handlers=[
        logging.FileHandler("extract_graph.log"),
        logging.StreamHandler(sys.stdout)
    ]
)



## Input data directory
data_dir = "ag_news"
inputdirectory = Path(f"./data/raw/input/{data_dir}")
## This is where the output csv files will be written
out_dir = data_dir
outputdirectory = Path(f"./data/interim/output/{out_dir}")


# In[2]:


ag_news = pd.read_csv("data/raw/ag_news_train.csv", header=None)


# In[3]:


# ag_news_txt = ag_news[2].str.cat(sep="\n")
ag_news_txt = ag_news[2].iloc[:50].str.cat(sep="\n")


# In[4]:


with open("data/raw/input/ag_news/ag_news.txt", "w") as f:
    f.write(ag_news_txt)


# ## Load Documents

# In[5]:


## Dir PDF Loader
# loader = PyPDFDirectoryLoader(inputdirectory)
## File Loader
# loader = PyPDFLoader("./data/MedicalDocuments/orf-path_health-n1.pdf")
loader = DirectoryLoader(inputdirectory, use_multithreading=True, show_progress=True)
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150,
    length_function=len,
    is_separator_regex=False,
)

pages = splitter.split_documents(documents)
logger.debug("Number of chunks = " + str(len(pages)))
logger.debug("Example of a chunk (No3):\n" + pages[3].page_content)


# ## Create a dataframe of all the chunks

# In[6]:



df = documents2Dataframe(pages)
logger.debug("Dataframe of chunks:\n"
             + "Shape: "+ str(df.shape) + "\n"
             + "Head:\n" + str(df.head()) + "\n")


# ## Extract Concepts

# In[7]:



# If regenerate is set to True then the dataframes are regenerated and Both the dataframes are written in the csv format so we dont have to calculate them again. 
# 
#         dfne = dataframe of edges
# 
#         df = dataframe of chunks
# 
# 
# Else the dataframes are read from the output directory

# In[8]:


## To regenerate the graph with LLM, set this to True
regenerate = True

if regenerate:
    concepts_list = df2Graph(df, model='zephyr:latest')
    dfg1 = graph2Df(concepts_list)
    if not os.path.exists(outputdirectory):
        os.makedirs(outputdirectory)
    
    dfg1.to_csv(outputdirectory/"graph.csv", sep="|", index=False)
    df.to_csv(outputdirectory/"chunks.csv", sep="|", index=False)
else:
    dfg1 = pd.read_csv(outputdirectory/"graph.csv", sep="|")

dfg1.replace("", np.nan, inplace=True)
dfg1.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
dfg1['count'] = 4 
## Increasing the weight of the relation to 4. 
## We will assign the weight of 1 when later the contextual proximity will be calculated.  
logger.debug("Shape and head of produced graph as a dataframe:\n"
             + str(dfg1.shape) + "\n"
             + str(dfg1.head()) + "\n")


# ## Calculating contextual proximity

# In[9]:


def contextual_proximity(df: pd.DataFrame) -> pd.DataFrame:
    ## Melt the dataframe into a list of nodes
    dfg_long = pd.melt(
        df, id_vars=["chunk_id"], value_vars=["node_1", "node_2"], value_name="node"
    )
    dfg_long.drop(columns=["variable"], inplace=True)
    # Self join with chunk id as the key will create a link between terms occuring in the same text chunk.
    dfg_wide = pd.merge(dfg_long, dfg_long, on="chunk_id", suffixes=("_1", "_2"))
    # drop self loops
    self_loops_drop = dfg_wide[dfg_wide["node_1"] == dfg_wide["node_2"]].index
    dfg2 = dfg_wide.drop(index=self_loops_drop).reset_index(drop=True)
    ## Group and count edges.
    dfg2 = (
        dfg2.groupby(["node_1", "node_2"])
        .agg({"chunk_id": [",".join, "count"]})
        .reset_index()
    )
    dfg2.columns = ["node_1", "node_2", "chunk_id", "count"]
    dfg2.replace("", np.nan, inplace=True)
    dfg2.dropna(subset=["node_1", "node_2"], inplace=True)
    # Drop edges with 1 count
    dfg2 = dfg2[dfg2["count"] != 1]
    dfg2["edge"] = "contextual proximity"
    return dfg2


dfg2 = contextual_proximity(dfg1)
dfg2.tail()


# ### Merge both the dataframes

# In[10]:


dfg = pd.concat([dfg1, dfg2], axis=0)
dfg = (
    dfg.groupby(["node_1", "node_2"])
    .agg({"chunk_id": ",".join, "edge": ','.join, 'count': 'sum'})
    .reset_index()
)
dfg


# ## Calculate the NetworkX Graph

# In[11]:


nodes = pd.concat([dfg['node_1'], dfg['node_2']], axis=0).unique()
nodes.shape


# In[12]:



G = nx.Graph()

## Add nodes to the graph
for node in nodes:
    G.add_node(
        str(node)
    )

## Add edges to the graph
for index, row in dfg.iterrows():
    G.add_edge(
        str(row["node_1"]),
        str(row["node_2"]),
        title=row["edge"],
        weight=row['count']/4
    )


# ### Calculate communities for coloring the nodes

# In[13]:


communities_generator = nx.community.girvan_newman(G)
top_level_communities = next(communities_generator)
next_level_communities = next(communities_generator)
communities = sorted(map(sorted, next_level_communities))
logger.debug("Number of Communities = " + str(len(communities)) + "\n"
             + "Communities found:\n" + str(communities) +"\n")


# ### Create a dataframe for community colors

# In[14]:


palette = "hls"

## Now add these colors to communities and make another dataframe
def colors2Community(communities) -> pd.DataFrame:
    ## Define a color palette
    p = sns.color_palette(palette, len(communities)).as_hex()
    random.shuffle(p)
    rows = []
    group = 0
    for community in communities:
        color = p.pop()
        group += 1
        for node in community:
            rows.append({"node": node, "color": color, "group": group})
    df_colors = pd.DataFrame(rows)
    return df_colors


colors = colors2Community(communities)
colors


# ### Add colors to the graph

# In[15]:


for index, row in colors.iterrows():
    G.nodes[row['node']]['group'] = row['group']
    G.nodes[row['node']]['color'] = row['color']
    G.nodes[row['node']]['size'] = G.degree[row['node']]


# In[16]:



graph_output_directory = "./reports/graphs/graph.html"

net = Network(
    notebook=False,
    # bgcolor="#1a1a1a",
    cdn_resources="remote",
    height="900px",
    width="100%",
    select_menu=True,
    # font_color="#cccccc",
    filter_menu=False,
)

net.from_nx(G)
# net.repulsion(node_distance=150, spring_length=400)
net.force_atlas_2based(central_gravity=0.015, gravity=-31)
# net.barnes_hut(gravity=-18100, central_gravity=5.05, spring_length=380)
net.show_buttons(filter_=["physics"])

net.show(graph_output_directory)


# In[ ]:




