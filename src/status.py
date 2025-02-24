from enum import Enum


class DownloadStatus(str, Enum):
    """
    Enum for the download status
    """

    QUEUED = "Queued"
    LINK_FOUND = "Link Found"
    FILE_ALREADY_EXISTS = "File Already Exists"
    SEARCH_FAILED = "Search Failed"
    DOWNLOAD_FAILED = "Download Failed"
    PROCESSING_COMPLETE = "Processing Complete"
    NO_LINK_FOUND = "No Link Found"
    STOPPED = "Stopped"
    COMPLETE = "Complete"
    RUNNING = "Running"  # Downloading
    ERROR = "Error"
    UNKNOWN = "Unknown"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
