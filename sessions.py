import streamlit as st


class SessionState:
    class _SessionState:
        def __init__(self):
            self.api_key = ''
            self.query = ''
            self.search_type = 'channel'
            self.results_per_page = 50
            
            # search
            self.search = SessionState.SessionSearch()

            # download
            self.download = SessionState.SessionDownload()

    class SessionSearch:
        def __init__(self):
            self.start_search = False
            self.page_info = {}
            self.next_page_token = None
            self.prev_page_token = None
            self.page_token = None
            self.current_page = 1

    class SessionDownload:
        def __init__(self):
            self.max_results = 500
            self.uploaded_files = []
            self.uploaded_results = {}

            self.page_info = {}
            self.page_token = None

            self.search_results = []
            self.playlist_info = {}

    def __init__(self):
        if '_state' not in st.session_state:
            st.session_state._state = self._SessionState()
        self._state = st.session_state._state

        # ensure all attributes are present in the session state
        for attr, value in vars(self._SessionState()).items():
            if not hasattr(self._state, attr):
                setattr(self._state, attr, value)

    def __getattr__(self, name):
        # return getattr(self._state, name)
        if hasattr(self._state, name):
            return getattr(self._state, name)
        elif name == 'download' and hasattr(self._state, 'download'):
            return self._state.download
        elif name == 'search' and hasattr(self._state, 'search'):
            return self._state.search
        else:
            raise AttributeError(f"'SessionState' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name == '_state':
            super().__setattr__(name, value)
        elif name in ['download', 'search']:
            setattr(self._state, name, value)
        elif hasattr(self._state, 'download') and name in vars(self._state.download):
            setattr(self._state.download, name, value)
        elif hasattr(self._state, 'search') and name in vars(self._state.search):
            setattr(self._state.search, name, value)
        else:
            setattr(self._state, name, value)

    def clear_all(self):
        self._state = self._SessionState()
        st.session_state._state = self._state

    def clear_pagination(self):
        self._state.search.page_info = {}
        self._state.search.next_page_token = None
        self._state.search.prev_page_token = None
        self._state.search.page_token = None
        self._state.search.current_page = 1

    def add_file(self, file_name, data):
        if file_name not in self._state.download.uploaded_files:
            self._state.download.uploaded_files.append(file_name)
            self._state.download.uploaded_results[file_name] = data

    def remove_file(self, file_name):
        if file_name in self._state.download.uploaded_files:
            self._state.download.uploaded_files.remove(file_name)
            self._state.download.uploaded_results.pop(file_name, None)

    def clear_download_results(self):
        self._state.download.search_results = []