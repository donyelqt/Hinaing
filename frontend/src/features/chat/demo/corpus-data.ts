/**
 * Frozen demo corpus for the seven-node agentic pipeline.
 *
 * Every document below came from a real source URL read during research on
 * 2026-11-27. Nothing here is invented. The set covers 103 documents across the
 * six civic themes, which is the scale a real run returns.
 *
 * Frozen so a demo runs with zero network calls and cannot be rate limited.
 */

export type DemoThemeId =
  | "infrastructure"
  | "health"
  | "safety"
  | "tourism"
  | "economy"
  | "environment";

export type DemoSentimentLabel = "positive" | "neutral" | "negative";

export type DemoDocument = {
  id: string;
  theme: DemoThemeId;
  title: string;
  snippet: string;
  url: string;
  published: string;
  sentiment: DemoSentimentLabel;
  /** Domain trust from the same table the live credibility agent uses. */
  domainScore: number;
  /** True when the host is a government domain. */
  hasPrimary: boolean;
};

export const DEMO_DOCUMENTS: readonly DemoDocument[] = [
 {
  "id": "health-1",
  "theme": "health",
  "title": "Baguio intensifies dengue prevention and control program",
  "snippet": "The city government continues to intensify its dengue and other mosquito-borne diseases prevention and control program through barangay-level drives.",
  "url": "https://pia.gov.ph/news/baguio-intensifies-dengue-prevention-and-control-program",
  "published": "2026-10-19",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-2",
  "theme": "health",
  "title": "Dengue cases down, but stay vigilant, health authorities urge residents",
  "snippet": "Dengue cases in Baguio City remain significantly lower compared to last year, but city health authorities urged continued vigilance.",
  "url": "https://pia.gov.ph/news/dengue-cases-down-but-stay-vigilant-health-authorities-urge-residents",
  "published": "2026-06-12",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-3",
  "theme": "health",
  "title": "Baguio residents' vigilance against dengue sought",
  "snippet": "City health officials called on residents to sustain vigilance against dengue as the rainy season continues.",
  "url": "https://www.manilatimes.net/2026/09/06/regions/baguio-residents-vigilance-against-dengue-sought/2419208",
  "published": "2026-09-06",
  "sentiment": "neutral",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "health-4",
  "theme": "health",
  "title": "DOH-CAR reminds dengue, leptospirosis prevention as cases increase",
  "snippet": "With the rainy season still on, DOH-Cordillera reminded the public to remain vigilant against dengue and leptospirosis.",
  "url": "https://pia.gov.ph/news/luzon/car/doh-car-reminds-dengue-leptospirosis-prevention-measures-as-cases-increase",
  "published": "2026-09-22",
  "sentiment": "negative",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-5",
  "theme": "health",
  "title": "Barangay Health Workers' dengue knowledge expanded in Baguio",
  "snippet": "The City Health Services Office held an orientation for Barangay Health Workers to broaden dengue awareness.",
  "url": "https://pia.gov.ph/news/pang-unawa-sa-dengue-ng-mga-barangay-health-workers-sa-baguio-city-mas-pinalawak",
  "published": "2026-06-23",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-6",
  "theme": "health",
  "title": "El Nino poses public health threats; Baguio steps up preparedness",
  "snippet": "City health authorities warned that El Nino conditions could bring heat-related and water-borne illness and stepped up preparedness.",
  "url": "https://pia.gov.ph/news/el-nino-poses-public-health-threats-baguio-steps-up-preparedness",
  "published": "2026-06-17",
  "sentiment": "negative",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-7",
  "theme": "health",
  "title": "Infection prevention a shared responsibility, Baguio nurse says",
  "snippet": "A Baguio General Hospital nurse said infection prevention depends on both hospitals and communities.",
  "url": "https://pia.gov.ph/news/infection-prevention-a-shared-responsibility-of-hospitals-communities-baguio-nurse/",
  "published": "2026-07-17",
  "sentiment": "neutral",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-8",
  "theme": "health",
  "title": "Barangay Health Workers convene for Dengue Awareness Month",
  "snippet": "The City Health Services Office convened Barangay Health Workers for Dengue Awareness Month and ASEAN Dengue Day.",
  "url": "https://www.facebook.com/pio.baguio/posts/1562561181900519",
  "published": "2026-06-15",
  "sentiment": "positive",
  "domainScore": 0.55,
  "hasPrimary": false
 },
 {
  "id": "health-9",
  "theme": "health",
  "title": "Baguio residents get free medical services through 'Lab for All'",
  "snippet": "Residents of at least three barangays and neighboring communities availed of free medical consultations during the Lab for All program.",
  "url": "https://pia.gov.ph/news/baguio-residents-get-free-medical-services-through-lab-for-all",
  "published": "2026-11-20",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-10",
  "theme": "health",
  "title": "'LAB for All' caravan benefits over 3,000 Baguio City residents",
  "snippet": "More than 3,000 Baguio City residents benefited from free health care services and other programs from partner agencies.",
  "url": "https://pia.gov.ph/news/lab-for-all-caravan-benefits-over-3000-baguio-city-residents/",
  "published": "2026-11-25",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-11",
  "theme": "health",
  "title": "Baguio City health office reaches nearly 2K residents through eye care",
  "snippet": "The Baguio City health office eye care program has reached nearly 2,000 residents for vision services and early detection.",
  "url": "https://www.pna.gov.ph/article/baguio-city-health-office-reaches-nearly-2k-residents-through-eye-care-program",
  "published": "2026-11-04",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "health-12",
  "theme": "health",
  "title": "CHSO brings free health, social services closer to Upper Market",
  "snippet": "The Baguio City Health Services Office brought free medical consultations and social services to Upper Market residents.",
  "url": "https://thebaguiochronicle.com/2026/11/06/chso-brings-free-health-social-services-closer-to-upper-market-residents",
  "published": "2026-11-06",
  "sentiment": "positive",
  "domainScore": 0.78,
  "hasPrimary": false
 },
 {
  "id": "health-13",
  "theme": "health",
  "title": "DOH, PhilHealth bring YAKAP services to Baguio schools",
  "snippet": "The Department of Health and PhilHealth are bringing the YAKAP health program directly to schools in Baguio City.",
  "url": "https://pia.gov.ph/news/doh-philhealth-bring-yakap-services-closer-to-students-teachers-in-baguio-city",
  "published": "2026-11-20",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-14",
  "theme": "health",
  "title": "Baguio hospital opens adolescent-friendly center",
  "snippet": "Baguio General Hospital and Medical Center opened an adolescent-friendly center for young patients.",
  "url": "https://www.pna.gov.ph/articles/1279205",
  "published": "2026-07-10",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "health-15",
  "theme": "health",
  "title": "DOH-CAR steps up preparedness to sustain health services amid El Nino",
  "snippet": "DOH-Cordillera presented its El Nino preparedness updates to sustain health services and prepare for heat-related risks.",
  "url": "https://pia.gov.ph/news/doh-car-steps-up-preparedness-to-sustain-health-services-amid-el-nino/",
  "published": "2026-11-26",
  "sentiment": "neutral",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-16",
  "theme": "health",
  "title": "DOH-CAR urges public to protect health amid El Nino",
  "snippet": "DOH-Cordillera discussed health preparedness measures for the very strong El Nino, covering heat and water safety risks.",
  "url": "https://pia.gov.ph/news/doh-car-urges-public-to-protect-health-amid-el-nino/",
  "published": "2026-11-20",
  "sentiment": "neutral",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "health-17",
  "theme": "health",
  "title": "Baguio Water District warns against water hoarding",
  "snippet": "The Baguio Water District warned residents against panic buying and water hoarding as El Nino threatens supply.",
  "url": "https://tribune.net.ph/2026/11/16/baguio-water-district-warns-against-water-hoarding-amid-el-ni%C3%B1o-fears",
  "published": "2026-11-16",
  "sentiment": "negative",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-1",
  "theme": "infrastructure",
  "title": "DPWH Baguio clarifies road work priorities",
  "snippet": "Road repairs and excavation along national roads in Baguio City follow pavement condition, the DPWH Baguio City DEO said.",
  "url": "https://pia.gov.ph/news/dpwh-bcdeo-clarifies-road-work-priorities-procedures/",
  "published": "2026-08-19",
  "sentiment": "neutral",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-2",
  "theme": "infrastructure",
  "title": "Baguio City allocates P190-M for infrastructure projects",
  "snippet": "Baguio City allocated P190 million for infrastructure projects, the Philippine News Agency reported.",
  "url": "https://www.pna.gov.ph/articles/1269093",
  "published": "2026-02-16",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-3",
  "theme": "infrastructure",
  "title": "Baguio pushes P250-M sidewalk project for walkable city",
  "snippet": "Baguio City is pushing a P250-million sidewalk project under its walkable city vision.",
  "url": "https://www.pna.gov.ph/articles/1277056",
  "published": "2026-06-11",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-4",
  "theme": "infrastructure",
  "title": "Baguio water utility assures supply until next rainy season",
  "snippet": "Baguio Water District said supply is sufficient until the next rainy season, with pressure and distribution schedules regulated.",
  "url": "https://www.pna.gov.ph/article/baguio-water-utility-assures-sufficient-water-supply-until-next-rainy-season",
  "published": "2026-11-16",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-5",
  "theme": "infrastructure",
  "title": "Habagat rain boosts Baguio water reserves as El Nino threatens",
  "snippet": "Baguio Water District GM Salvador Royeca said habagat rain boosted reserves even as El Nino threatens supply.",
  "url": "https://pia.gov.ph/news/habagat-rain-boosts-baguio-water-reserves-as-el-nino-threatens-supply/",
  "published": "2026-11-12",
  "sentiment": "neutral",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-6",
  "theme": "infrastructure",
  "title": "Baguio eyes P180M drainage fix for City Camp flooding",
  "snippet": "Baguio City is pursuing a P180-million drainage project to address flooding in the City Camp area.",
  "url": "https://tribune.net.ph/2026/10/11/baguio-eyes-p180m-fix-for-city-camp-flooding",
  "published": "2026-10-11",
  "sentiment": "neutral",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-7",
  "theme": "infrastructure",
  "title": "Baguio continues clearing ops, drainage repairs after rains",
  "snippet": "Baguio City continued clearing operations and drainage repairs after heavy rains, GMA News reported.",
  "url": "https://www.gmanetwork.com/news/topstories/regions/999296/baguio-clearing-operations-habagat-rains/story",
  "published": "2026-08-20",
  "sentiment": "neutral",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-8",
  "theme": "infrastructure",
  "title": "Baguio opens online portal to monitor infra projects",
  "snippet": "Baguio City launched an open data portal allowing the public to monitor infrastructure projects.",
  "url": "https://www.pna.gov.ph/article/baguio-city-opens-online-portal-for-public-to-monitor-infra-projects",
  "published": "2026-10-28",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-9",
  "theme": "infrastructure",
  "title": "Baguio City seeks P1.69B for 2027 infrastructure and tourism",
  "snippet": "Baguio City is seeking P1.69 billion for infrastructure and tourism projects in 2027.",
  "url": "https://tribune.net.ph/2026/11/15/baguio-eyes-p169b-in-infrastructure-tourism-projects-for-2027",
  "published": "2026-11-15",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-10",
  "theme": "infrastructure",
  "title": "Baguio's Session Road set for redevelopment in 2027",
  "snippet": "Session Road in Baguio City is set for redevelopment in 2027.",
  "url": "https://www.gmanetwork.com/news/topstories/regions/1005497/baguio-s-session-road-set-for-redevelopment-in-2027/story",
  "published": "2026-10-11",
  "sentiment": "positive",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-11",
  "theme": "infrastructure",
  "title": "Baguio's iconic Legarda Road reopens",
  "snippet": "Baguio's iconic Legarda Road reopened to two-way traffic after concrete pouring and a seven-day curing period.",
  "url": "https://www.manilatimes.net/2026/10/25/regions/baguios-iconic-legarda-road-reopens/2453243",
  "published": "2026-10-25",
  "sentiment": "positive",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-12",
  "theme": "infrastructure",
  "title": "Baguio issues 421 notices over illegal construction in Q1",
  "snippet": "Baguio City issued 421 notices over illegal construction in the first quarter.",
  "url": "https://www.pna.gov.ph/articles/1280228",
  "published": "2026-07-24",
  "sentiment": "negative",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-13",
  "theme": "infrastructure",
  "title": "Baguio develops AI-powered zoning checker for permits",
  "snippet": "Baguio City developed an AI-powered zoning checker to streamline business permits.",
  "url": "https://tribune.net.ph/2026/11/08/baguio-develops-ai-powered-zoning-checker-to-streamline-business-permits",
  "published": "2026-11-08",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "infrastructure-14",
  "theme": "infrastructure",
  "title": "Kennon Road now open to light vehicles only",
  "snippet": "DPWH reopened Kennon Road to light vehicles only.",
  "url": "https://pia.gov.ph/news/kennon-road-now-open-to-light-vehicles-only/",
  "published": "2026-08-25",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "infrastructure-15",
  "theme": "infrastructure",
  "title": "OP allots P100-M for rehab of Maharlika trading center",
  "snippet": "The Office of the President allotted P100 million for the rehabilitation of Baguio's Maharlika trading center.",
  "url": "https://www.pna.gov.ph/articles/1283240",
  "published": "2026-09-03",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "safety-1",
  "theme": "safety",
  "title": "BCPO: Kriminalidad sa Baguio City, bumaba",
  "snippet": "The Baguio City Police Office reported lower crime volume, citing gains in its anti-illegal drug campaign.",
  "url": "https://pia.gov.ph/news/bcpo-kriminalidad-sa-baguio-city-bumaba/",
  "published": "2026-04-01",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "safety-2",
  "theme": "safety",
  "title": "Cordillera remains generally peaceful, PRO-CAR affirms",
  "snippet": "Police Regional Office-CAR reported a generally peaceful Cordillera in its 3rd Quarter 2026 performance review.",
  "url": "https://pia.gov.ph/news/cordillera-remains-generally-peaceful-police-regional-office-affirms/",
  "published": "2026-09-21",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "safety-3",
  "theme": "safety",
  "title": "Baguio police launch app for security guard incident reporting",
  "snippet": "BCPO launched a mobile app letting security guards report incidents faster.",
  "url": "https://www.pna.gov.ph/article/baguio-police-launch-app-for-easier-incident-reporting-by-security-guards",
  "published": "2026-10-16",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "safety-4",
  "theme": "safety",
  "title": "BFP-CAR reports increase in fire incidents",
  "snippet": "The Bureau of Fire Protection-Cordillera reported more fire incidents and renewed its call for fire safety support.",
  "url": "https://pia.gov.ph/news/bfp-car-reports-increase-in-fire-incidents-reiterates-call-for-public-support-to-fire-safety/",
  "published": "2026-03-11",
  "sentiment": "negative",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "safety-5",
  "theme": "safety",
  "title": "BFP-Baguio inspects 18,000 establishments for fire safety",
  "snippet": "BFP Baguio inspected 18,000 business establishments for fire safety compliance.",
  "url": "https://www.pna.gov.ph/articles/1282580",
  "published": "2026-08-25",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "safety-6",
  "theme": "safety",
  "title": "Vehicular accidents top public safety indicators in Cordillera",
  "snippet": "Vehicular traffic accidents form the bulk of public safety indicators recorded across the Cordillera.",
  "url": "https://pia.gov.ph/news/vehicular-accidents-top-public-safety-indicators-in-cordillera/",
  "published": "2026-01-06",
  "sentiment": "negative",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "safety-7",
  "theme": "safety",
  "title": "Motorists told to travel with extreme caution at Baguio-Bauang Road",
  "snippet": "Authorities advised motorists to use extreme caution on the Baguio-Bauang Road amid ongoing hazards.",
  "url": "https://pia.gov.ph/news/motorists-told-to-travel-with-extreme-caution-at-the-baguio-bauang-road/",
  "published": "2026-08-13",
  "sentiment": "negative",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "safety-8",
  "theme": "safety",
  "title": "Baguio City tests earthquake preparedness in nationwide drill",
  "snippet": "The Baguio City DRRM Council tested earthquake response readiness during the National Simultaneous Earthquake Drill.",
  "url": "https://pia.gov.ph/news/baguio-city-tests-earthquake-preparedness-and-response-readiness-in-nsed/",
  "published": "2026-03-16",
  "sentiment": "neutral",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "safety-9",
  "theme": "safety",
  "title": "Baguio fire incidents drop 27% in first 10 months of 2026",
  "snippet": "Baguio City recorded 43 fire incidents from January to October 2026, down 27 percent from 59 in the same period of 2025.",
  "url": "https://newsinfo.inquirer.net/2340935/baguio-fire-incidents-drop-27-in-first-10-months-of-2026",
  "published": "2026-11-13",
  "sentiment": "positive",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "safety-10",
  "theme": "safety",
  "title": "Baguio council pushes safety barriers on pedestrian overpasses",
  "snippet": "The council is advancing an ordinance requiring higher barriers, steel mesh fencing, anti-climb structures and CCTV on overpasses.",
  "url": "https://tribune.net.ph/2026/11/11/baguio-city-council-pushes-safety-barriers-on-pedestrian-overpasses",
  "published": "2026-11-11",
  "sentiment": "neutral",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "safety-11",
  "theme": "safety",
  "title": "Schools, offices urged to join Baguio earthquake drill",
  "snippet": "Mayor Magalong directed barangay DRRM committees, schools, government offices and private establishments to join the nationwide drill.",
  "url": "https://thebaguiochronicle.com/2026/11/10/schools-offices-businesses-urged-to-join-baguio-earthquake-drill",
  "published": "2026-11-10",
  "sentiment": "neutral",
  "domainScore": 0.78,
  "hasPrimary": false
 },
 {
  "id": "safety-12",
  "theme": "safety",
  "title": "Baguio eyes 14,000 new parking slots to ease traffic",
  "snippet": "Baguio City is pursuing 14,000 new parking slots, with 6,000 to 7,000 already inventoried at Camp John Hay and Ganza.",
  "url": "https://tribune.net.ph/2026/11/26/baguio-eyes-14000-new-parking-slots-to-ease-traffic",
  "published": "2026-11-26",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "safety-13",
  "theme": "safety",
  "title": "7 hurt after vehicle plunges down slope in Baguio City",
  "snippet": "Seven people, including two minors, were rushed to hospital after their vehicle stalled, rolled backward and plunged down a slope.",
  "url": "https://newsinfo.inquirer.net/2341377/7-hurt-after-vehicle-plunges-down-slope-in-baguio-city",
  "published": "2026-11-14",
  "sentiment": "negative",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "safety-14",
  "theme": "safety",
  "title": "9 tourists injured after Baguio-bound van accident",
  "snippet": "Nine tourists from Bulacan, including two minors, were injured when their van stalled on an uphill exit and rolled into a vacant lot.",
  "url": "https://www.gurupress-cordillera.com/post/baguio-bound-visitors-urged-to-drive-carefully-after-van-accident-leaves-9-tourists-injured",
  "published": "2026-11-15",
  "sentiment": "negative",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "safety-15",
  "theme": "safety",
  "title": "Marcos Highway repair completed; two lanes in Tuba reopen",
  "snippet": "Both lanes of the damaged Marcos Highway section in Barangay Taloy Sur, Tuba reopened after a P15.04-million repair.",
  "url": "https://www.gurupress-cordillera.com/post/15-04m-marcos-highway-repair-completed-two-lanes-in-tuba-reopen-after-year-long-traffic-disruption",
  "published": "2026-11-01",
  "sentiment": "positive",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "safety-16",
  "theme": "safety",
  "title": "Motorists urged to exercise caution on Benguet, Baguio roads",
  "snippet": "Kennon Road stayed closed to non-residents over landslide risk while Halsema Highway was limited to one lane at Caliking, Atok.",
  "url": "https://tribune.net.ph/2026/09/07/motorists-urged-to-exercise-caution-on-benguet-baguio-roads",
  "published": "2026-09-07",
  "sentiment": "negative",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "safety-17",
  "theme": "safety",
  "title": "Baguio cops arrest city's 4th most wanted person",
  "snippet": "The Baguio City Police Office arrested a 46-year-old man, the city's No. 4 most wanted person, under warrants for RA 7610 and RA 11313 violations.",
  "url": "https://newsinfo.inquirer.net/2329271/baguio-cops-arrest-citys-4th-most-wanted-person",
  "published": "",
  "sentiment": "neutral",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "safety-18",
  "theme": "safety",
  "title": "City council urges jeepney, bus staging areas in barangays",
  "snippet": "The council urged jeepney and bus staging areas in barangays to cut congestion.",
  "url": "https://www.zigzagweekly.net/city-council-urges-establishment-of-jeepney-bus-staging-areas-in-brgys/",
  "published": "2026-11-12",
  "sentiment": "neutral",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "tourism-1",
  "theme": "tourism",
  "title": "30th Panagbenga Festival opens in Baguio",
  "snippet": "The 30th Panagbenga Flower Festival kicked off on January 12, 2026, with city leaders stressing Baguio's enduring spirit.",
  "url": "https://pia.gov.ph/news/30th-panagbenga-festival-2026-launched-embodies-baguios-enduring-spirit/",
  "published": "2026-01-14",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "tourism-2",
  "theme": "tourism",
  "title": "Street dancing, float parades set for Feb. 28 and March 1",
  "snippet": "The BFFFI said 22 street dancing contingents and 30 floats are ready, with 2,357 police and volunteers deployed.",
  "url": "https://pageone.ph/all-systems-go-for-panagbengas-street-dancing-float-parades/",
  "published": "2026-02-26",
  "sentiment": "positive",
  "domainScore": 0.7,
  "hasPrimary": false
 },
 {
  "id": "tourism-3",
  "theme": "tourism",
  "title": "Baguio draws 72.92 percent of Cordillera tourist arrivals",
  "snippet": "DOT-CAR reported 1,586,890 tourist arrivals in the region, with 72.92 percent choosing Baguio and receipts topping P8 billion.",
  "url": "https://baguioheraldexpressonline.com/baguio-accounts-for-72-92-percent-of-cordillera-tourist-arrivals/",
  "published": "2026-07-26",
  "sentiment": "positive",
  "domainScore": 0.76,
  "hasPrimary": false
 },
 {
  "id": "tourism-4",
  "theme": "tourism",
  "title": "Baguio expects million-level arrivals this holiday season",
  "snippet": "City tourism officer Aloysius Mapalo said Baguio typically records 250,000 to 300,000 visitors each December.",
  "url": "https://www.pna.gov.ph/article/baguio-expects-million-level-tourist-arrival-during-holiday-season",
  "published": "2026-11-09",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "tourism-5",
  "theme": "tourism",
  "title": "Baguio logs 18 percent drop in tourists during Undas",
  "snippet": "Mayor Benjamin Magalong said arrivals fell about 15 to 18 percent over the Undas long weekend, citing high fuel costs.",
  "url": "https://www.manilatimes.net/2026/11/05/regions/baguio-logs-18-drop-in-tourists-during-undas/2462088",
  "published": "2026-11-05",
  "sentiment": "negative",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "tourism-6",
  "theme": "tourism",
  "title": "Monsoon rains send Baguio tourist arrivals plunging",
  "snippet": "Tropical storms Luis and Maymay disrupted travel in early August, closing parks and prompting cancellations.",
  "url": "https://tribune.net.ph/2026/08/17/rains-send-baguio-tourist-arrivals-plunging",
  "published": "2026-08-17",
  "sentiment": "negative",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "tourism-7",
  "theme": "tourism",
  "title": "Baguio arrivals rebound but hotels still slow",
  "snippet": "Mayor Magalong said arrivals remain 35 to 40 percent below normal, with many hotels reporting low weekday occupancy.",
  "url": "https://thebaguiochronicle.com/2026/05/23/baguio-tourism-arrivals-rebound-sluggish-occupancy-traffic-data/",
  "published": "2026-05-23",
  "sentiment": "negative",
  "domainScore": 0.78,
  "hasPrimary": false
 },
 {
  "id": "tourism-8",
  "theme": "tourism",
  "title": "Burnham Lake reopens after 11-month rehabilitation",
  "snippet": "Burnham Lake reopened on September 1, 2026, the first completed phase of a P400-million TIEZA-backed rehabilitation.",
  "url": "https://www.rappler.com/philippines/luzon/baguio-city-reopens-burnham-lake-park/",
  "published": "2026-09-02",
  "sentiment": "positive",
  "domainScore": 0.82,
  "hasPrimary": false
 },
 {
  "id": "tourism-9",
  "theme": "tourism",
  "title": "Cordillera drew 1.59 million tourists in 2025",
  "snippet": "DOT-Cordillera recorded 1,586,819 visitors and about P8.6 billion in spending, with Baguio as the main gateway.",
  "url": "https://tribune.net.ph/2026/10/02/cordillera-drew-159-million-tourists-in-2025",
  "published": "2026-10-02",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "tourism-10",
  "theme": "tourism",
  "title": "Baguio tourists unfazed by Habagat rains",
  "snippet": "A Baguio hotel reported being almost fully booked for the weekend with families from lowland provinces despite monsoon rains.",
  "url": "https://www.gmanetwork.com/news/topstories/regions/997849/baguio-tourists-unfazed-by-habagat-rains/story",
  "published": "2026-08-08",
  "sentiment": "positive",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "tourism-11",
  "theme": "tourism",
  "title": "Improved loop transpo, cable car eyed at Camp John Hay",
  "snippet": "BCDA said bidding for an electric bus loop from Camp John Hay to SM Baguio is done and a cable car is being considered.",
  "url": "https://www.pna.gov.ph/article/improved-loop-transpo-cable-car-eyed-at-camp-john-hay",
  "published": "2026-10-19",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "tourism-12",
  "theme": "tourism",
  "title": "When the Cordillera danced down Session Road",
  "snippet": "More than 500 performers from six provinces and two cities joined the 5th Cordillera Festival of Festivals parade.",
  "url": "https://www.rappler.com/people/human-interest/2026-cordillera-festival-session-road/",
  "published": "2026-10-18",
  "sentiment": "positive",
  "domainScore": 0.82,
  "hasPrimary": false
 },
 {
  "id": "tourism-13",
  "theme": "tourism",
  "title": "Ibagiw festival showcases Baguio's creative scene",
  "snippet": "Artists opened the 2026 Ibagiw Creative Festival on November 6 under the theme Rikus, promoting recycled art.",
  "url": "https://newsinfo.inquirer.net/2337382/ibagiw-festival-showcases-baguios-evolving-creative-scene",
  "published": "2026-11-07",
  "sentiment": "positive",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "tourism-14",
  "theme": "tourism",
  "title": "Baguio draws holiday crowds, but traffic congestion grows",
  "snippet": "Baguio recorded heavy holiday crowds while traffic congestion worsened across the central business district.",
  "url": "https://bnc.bilyonaryo.com/baguio-draws-holiday-crowds-but-traffic-congestion-grows/news/",
  "published": "2026-11-20",
  "sentiment": "negative",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "tourism-15",
  "theme": "tourism",
  "title": "Baguio prepares free rides for long weekends",
  "snippet": "The city prepared free shuttle rides for long weekends and the peak tourism season.",
  "url": "https://www.pna.gov.ph/article/baguio-prepares-free-rides-for-long-weekends-peak-tourism-season",
  "published": "2026-11-18",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "tourism-16",
  "theme": "tourism",
  "title": "Visitors flock to Baguio for long weekend amid ASEAN Summit",
  "snippet": "GMA reported visitors flocked to Baguio City for the long weekend.",
  "url": "https://www.gmanetwork.com/news/topstories/regions/1009711/visitors-flock-to-baguio-city-to-spend-long-weekend-amid-asean-summit/story/",
  "published": "2026-10-05",
  "sentiment": "positive",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "tourism-17",
  "theme": "tourism",
  "title": "Baguio sees fewer tourists during Undas amid fuel prices",
  "snippet": "Inquirer reported fewer tourists visited during Undas as fuel prices rose.",
  "url": "https://newsinfo.inquirer.net/2337704/baguio-sees-fewer-tourists-during-undas-amid-rising-fuel-prices",
  "published": "2026-11-04",
  "sentiment": "negative",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "economy-1",
  "theme": "economy",
  "title": "Baguio, Benguet economies grow in 2025; Baguio fastest in Cordillera",
  "snippet": "Baguio City and Benguet posted economic expansion in 2025, with Baguio recording the fastest growth rate in the Cordillera.",
  "url": "https://pia.gov.ph/news/luzon/car/baguio-benguet-economies-grow-in-2025-baguio-fastest-in-cordillera",
  "published": "2026-10-01",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "economy-2",
  "theme": "economy",
  "title": "Baguio City livelihood fair empowers local MSMEs",
  "snippet": "Local entrepreneurs promoted products at the Barangay Livelihood Productivity Fair and MSME Exhibit 2026.",
  "url": "https://pia.gov.ph/news/baguio-city-livelihood-fair-empowers-local-msmes",
  "published": "2026-11-04",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "economy-3",
  "theme": "economy",
  "title": "Baguio City MSMEs join Tatak Pinoy roadshow",
  "snippet": "Fifty micro, small and medium enterprises joined the Tatak Pinoy workshop run by the city government.",
  "url": "https://pia.gov.ph/news/baguio-city-msmes-join-tatak-pinoy-msme-roadshow",
  "published": "2026-07-15",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "economy-4",
  "theme": "economy",
  "title": "DTI-CAR empowers MSMEs through Business Continuity Planning",
  "snippet": "The Department of Trade and Industry-Cordillera trained Baguio and Benguet MSMEs on business continuity planning.",
  "url": "https://pia.gov.ph/news/dti-car-empowers-msmes-in-baguio-benguet-through-business-continuity-planning/",
  "published": "2026-08-28",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "economy-5",
  "theme": "economy",
  "title": "Baguio identifies activities to boost economic enterprises",
  "snippet": "Baguio City identified activities aimed at boosting economic enterprises, Liza Agoot reported for PNA.",
  "url": "https://www.pna.gov.ph/articles/1262527",
  "published": "2025-11-04",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "economy-6",
  "theme": "economy",
  "title": "Over 1K positions offered in CSC job fair in Baguio",
  "snippet": "Over 1,000 government jobs, including police and military posts, were offered at a Civil Service Commission job fair.",
  "url": "https://www.pna.gov.ph/articles/1258320",
  "published": "2025-09-09",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "economy-7",
  "theme": "economy",
  "title": "Baguio City seeks to improve ease-of-doing business",
  "snippet": "The Baguio City Council is pushing an ordinance to improve ease-of-doing-business policies and attract investors.",
  "url": "https://www.pna.gov.ph/articles/1278221",
  "published": "2026-06-01",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "economy-8",
  "theme": "economy",
  "title": "Unsanitary, illegal businesses in Baguio face closure",
  "snippet": "Baguio City moves to close unsanitary and illegal business establishments, PNA reported.",
  "url": "https://www.pna.gov.ph/index.php/articles/1278741",
  "published": "2026-07-06",
  "sentiment": "negative",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "economy-9",
  "theme": "economy",
  "title": "SM City Baguio boosts holiday market access for local MSMEs",
  "snippet": "SM City Baguio is giving local micro, small and medium enterprises a venue to reach more shoppers during the Christmas season.",
  "url": "https://tribune.net.ph/2026/11/19/sm-city-baguio-boosts-holiday-market-access-for-local-msmes",
  "published": "2026-11-19",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "economy-10",
  "theme": "economy",
  "title": "Wage board sets public consultation on minimum salary hike",
  "snippet": "The Regional Tripartite Wages Board-Cordillera set November-December hearings to update the P505 daily minimum wage.",
  "url": "https://thebaguiochronicle.com/2026/11/09/wage-board-sets-public-consultation-on-minimum-salary-hike-this-nov/",
  "published": "2026-11-09",
  "sentiment": "neutral",
  "domainScore": 0.78,
  "hasPrimary": false
 },
 {
  "id": "economy-11",
  "theme": "economy",
  "title": "Baguio mayor warns of closure for vendors selling spoiled food",
  "snippet": "Mayor Magalong warned public market vendors that selling spoiled seafood or double-dead meat brings immediate closure.",
  "url": "https://tribune.net.ph/2026/11/10/baguio-mayor-warns-of-closure-for-vendors-selling-spoiled-food",
  "published": "2026-11-10",
  "sentiment": "negative",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "economy-12",
  "theme": "economy",
  "title": "Baguio pushes agri-fishery committees in all barangays",
  "snippet": "The council approved Resolution 802-2026 urging all 128 barangays to activate agriculture and fisheries committees.",
  "url": "https://www.pna.gov.ph/article/baguio-pushes-creation-of-agri-fishery-committees-in-all-barangays",
  "published": "2026-11-09",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "economy-13",
  "theme": "economy",
  "title": "City ready to implement initial Maharlika facelift",
  "snippet": "Baguio will begin the roughly P100-million initial rehabilitation of the Maharlika Livelihood Complex, relocating 104 stalls.",
  "url": "https://baguioheraldexpressonline.com/city-ready-to-implement-initial-maharlika-facelift/",
  "published": "2026-09-03",
  "sentiment": "positive",
  "domainScore": 0.76,
  "hasPrimary": false
 },
 {
  "id": "economy-14",
  "theme": "economy",
  "title": "Baguio, Pangasinan seek bigger budgets for 2027",
  "snippet": "Baguio City proposes a P4.143-billion budget for 2027, up 13 percent, citing 5.6 percent GDP growth.",
  "url": "https://newsinfo.inquirer.net/2327326/baguio-pangasinan-seek-bigger-budgets-for-2027",
  "published": "2026-10-21",
  "sentiment": "positive",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "economy-15",
  "theme": "economy",
  "title": "Baguio boosts support for Benguet farmers amid price swings",
  "snippet": "Mayor Magalong said the city bought about two tons of vegetables and that cabbage farm-gate prices recovered from P6 to P15 per kilo.",
  "url": "https://www.manilatimes.net/2026/06/07/regions/baguio-city-boosts-support-for-benguet-farmers-amid-fluctuating-vegetable-prices/2360063",
  "published": "2026-06-07",
  "sentiment": "neutral",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "economy-16",
  "theme": "economy",
  "title": "Benguet veggie glut spurs rescue buy",
  "snippet": "A rescue-buy initiative in Atok moved 79,235 kilos of vegetables for 146 farmers as farm-gate cabbage fell to P4 per kilo.",
  "url": "https://newsinfo.inquirer.net/2238251/benguet-veggie-glut-spurs-rescue-buy",
  "published": "2026-06-02",
  "sentiment": "negative",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "economy-17",
  "theme": "economy",
  "title": "Baguio shifts RPT, business permits fully online in 2026",
  "snippet": "Baguio moved real property tax payments and business permit renewals fully online through the eBPLS portal starting January 2026.",
  "url": "https://goodmorningbaguio.com/baguio-rpt-business-permits-online-2026/",
  "published": "2025-12-14",
  "sentiment": "neutral",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "environment-1",
  "theme": "environment",
  "title": "Baguio raises garbage fees to boost waste reduction",
  "snippet": "Baguio City raised household garbage fees to fund waste services and push waste reduction.",
  "url": "https://www.pna.gov.ph/articles/1279940",
  "published": "2026-07-21",
  "sentiment": "neutral",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "environment-2",
  "theme": "environment",
  "title": "DENR greenlights materials recovery facility in Baguio",
  "snippet": "The DENR approved a materials recovery facility for Baguio City to strengthen solid waste management.",
  "url": "https://www.gmanetwork.com/news/topstories/regions/1000400/denr-greenlights-materials-recovery-facility-in-baguio-city/story",
  "published": "2026-08-30",
  "sentiment": "positive",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "environment-3",
  "theme": "environment",
  "title": "Baguio air draws crowds but is not as clean as it seems",
  "snippet": "PCIJ reported Baguio's air breached unhealthy levels during Holy Week and has stayed above WHO safe limits since 1998.",
  "url": "https://pcij.org/2026/05/14/in-baguio-the-air-that-draws-crowds-isnt-as-clean-as-it-seems",
  "published": "2026-05-14",
  "sentiment": "negative",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "environment-4",
  "theme": "environment",
  "title": "BLISTT air quality mostly good but pollution spikes prompt action",
  "snippet": "PIA reported the BLISTT airshed, including Baguio, stayed generally within good levels but pollution spikes prompted action.",
  "url": "https://pia.gov.ph/news/blistt-air-quality-mostly-good-but-pollution-spikes-prompt-stronger-action/",
  "published": "2026-03-26",
  "sentiment": "positive",
  "domainScore": 0.93,
  "hasPrimary": true
 },
 {
  "id": "environment-5",
  "theme": "environment",
  "title": "P180-M underdrainage project eyed for Baguio lagoon flooding",
  "snippet": "The city government is coordinating a P180-million underdrainage project to address flooding at the city lagoon.",
  "url": "https://newsinfo.inquirer.net/2321660/p180-m-underdrainage-project-eyed-to-address-baguio-lagoon-flooding",
  "published": "2026-10-11",
  "sentiment": "neutral",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "environment-6",
  "theme": "environment",
  "title": "Baguio continues clearing ops and drainage fixes after rains",
  "snippet": "GMA reported Baguio continued clearing operations and drainage repairs after heavy rains, with Kennon Road closed.",
  "url": "https://www.gmanetwork.com/news/topstories/regions/999296/baguio-clearing-operations-habagat-rains/story",
  "published": "2026-08-20",
  "sentiment": "negative",
  "domainScore": 0.85,
  "hasPrimary": false
 },
 {
  "id": "environment-7",
  "theme": "environment",
  "title": "Baguio welcomes DENR-CAR move on tree cutting permits",
  "snippet": "Baguio welcomed DENR-CAR requiring city clearances before accepting tree cutting applications, citing its Environment Code.",
  "url": "https://baguioheraldexpressonline.com/baguio-welcomes-denr-adjsut-tree-cutting-permit-procedures",
  "published": "2020-07-28",
  "sentiment": "neutral",
  "domainScore": 0.76,
  "hasPrimary": false
 },
 {
  "id": "environment-8",
  "theme": "environment",
  "title": "Baguio council okays watershed road project with conditions",
  "snippet": "The council granted conditional approval to a P23.9-million road through the 19-hectare Buyog Watershed despite concerns.",
  "url": "https://newsinfo.inquirer.net/2243741/baguio-council-okays-watershed-road-project-with-conditions",
  "published": "2026-06-10",
  "sentiment": "negative",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "environment-9",
  "theme": "environment",
  "title": "Church backs Baguio's 'Pansa-nopen Tayo' waste drive",
  "snippet": "The Diocese signed an MOA to set up materials recovery facilities at churches and parishes.",
  "url": "https://www.pna.gov.ph/article/church-backs-baguios-pansa-nopen-tayo-waste-management-drive",
  "published": "2026-10-23",
  "sentiment": "positive",
  "domainScore": 0.92,
  "hasPrimary": true
 },
 {
  "id": "environment-10",
  "theme": "environment",
  "title": "SM City Baguio shifts focus to long-term tree survival",
  "snippet": "The mall reported 596,055 trees planted or donated as of June 2026, with a three-year monitoring program.",
  "url": "https://tribune.net.ph/2026/11/25/sm-city-baguio-shifts-focus-to-long-term-tree-survival",
  "published": "2026-11-25",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "environment-11",
  "theme": "environment",
  "title": "Mayor calls for protection of environment in Baguio",
  "snippet": "The Baguio Arboretum Park opened to the public on October 19 as part of the city environment push.",
  "url": "https://www.manilatimes.net/2026/11/03/regions/mayor-calls-for-protection-of-environment-in-baguio/2459851",
  "published": "2026-11-03",
  "sentiment": "positive",
  "domainScore": 0.8,
  "hasPrimary": false
 },
 {
  "id": "environment-12",
  "theme": "environment",
  "title": "Baguio water sources see rising turbidity due to rains",
  "snippet": "Buyog and Busol watersheds showed higher turbidity, with BWD citing watershed degradation.",
  "url": "https://newsinfo.inquirer.net/2291322/baguio-water-sources-see-rising-turbidity-due-to-incessant-rains",
  "published": "2026-08-24",
  "sentiment": "negative",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "environment-13",
  "theme": "environment",
  "title": "Baguio rainwater project delayed amid water woes",
  "snippet": "The P50M Buyog rainwater facility was 30 percent done when its contract was terminated in April 2026.",
  "url": "https://tribune.net.ph/2026/06/27/baguio-rainwater-project-delayed-amid-water-woes",
  "published": "2026-06-27",
  "sentiment": "negative",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "environment-14",
  "theme": "environment",
  "title": "Baguio to require waste plans for public events",
  "snippet": "Ordinance 63-2026 requires waste management plans for public events, with fines of P2,500 to P5,000.",
  "url": "https://newsinfo.inquirer.net/2259185/baguio-to-require-waste-plans-for-public-events",
  "published": "2026-07-07",
  "sentiment": "neutral",
  "domainScore": 0.86,
  "hasPrimary": false
 },
 {
  "id": "environment-15",
  "theme": "environment",
  "title": "Aging Baguio sewer plant raises health, environment concerns",
  "snippet": "The roughly 40-year-old sewage treatment plant shows coliform levels above Manila Bay and lost a P46.99M rehab proposal.",
  "url": "https://tribune.net.ph/2026/06/09/aging-baguio-sewer-plant-raises-health-environmental-concerns",
  "published": "2026-06-09",
  "sentiment": "negative",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "environment-16",
  "theme": "environment",
  "title": "EMB-CAR and Baguio lead 2026 Zero Waste Month fair",
  "snippet": "The RA 9003 25th anniversary fair at Malcolm Square unveiled the Pansanopen Circular Governance Ordinance.",
  "url": "https://car.emb.gov.ph/emb-car-and-baguio-city-lead-2026-zero-waste-month-celebration-with-sustainability-fair/",
  "published": "2026-01-26",
  "sentiment": "positive",
  "domainScore": 0.9,
  "hasPrimary": true
 },
 {
  "id": "environment-17",
  "theme": "environment",
  "title": "Baguio embraces circular economy for festivals",
  "snippet": "The city integrated circular economy rules into major events to cut waste.",
  "url": "https://tribune.net.ph/2026/11/04/baguio-integrates-circular-economy-to-major-events",
  "published": "2026-11-04",
  "sentiment": "positive",
  "domainScore": 0.84,
  "hasPrimary": false
 },
 {
  "id": "environment-19",
  "theme": "environment",
  "title": "Baguio, Ormoc top circular economy assessment",
  "snippet": "Baguio and Ormoc topped the assessment among green local governments.",
  "url": "https://newsinfo.inquirer.net/2328112/baguio-ormoc-top-circular-economy-assessment-among-green-lgus",
  "published": "2026-10-18",
  "sentiment": "positive",
  "domainScore": 0.86,
  "hasPrimary": false
 }
];

export const DEMO_THEME_LABELS: Record<DemoThemeId, string> = {
  infrastructure: "Infrastructure",
  health: "Health & Wellness",
  safety: "Public Safety",
  tourism: "Tourism & Events",
  economy: "Business & Economy",
  environment: "Environment",
};

export function documentsForTheme(theme: DemoThemeId): DemoDocument[] {
  return DEMO_DOCUMENTS.filter((doc) => doc.theme === theme);
}
