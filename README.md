
## Goal

This project aims to create a conversational tool that can be attached to a mailbox to give AI analysis/lookup
Effectively, I want to 'train' an llm to use an mbox as context for RAG.

## Limitations and Considerations:

### 1. mbox files can be large.
My current file is ~2GB and so I don't want to pass all my emails through an LLM. This can be expensive if I use openai and time-consuming if I use ollama.

#### Possible Solutions

- Skip emails from a subscribing list.
    
    These are not specific for the user and I am assuming they won't be too important for most users. Also, when I checked a batch of 100 of my emails, given not too busy with important info, 78/100 were from mailing lists.

- Run analysis in batches.

    This can help quantify how many tokens are needed for an entire mbox

- Create vector embeddings for each email and only check mbox when we need to pull on actual text


### 2. Storage of Analysis

I will not want to use cloud storage unless I am deploying this as an actual product. 

- For now just host some NoSQL db locally for embeddings 

    

