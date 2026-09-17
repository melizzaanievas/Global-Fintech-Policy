# config.py - Jurisdiction Configuration & Dynamic Intelligence Mappings
# Contains direct official regulatory RSS feeds and entity-expanded search alias queries.

# 1. Direct Official Regulatory RSS Feeds
OFFICIAL_RSS_FEEDS = {
    # APAC
    "Hong Kong": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Hong Kong (SFC / HKMA)": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Hong Kong (SFC)": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Singapore": "https://www.mas.gov.sg/rss/feeds/press-releases.xml",
    "Singapore (MAS)": "https://www.mas.gov.sg/rss/feeds/press-releases.xml",
    "Japan": "https://www.fsa.go.jp/en/news/rss.xml",
    "Japan (FSA)": "https://www.fsa.go.jp/en/news/rss.xml",
    "South Korea": "https://www.fsc.go.kr/eng/rss.xml",
    "South Korea (FSC)": "https://www.fsc.go.kr/eng/rss.xml",
    "Australia": "https://asic.gov.au/about-asic/news-centre/rss/",
    "ASIC": "https://asic.gov.au/about-asic/news-centre/rss/",

    # Europe & UK
    "United Kingdom": "https://www.fca.org.uk/news/rss.xml",
    "UK FCA": "https://www.fca.org.uk/news/rss.xml",
    "FCA": "https://www.fca.org.uk/news/rss.xml",
    "European Union": "https://www.esma.europa.eu/rss.xml",
    "EU MiCA": "https://www.esma.europa.eu/rss.xml",
    "MiCA Regulation (EU-wide)": "https://www.esma.europa.eu/rss.xml",

    # Americas
    "United States": "https://www.sec.gov/rss/pressreleases.xml",
    "US SEC": "https://www.sec.gov/rss/pressreleases.xml",
    "SEC": "https://www.sec.gov/rss/pressreleases.xml",
    "Brazil": "https://www.bcb.gov.br/api/feeds/noticias",
    "Mexico": "https://www.banxico.org.mx/rss.xml",
    "Colombia": "https://www.superfinanciera.gov.co/feed",

    # Middle East & Africa
    "UAE": "https://www.vara.ae/en/rss.xml",
    "UAE (VARA / DIFC)": "https://www.vara.ae/en/rss.xml",
    "Bahrain": "https://www.cbb.gov.bh/rss.xml",
    "Nigeria": "https://sec.gov.ng/feed/",
    "Kenya": "https://www.centralbank.go.ke/feed/",
    "South Africa": "https://www.fsca.co.za/Pages/Feed.aspx",
    "Rwanda": "https://www.bnr.rw/feed/",
}

# 2. Entity-Expanded Search Queries (Used for Google News RSS Fallback)
JURISDICTION_ALIASES = {
    # APAC Hubs
    "Hong Kong": "Hong Kong OR HKMA OR SFC OR VATP OR ASPIRe OR OSL OR HashKey OR Stablecoin Sandbox OR AMLO",
    "Hong Kong (SFC / HKMA)": "Hong Kong OR HKMA OR SFC OR VATP OR ASPIRe OR OSL OR HashKey OR Stablecoin Sandbox OR AMLO",
    "Hong Kong (SFC)": "Hong Kong OR HKMA OR SFC OR VATP OR ASPIRe OR OSL OR HashKey OR Stablecoin Sandbox OR AMLO",
    "Singapore": "Singapore OR MAS OR Payment Services Act OR PSA OR Sygnum OR DBS Digital OR Coinhako OR Project Guardian",
    "Singapore (MAS)": "Singapore OR MAS OR Payment Services Act OR PSA OR Sygnum OR DBS Digital OR Coinhako OR Project Guardian",
    "Japan": "Japan OR FSA OR JSDA OR JVCEA OR Payment Services Act OR FIEA OR bitFlyer OR Coincheck OR SBI VC Trade",
    "Japan (FSA)": "Japan OR FSA OR JSDA OR JVCEA OR Payment Services Act OR FIEA OR bitFlyer OR Coincheck OR SBI VC Trade",
    "South Korea": "South Korea OR FSC OR FSS OR FIU OR Virtual Asset User Protection Act OR Upbit OR Bithumb OR Dunamu",
    "South Korea (FSC)": "South Korea OR FSC OR FSS OR FIU OR Virtual Asset User Protection Act OR Upbit OR Bithumb OR Dunamu",
    "Australia": "Australia OR ASIC OR AUSTRAC OR Treasury OR Digital Assets Framework OR CoinJar OR Independent Reserve",
    "ASIC": "Australia OR ASIC OR AUSTRAC OR Treasury OR Digital Assets Framework OR CoinJar OR Independent Reserve",

    # Americas
    "United States": "United States OR SEC OR CFTC OR OCC OR Treasury OR FinCEN OR FIT21 OR SAB 121 OR Coinbase OR Circle OR Ripple",
    "US SEC": "United States OR SEC OR CFTC OR OCC OR Treasury OR FinCEN OR FIT21 OR SAB 121 OR Coinbase OR Circle OR Ripple",
    "SEC": "United States OR SEC OR CFTC OR OCC OR Treasury OR FinCEN OR FIT21 OR SAB 121 OR Coinbase OR Circle OR Ripple",
    "Brazil": "Brazil OR Central Bank of Brazil OR BCB OR CVM OR Marco Legal dos Criptoativos OR Mercado Bitcoin OR Nubank",
    "Mexico": "Mexico OR Banxico OR CNBV OR Ley Fintech OR Bitso",
    "Colombia": "Colombia OR Superfinanciera OR SFC OR Sandbox Crypto OR Buda.com",

    # Europe & UK
    "United Kingdom": "UK OR United Kingdom OR FCA OR Bank of England OR HM Treasury OR FSMA OR Revolut OR Archax OR Zodia",
    "UK FCA": "UK OR United Kingdom OR FCA OR Bank of England OR HM Treasury OR FSMA OR Revolut OR Archax OR Zodia",
    "FCA": "UK OR United Kingdom OR FCA OR Bank of England OR HM Treasury OR FSMA OR Revolut OR Archax OR Zodia",
    "European Union": "European Union OR EU OR MiCA OR ESMA OR EBA OR ECB OR Transfer of Funds Regulation OR TFR",
    "EU MiCA": "European Union OR EU OR MiCA OR ESMA OR EBA OR ECB OR Transfer of Funds Regulation OR TFR",
    "MiCA Regulation (EU-wide)": "European Union OR EU OR MiCA OR ESMA OR EBA OR ECB OR Transfer of Funds Regulation OR TFR",

    # Middle East & Africa
    "UAE": "UAE OR Dubai OR Abu Dhabi OR VARA OR ADGM OR FSRA OR DIFC OR DFSA OR CBUAE OR M2 OR Rain",
    "UAE (VARA / DIFC)": "UAE OR Dubai OR Abu Dhabi OR VARA OR ADGM OR FSRA OR DIFC OR DFSA OR CBUAE OR M2 OR Rain",
    "Bahrain": "Bahrain OR CBB OR Central Bank of Bahrain OR Rain Financial OR CoinMENA",
    "Nigeria": "Nigeria OR SEC Nigeria OR CBN OR Central Bank of Nigeria OR Yellow Card OR Quidax",
    "Kenya": "Kenya OR CBK OR Central Bank of Kenya OR CMA Kenya OR Yellow Card OR M-Pesa Crypto",
    "South Africa": "South Africa OR FSCA OR SARB OR CASP Licensing OR Luno OR VALR",
    "Rwanda": "Rwanda OR BNR OR National Bank of Rwanda OR Digital Asset Regulation",
}
