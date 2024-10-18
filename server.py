import streamlit as st
import pandas as pd
import re, io

from api import find_top_creators, download_creators
from constants import TYPE_TIPS, QUERY_TIPS
from sessions import SessionState
from logs import setup_logger


__version__ = "0.0.1"

logger = setup_logger(__name__)

def format_number(num):
    match num:
        case _ if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        case _ if num >= 1000000:
            return f"{num/1000000:.1f}M"
        case _ if num >= 1000:
            return f"{num/1000:.1f}K"
        case _:
            return str(num)

def create_channel_link(channel_id):
    return f'https://www.youtube.com/channel/{channel_id}'

def extract_email(description):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, description)
    return match.group(0) if match else 'Not found'

def fetch_and_display(api_key, query, search_type, results_per_page, region_code, sessionState):
    # spinner for fetching data
    with st.spinner("Fetching Data..."):
        logger.info("Search list progress started.")

        # get top creators
        top_creators, page_info, pagination_token = find_top_creators(
            api_key=api_key,
            query=query,
            search_type=search_type,
            results_per_page=results_per_page,
            page_token=sessionState.search.page_token,
            region_code=region_code,
            current_page=sessionState.search.current_page
        )

        st.write(f"fetch results_per_page: {results_per_page}, {sessionState.results_per_page}")

        # update session with page_info
        sessionState.search.page_info = page_info

        # update session state for new page tokens
        sessionState.search.next_page_token = pagination_token.get('next_token')
        sessionState.search.prev_page_token = pagination_token.get('prev_token')

        # index base value
        index_base = (sessionState.search.current_page - 1) * sessionState.results_per_page

        # convert data to DataFrame
        df = pd.DataFrame(
            [
                {
                    "Index": index_base + i,
                    "Subscribers": format_number(info['subscribers']),
                    "Videos": format_number(info['count_video']),
                    "Views": format_number(info['count_view']),
                    "Channel Title": info['title'],
                    "Channel Id": channel_id,
                    "Owner Name": info['owner_name'],
                    "Email (Description)": extract_email(info['description']),
                    "Updated": info['latest_video_updated_at'],
                    "Created": info['created_at'],
                    "Country": info['country'],
                    "Link": create_channel_link(channel_id)
                }
                for i, (channel_id, info) in enumerate(top_creators, 1)
            ]
        ).set_index("Index")

        logger.info("Search list progress done.")
        logger.info("Searched {df.size}.")

        st.dataframe(
            data=df,
            height=max(35 * (len(df) + 1), 350),
            use_container_width=True
        )

def refresh_uploaded_files(sessionState):
    current_files = st.session_state.files if 'files' in st.session_state else [] #if hasattr(st.session_state, 'download') else []

    # remove
    for file_name in sessionState.download.uploaded_files:
        if file_name not in current_files:
            sessionState.remove_file(file_name)

    # add
    for file in current_files:
        if file.name not in sessionState.download.uploaded_files:
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file)
                else:
                    st.error(f"Unsupported file format, {file.name}")
                    continue
                
                sessionState.add_file(file.name, df.to_dict('records'))
                logger.info(f"File {file.name} is uploaded.")

            except Exception as e:
                st.error(f"Error reading file {file.name}, {str(e)}")
                logger.error(f"Error reading file {file.name}, {str(e)}")

def handle_file_upload(sessionState):
    # file upload
    st.file_uploader(
        "Upload Existed CSV or Excel Files",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="files",
        on_change=lambda: refresh_uploaded_files(sessionState),
    )

    # display uploaded files
    if sessionState.download.uploaded_files:
        uploaded_results_count = sum([len(data) for data in sessionState.download.uploaded_results.values()])
        st.write("Total {} email is uploaded.".format(uploaded_results_count)) 


