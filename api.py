import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import defaultdict

from logs import setup_logger


logger = setup_logger(__name__)

class YouTubeClient:
    def __init__(self, api_key):
        self.client = build('youtube', 'v3', developerKey=api_key)

    def search_list(self, query, search_type, results_per_page, page_token, region_code):
        """
        search with query value in type.
        """
        try:
            search_response = self.client.search().list(
                q=query,
                type=search_type,
                part='id, snippet',
                maxResults=results_per_page,
                order='title',
                pageToken=page_token,
                regionCode=region_code
            ).execute()

            page_info = search_response.get('pageInfo', {})
            pagination_token = {
                'next_token': search_response.get('nextPageToken', None),
                'prev_token': search_response.get('prevPageToken', None)
            }

            logger.info(f"number search_response, {len(search_response.get('items', []))}")

            return search_response.get('items', []), page_info, pagination_token

        except HttpError as e:
            logger.error(f"Failed to get search list, {e.error_details}")
            raise e

    def get_playlist_info(self, playlist_id):
        """
        get playlist informations.
        """
        try:
            playlist_response = self.client.playlistItems().list(
                part='snippet',
                playlistId=playlist_id
            ).execute()

            if 'items' not in playlist_response:
                return {
                    'publishedAt': 'None'
                }

            latest_video = playlist_response['items'][0]['snippet']

            return {
                'publishedAt': latest_video['publishedAt']
            }

        except HttpError as e:
            if e.status_code == 404: # playlist not found
                return {
                    'publishedAt': 'None'
                }

            raise Exception(f'An error occurred while getting playlist info, {e}')

    def get_channel_info(self, channel_id):
        """
        get channel informations.
        """
        try:
            channel_response = self.client.channels().list(
                part='snippet, statistics, contentDetails',
                id=channel_id
            ).execute()

            if 'items' in channel_response:
                channel = channel_response['items'][0]
                playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
                latest_video = self.get_playlist_info(playlist_id)

                return {
                    'title': channel['snippet']['title'],
                    'owner_name': channel['snippet'].get('customUrl', 'Unknown'),
                    'country': channel['snippet'].get('country', 'Unknown'),
                    'description': channel['snippet'].get('description', ''),
                    'created_at': channel['snippet']['publishedAt'], # channel creation date
                    'subscribers': int(channel['statistics']['subscriberCount']),
                    'count_video': int(channel['statistics']['videoCount']),
                    'count_view': int(channel['statistics']['viewCount']),
                    'latest_video_updated_at': latest_video['publishedAt']
                }

            logger.info(f'No items in channel response from {channel_id}')
            return None

        except HttpError as e:
            logger.info(f"Failed to get channel info, {e.error_details}")
            raise e


def sort_creator_info(youtube_client, results):
    """
    retrieve and sort creator information based on subscriber count.
    """
    # creators dictionary
    creators = defaultdict(
        lambda: {'title': '', 'owner_name': '', 'country': '', 'description': '', 'created_at': '', 'subscribers': 0, 'count_video': 0, 'count_view': 0, 'latest_video_updated_at': ''}
    )

    for result in results:
        channel_id = result['snippet']['channelId']
        if channel_id not in creators:
            channel_info = youtube_client.get_channel_info(channel_id)
            if channel_info:
                creators[channel_id] = channel_info

    # sort by subscribers
    sorted_creators = sorted(creators.items(), key=lambda x: x[1]['subscribers'], reverse=True)
    return sorted_creators

def extract_email(description):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, description)
    return match.group(0) if match else 'Not found'

def check_duplicated(existed_emails, email):
    """
    check duplicate email.
    """
    return email not in existed_emails and email != 'Not found'

def find_top_creators(api_key, query, search_type, results_per_page, page_token=None, region_code='KR', current_page=1):
    """
    find top creators.
    """
    youtube_client = YouTubeClient(api_key)

    results, page_info, pagination_token = youtube_client.search_list(
        query=query,
        search_type=search_type,
        results_per_page=results_per_page,
        page_token=page_token,
        region_code=region_code
    )

    # current page and range
    total_results = page_info.get('totalResults', 0)
    results_per_page = page_info.get('resultsPerPage', results_per_page)

    start_index = (current_page - 1) * results_per_page + 1
    end_index = min(start_index + results_per_page - 1, total_results)

    logger.info(f"total_results: {total_results}, results_per_page: {results_per_page}, start_index: {start_index}, end_index: {end_index}")

    page_info_extended = {
        **page_info,
        'current_page': current_page,
        'start_index': start_index,
        'end_index': end_index
    }

    # sort by subscribers
    sorted_creators = sort_creator_info(youtube_client, results)

    return sorted_creators, page_info_extended, pagination_token

def download_creators(api_key, query, search_type, region_code, sessionState, progress_bar, progress_status):
    """
    download creators.
    """

    results_per_page = sessionState.results_per_page
    max_results = sessionState.download.max_results

    uploaded_results = sessionState.download.uploaded_results
    search_results = sessionState.download.search_results

    # list up existed email
    existed_emails = []
    for filename, data in uploaded_results.items():
        existed_emails.extend([records['Email'] for records in data])

    # client 
    youtube_client = YouTubeClient(api_key)

    # loop. search creators until max results
    while len(search_results) < max_results:
        page_token = sessionState.download.page_token

        results, page_info, pagination_token = youtube_client.search_list(
            query=query,
            search_type=search_type,
            results_per_page=results_per_page,
            page_token=page_token,
            region_code=region_code
        )

        # sort by subscribers
        sorted_creators = sort_creator_info(youtube_client, results)

        # append to search results
        for channel_id, creator in sorted_creators:
            email = extract_email(creator['description'])
            if check_duplicated(existed_emails, email):
                search_results.append({
                    'channel_id': channel_id,
                    'email': email,
                    **creator,
                })
                existed_emails.append(email)

                # progress estimate
                length_search_results = len(search_results)
                progress = min(length_search_results / max_results, 1.0)
                progress_bar.progress(progress)
                progress_status.text(f"Downloaded {length_search_results} out of {max_results} results")

                # break max_results
                if length_search_results >= max_results:
                    break

        # next page token
        sessionState.download.page_token = pagination_token['next_token']

        # break if no more next token
        if not sessionState.download.page_token or len(search_results) >= max_results:
            break
    
    progress_status.text(f"Download completed. Total results: {len(search_results)}")
