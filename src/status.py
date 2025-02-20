from enum import Enum


class DownloadStatus(Enum):
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
    RUNNING = "Running"
    ERROR = "Error"
    UNKNOWN = "Unknown"