def main():
    logger.info(f"Starting, App version: {__version__}")
    
    # init session state
    sessionState = SessionState()

    #
    st.set_page_config(page_title="Search YouTube Creators", page_icon="📹", layout="wide")

    st.header("YouTube Creators")
    st.write("This app shows the creators based on the `query` and `type`")
    st.write("CAUTION: YouTube API DO NOT search all of the channels and videos. So, the result based on the subscriber count may not be accurate.")

    # configs
    container_configs = st.container()
    with container_configs:
        column_api_key, column_search_type, column_results_per_page, column_region_code = st.columns([3, 1, 1, 1])
        
        # api key
        with column_api_key:
            api_key = st.text_input("YouTube API Key", type="password", placeholder="e.g. Api key")
            # with st.expander("How to getAPI Key"):
            #     st.markdown(APIKEY_HOWTO)

        # type
        with column_search_type:
            search_type = st.selectbox("Type", options=["channel", "video", "playlist"], index=1)
            with st.expander("Type Tips"):
                st.markdown(TYPE_TIPS)

        # results per page
        with column_results_per_page:
            results_per_page = st.number_input("Results per Page", value=sessionState.results_per_page, min_value=10, max_value=50, step=10, help="Number between 10 and 50 with step 10.")

        # 
        with column_region_code:
            region_code = st.text_input("Region Code", value="", help="Region code for the country. e.g. US, GB, IN")

    # query
    container_query = st.container()
    with container_query:
        query = st.text_input("Query", placeholder="e.g. vlog, travel", help="Click 'Query Tips' below for advanced usage.")
        with st.expander("Query Tips"):
            st.markdown(QUERY_TIPS)

    # tabs for download and search
    tab_download, tab_search = st.tabs(["DOWNLOAD FILE", "SEARCH LIST"])

    with tab_search:
        container_nav = st.container()
        with container_nav:
            if st.button("SEARCH", use_container_width=True):
                sessionState.clear_pagination()
                sessionState.search.start_search = True

        # search process
        container_results = st.container()
        with container_results:
            # page and pagination
            column_blank, column_pageinfo, column_previous, column_next = st.columns([4, 2, 1, 1])

            # empty containers for pagination buttons
            placeholder_page_info = column_pageinfo.empty()
            placeholder_page_prev = column_previous.empty()
            placeholder_page_next = column_next.empty()

            if sessionState.search.start_search:
                if not api_key:
                    st.error("Please enter your YouTube API key.")
                    logger.error("YouTube API key is empty.")
                    return

                if not query.strip():
                    st.error("Please enter a Query.")
                    logger.error("Query is empty.")
                    return

                # store to session
                sessionState.results_per_page = results_per_page

                # reset page tokens on new search
                sessionState.search.next_page_token = None
                sessionState.search.prev_page_token = None

                # fetch and display data
                try:
                    st.write(f"results_per_page: {results_per_page}, {sessionState.results_per_page}")
                    fetch_and_display(
                        api_key=api_key,
                        query=query,
                        search_type=search_type,
                        results_per_page=results_per_page,
                        region_code=region_code,
                        sessionState=sessionState
                    )

                except Exception as e:
                    if not hasattr(e, 'error_details'):
                        st.error(f"An error occurred while fetching data, {e}")
                        logger.error("An error occurred while fetching data, {e}")
                        return

                    error_reason = e.error_details[0]['reason']
                    error_msg = e.error_details[0]['message']

                    st.error(f"{error_reason}: {error_msg}")
                    logger.error("{error_reason}: {error_msg}")
                    return

                # show page info
                page_info = sessionState.search.page_info
                total_results = page_info.get('totalResults', 0)
                start_index = page_info.get('start_index', 0)
                end_index = page_info.get('end_index', 0)
                placeholder_page_info.write(f"Found `{total_results}` channels, {start_index} - {end_index}")

                # reset start search
                sessionState.search.start_search = False

        # handle pagination
        if sessionState.search.prev_page_token:
            if placeholder_page_prev.button(f"Previous ({sessionState.search.prev_page_token})", use_container_width=True):
                sessionState.search.page_token = sessionState.search.prev_page_token
                sessionState.search.start_search = True
                sessionState.search.current_page = sessionState.search.current_page - 1

                logger.info(f"Pagination: previous {sessionState.search.prev_page_token}")
                st.rerun()

        if sessionState.search.next_page_token:
            if placeholder_page_next.button(f"Next ({sessionState.search.next_page_token})", use_container_width=True):
                sessionState.search.page_token = sessionState.search.next_page_token
                sessionState.search.start_search = True
                sessionState.search.current_page = sessionState.search.current_page + 1

                logger.info(f"Pagination: next {sessionState.search.next_page_token}")
                st.rerun()

    with tab_download:
        container_nav = st.container()
        with container_nav:
            column_max_results, column_existed_data = st.columns([1, 4])

            # number of results
            with column_max_results:
                max_results = st.number_input("Expected Results", value=sessionState.download.max_results, max_value=1000, help="Expected results to download. 0 to 1000.")

            # download button
            with column_existed_data:
                handle_file_upload(sessionState)
        
        container_results = st.container()
        with container_results:
            if st.button("DOWNLOAD", use_container_width=True):
                if not api_key:
                    st.error("Please enter your YouTube API key.")
                    logger.error("YouTube API key is empty.")
                    return
                
                if not query.strip():
                    st.error("Please enter a Query.")
                    logger.error("Query is empty.")
                    return

                logger.info("Download progress started.")

                # store to session
                sessionState.results_per_page = results_per_page
                sessionState.download.max_results = max_results

                # progress
                progress_bar = st.progress(0)
                progress_status = st.empty()

                # download creators
                download_creators(api_key, query, search_type, region_code, sessionState, progress_bar, progress_status)

                df = pd.DataFrame(
                    [
                        {
                            "Index": i,
                            "Channel Name": info["title"],
                            "Channel link": create_channel_link(info["channel_id"]),
                            "Email": info["email"]
                        }
                        for i, (info) in enumerate(sessionState.download.search_results, 1)
                    ]
                ).set_index("Index")

                logger.info("Download progress done.")

                # st.dataframe(
                #     data=df,
                #     height=max(35 * (len(df) + 1), 350),
                #     use_container_width=True
                # )

                # create excel file
                if not df.empty:
                    logger.info(f"Downloaded {df.size}.")
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, sheet_name=query, index=False)
                    excel_data = output.getvalue()

                    # provide download button for Excel file
                    now = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                    save_filename = f"{query}_{now}.xlsx"

                    st.download_button(
                        label=f"SAVE FILE ({save_filename})",
                        data=excel_data,
                        file_name=save_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )


if __name__ == "__main__":
    main()