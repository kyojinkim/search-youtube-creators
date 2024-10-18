TYPE_TIPS = """
Here are some tips to help you for deciding the type condition:

1. **For type='channel' and query='travel':**
- Channels with 'travel' in the channel name
- Channels with 'travel' in the channel description
- Channels that primarily upload travel-related content (based on the overall content topic of the channel) 

2. **For type='video' and query='travel':**
- Videos with 'travel' in the video title
- Videos with 'travel' in the video description
- Videos with 'travel' in the video tag
- Videos with 'travel' mentioned in captions
- Videos with topics related to 'travel' (based on YouTube's content analysis algorithm)

3. **For type='playlist' and query='travel':**
- Playlists with 'travel' in the playlist title
- Playlists with 'travel' in the playlist description
- Playlists with videos related to 'travel'
"""

QUERY_TIPS = """
Here are some advanced search tips to help you find exactly what you're looking for:

1. **Simple Search**: Enter single words or phrases.
- Example: `vlog` or `cooking tutorial`

2. **Compound Search**: Combine multiple words or phrases.
- Example: `travel vlog Europe`

3. **Exact Phrase**: Use quotes for exact matches.
- Example: `"how to code"`

4. **Boolean Operators**: Use AND, OR, - (NOT).
- AND: `travel AND vlog` (spaces are treated as AND by default)
- OR: `travel OR vlog`
- NOT: `travel -cruise` (excludes 'cruise' from 'travel' videos)

5. **Special Keywords**: Search specific metadata.
- `allintitle:`: All words in title. Example: `allintitle: travel vlog`
- `intitle:`: Specific word in title. Example: `intitle:travel vlog`

6. **Wildcard**: Use '*' for partial matches.
- Example: `how to * a cake`
"""