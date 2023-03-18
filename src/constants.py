from pathlib import Path

MAIN_DOC_URL = "https://docs.python.org/3/"
PEP_URL = "https://peps.python.org/"
BASE_DIR = Path(__file__).parent
DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DT_FORMAT = "%d.%m.%Y %H:%M:%S"

EXPECTED_STATUS = {
    "A": ("Active", "Accepted"),
    "D": ("Deferred",),
    "F": ("Final",),
    "P": ("Provisional",),
    "R": ("Rejected",),
    "S": ("Superseded",),
    "W": ("Withdrawn",),
    "": ("Draft", "Active"),
}

DIV_TAG = "div"
ID = "id"
CLASS = "class"
UL_TAG = "ul"
A_TAG = "a"
TABLE_TAG = "table"
HREF_TAG = "href"
DL_TAG = "dl"
H1_TAG = "h1"
ABBR_TAG = "abbr"

SECTION_TAG = "section"

WHATSNEW_ID = "what-s-new-in-python"
TOCTREE_CLASS = "toctree-wrapper"
LATEST_VER_CLASS = "sphinxsidebarwrapper"
DOWNLOAD_CLASS = "docutils"
DOWNLOAD_ROLE = "main"
PEP_ID = "numerical-index"
PEP_CLASS = "rfc2822 field-list simple"
