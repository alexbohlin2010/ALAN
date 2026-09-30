# Space-based / imagery-derived evidence on night-light colour, CCT and lamp type

Compiled 2026-09-25. Evidence levels used below:
- **[L]** = I loaded the page (abstract, full text or official page).
- **[S]** = snippet-only. I saw it in search results but did not load the full text. Treat numbers as unverified.
- **[P]** = press or outreach material, not peer-reviewed.

ScienceDirect, MDPI, Taylor & Francis, Springer and Wiley pages returned HTTP 403, so most SDGSAT-1 paper details are [S]. Per-city LED percentages were not visible in any snippet I saw, so none are reported here.

---

## 1. Datasets overview

| Dataset / platform | Spectral info | Resolution | Temporal coverage | Access terms | Lamp-type / CCT capability shown in literature |
|---|---|---|---|---|---|
| **SDGSAT-1 Glimmer Imager (GLI)**, CBAS / CAS. Launched 5 Nov 2021 (the eoPortal page says Nov 2021; one press snippet gives 29 Nov). | Blue 424–526 nm, Green 505–612 nm, Red 600–894 nm (the red band includes NIR). Panchromatic 444–910 nm. [L, eoPortal; S, MDPI pansharpening paper doi:10.3390/rs16020245] | RGB 40 m, PAN 10 m, 300 km swath [L, eoPortal] | Imaging since early 2022. 11-day repeat cycle. Sun-synchronous orbit at 505 km, descending node at about 10:00, so night imaging falls on the ascending pass, roughly 21:30–22:00 local (my inference). Scenes are tasked, so coverage is not systematic. | Free for scientific research through the SDGSAT-1 Open Science Program (https://www.sdgsat.ac.cn/). International users apply with a research proposal. Use is for scientific research only and products must credit SDGSAT-1 [S, "Regulations of the Use of SDGSAT-1 Data" PDF, sdgsat.ac.cn, 2022-09-20]. eoPortal says Level-4 products are "freely accessible globally" and the Open Science Programme started Sept 2022 [L]. By 2025, users in 88 countries had received data [S]. CAS also released a 10 m night-light atlas of 147 cities in 105 countries [S]. | Yes. LED vs HPS classification at about 80–95% overall accuracy. White LED / red LED / other classes. B/G and G/R ratios. See §2. |
| **ISS astronaut DSLR photography** (NASA Gateway to Astronaut Photography, eol.jsc.nasa.gov; the "Cities at Night" citizen-science project; ESA NightPod tracking mount from 2012) | Camera RGB (Bayer). Calibrated to B/G and G/R colour ratios and to indices such as the melatonin suppression index (MSI), star light index (SLI) and induced photosynthesis index (IPI). Method: Sánchez de Miguel et al. 2019 RSE 224:92–103 [S]; calibration pipeline: Sánchez de Miguel et al. 2021 RSE, doi:10.1016/j.rse.2021.112611 [L, arXiv 2108.07050] | Roughly 5–200 m, depending on lens and altitude. About 20 m for the Haifa image [S]. Europe mosaics are gridded to 500 m [L]. | Irregular, 2003–present. Only city/date combinations that were actually photographed exist. | NASA photos are public domain. The Europe products and code are on Zenodo, doi:10.5281/zenodo.6638505 [L, via PMC9473566]. | Yes, but mostly relative. Colour ratios track the HPS→LED change well. Unmixing into lamp types worked for HPS and metal halide but was poor for LED in Haifa (Rybnikova et al. 2021, Remote Sensing 13:4413, doi:10.3390/rs13214413) [S]. |
| **Europe spectral-change maps** (Sánchez de Miguel, Bennie, Rosenfeld, Dzurjak, Gaston, *Sci. Adv.* 8:eabl6891, 14 Sep 2022, doi:10.1126/sciadv.abl6891) [L, PMC9473566] | MSI, SLI, phototaxis indices, B/G, G/R | 500 m | Two epochs: 2012–2013 and 2014–2020 | Open (CC-BY). Zenodo 6638505. | Europe only. Blue-band emissions up 24.4% overall. MSI rose most in Spain, Romania and the UK. The paper cites Spain at 56% LED street lighting by 2017 and the UK at 51% by early 2019. **Madrid is the only one of the 50 study cities covered.** |
| **Jilin-1 (JL1-3B, later JL1 video/"night" modes)**, Chang Guang Satellite Technology | RGB | About 0.9–1 m | 2017 onward. Tasked, single scenes. | **Commercial, paid.** | HPS vs LED at F1 0.72–0.83 (Quito, IJRS 2023, doi:10.1080/01431161.2023.2205983) [S]. About 84% overall accuracy on 446 observations (Hangzhou) [S]. Street-light extraction in a 51 km² area of Shanghai [S]. Cheng et al. 2020, IEEE JSTARS, doi:10.1109/JSTARS.2020.2971266: street-light extraction (about 90%) and HPS/LED classification, Chinese urban areas [L abstract; no per-city shares given]. Jerusalem spatial-variability study (ISPRS J. 2020) [S]. |
| **Luojia-1-01** (Wuhan Univ., launched 2 Jun 2018) | **Panchromatic only**, 460–980 nm. **No colour. Confirmed.** [S, multiple] | 130 m | 2018–2019 (short mission) | Was free through Hubei data portal | None |
| **VIIRS DNB / DMSP-OLS** | Panchromatic (about 500–900 nm) | 750 m / 2.7 km | 1992–present | Open | None. Blind to LED blue. |
| **DESIS** (hyperspectral, on the ISS) | Hyperspectral VNIR | 30 m | Test night acquisitions | DLR / Teledyne | Proof of concept for night-light identification (Remote Sensing 16:923, 2024) [S, title only]. No cities from the 50. |
| **EROS-B** (ImageSat) | Panchromatic | About 0.7 m | Occasional night tasking | Commercial | No colour. I found no lamp-type study. |
| **Proposed missions** | Nightsat (Elvidge et al. 2007, IJRS 28(12), doi:10.1080/01431160600981525), multispectral at 50–100 m, never flown [S]. NITESat 2U CubeSat concept (full colour) [S]. "A Case for a New Satellite Mission for Remote Sensing of Night Lights," Remote Sensing 13:2294 (2021) [S]. | — | — | — | Not available |
| **Ground hyperspectral** (NYU CUSP "Urban Observatory") | 872–850 channels, 0.4–1.0 µm, side-looking at the skyline | Building / lamp scale | Snapshots in 2013 and 2018 | Research data | NYC: HPS dominant in 2013 (Dobler et al. 2016, *Sensors* 16:2047, doi:10.3390/s16122047) [L]. LED dominant by 2018 (Yu, Manz, Sharma, Karpf, Bianco, Dobler, *Remote Sensing* 18(5):799, Mar 2026, doi:10.3390/rs18050799) [S]. |
| **Ground colour photometers** (TESS-W, TESS-4C, SQM, LANcube; Johnson BVR stations) | Broad-band colour of the sky glow | Single point | Continuous | Mostly open (e.g. STARS4ALL TESS network) | Madrid UCM station 2010–2020 (below). Israel: TESS-4C + LANcube + SDGSAT-1 before and after an HPS→LED interchange retrofit (Labrousse, Haspel, Levin, JQSRT 340:109450, 2025) [S]. Globe at Night gives naked-eye star counts, not colour. |
| **Street-view imagery** | Daytime luminaire appearance | Per pole | Varies | Google ToS restricts bulk use | The only study I found (Hong Kong, *Renewable Energy* 2025, S0960148125026151) detects and locates street lights for solar potential. **It does not classify HPS vs LED** [S]. I found no street-view HPS/LED classification paper covering any of the 50 cities. My search budget ran out before I could exhaust this, so gaps are possible. |

### SDGSAT-1 lamp-type studies

| Study | City / area | Method | Result | Evidence |
|---|---|---|---|---|
| Lv Z., Guo H., Zhang L., et al. 2024. "Urban public lighting classification method and analysis of energy and environmental effects based on SDGSAT-1 glimmer imager data." *Applied Energy* 355:122355. doi:10.1016/j.apenergy.2023.122355 | Trained on the Washington DC streetlight inventory. Applied to **Beijing, Shanghai**, Guangzhou, Shenzhen. | ML classifier on the RGB bands | LED vs HPS overall accuracy 80.3%, kappa 0.603. Maps city lighting composition and LED-retrofit energy savings. Per-city shares are not in the abstract. | [L abstract via RePEc] |
| "Identification of illumination source types using nighttime light images from SDGSAT-1." *Int. J. Digital Earth* 17(1), 2024. doi:10.1080/17538947.2023.2297013 (CAS AIR team; CGTN/Xinhua coverage Feb 2024) | **Beijing** | Machine learning | Overall accuracy 0.92 for all ALAN types and 0.95 for streetlights. LED use rises as road class falls (HPS on major roads). | [S; CGTN page L, P] |
| "Nighttime light in China's coastal zone: The type classification approach using SDGSAT-1 Glimmer Imager." *Remote Sens. Environ.* 2024 (pii S0034425724001159) | Mainland China coastal zone. Probably includes Shanghai, Qingdao, Dalian, Ningbo and Shantou, but I did not see per-city values. | New light indices plus thresholds. Classes: white LED, red LED, other. | **White LED is 67% of coastal-zone night light.** | [S] |
| "Lighting characteristics of public space in urban functional areas based on SDGSAT-1 glimmer imagery: A case study in Beijing." *RSE* 2024 (pii S0034425724001482). Also "Modelling the Public Perception of Urban Public Space Lighting…Beijing," *Sustainable Cities & Society* 2022. | **Beijing** | Colour bands by functional zone | Only the titles were visible | [S] |
| "Mapping Spectral Composition of Nighttime Lighting in Urban Green Spaces Using SDGSAT-1 NTL Data and Google Earth Imagery." *Remote Sensing* 18(5):732, Feb 2026 | **Shanghai** | B/G and G/R ratios by green-space type | Street trees get the most red-dominant light (lowest B/G and G/R). Forest patches get relatively more blue and green. | [S] |
| "When city lights turn blue: Spectral ALAN exposure, LED lighting, and diabetes prevalence using SDGSAT-1." *Environ. Pollut.* 2026 (PubMed 41831550) | Several Chinese cities. The city list was not visible. | Epidemiological link to RGB bands and lamp types | Top blue-band quartile has 61% higher odds of diabetes than the bottom quartile | [S] |
| "Classification of nighttime light types in China's nature protected areas based on SDGSAT-1." *IJDE* 2025, doi:10.1080/17538947.2025.2496791 | Protected areas, not cities | — | — | [S] |
| "Multispectral characterization of urban lighting transitions … dark-sky preserves using SDGSAT-1." *Experimental Astronomy*, Aug 2026, doi:10.1007/s10686-026-10074-8 | Antalya and Erzurum (Türkiye) | Classification | White-LED cover 9.2% in Antalya. Erzurum more than 77% HPS. | [S] |
| Levin N. 2023. *Sensors* 23:8237, doi:10.3390/s23198237 | Central Israel roads and Brisbane. SDGSAT-1 scenes from Feb 2022 to Apr 2023. | LANcube car-borne survey compared with SDGSAT-1 | LED shows a lower R/G ratio. Telling technologies apart at 40 m in dense urban areas is "challenging" because pixels mix sources. Dim residential streets can appear dark. | [L] |
| Labrousse, Haspel, Levin 2025. *JQSRT* 340:109450 | Highway 1 interchange between **Tel Aviv** and Jerusalem. SDGSAT-1 scenes Feb 2023 vs Feb 2024. | TESS-4C + LANcube + SDGSAT-1 | Brightness rose after the HPS→LED retrofit | [S] |

### ISS colour studies

- **Europe:** Sánchez de Miguel et al. 2022, *Sci. Adv.* [L]. See the table above.
- **Spain:** calibration example in Sánchez de Miguel et al. 2021 RSE [L].
- **Madrid:** worked example in the 2019 RSE paper, using a wide-angle ISS image from 19 Nov 2017 [S].
- **Milan:** ESA outreach [L, P].
  - The centre converted to white LED by 2015, the first European city to convert fully.
  - Belgium stays orange because of low-pressure sodium.
- **Haifa:** unmixing into lamp types, 2021 [S].
- **Granada Geopark:** ISS images from 6 Feb 2012 and 24 Jul 2021, 47 municipalities. Blue-band emissions rose 266%. Bustamante-Calabria et al. 2023, arXiv 2305.12009 [L].
- **Hong Kong / Macau:** Luojia-1 plus multi-temporal ISS imagery against night-sky brightness, *Remote Sensing* 17:3739 (2025) [S]. I did not see lamp-type results.
- **Colour vs land use (not lamp type), 8 cities:** Rybnikova, Mirkes, Gorban 2021, *Sensors* 21:7662 [L]. Cities: Atlanta, Beijing, Haifa, Khabarovsk, London, Naples, Nashville, Tianjin.
  - Blue light is associated with industrial and commercial areas.
  - Red and green are associated with residential areas.
- **Qualitative before/after pairs** (NASA astronaut Don Pettit, Sept 2026; PetaPixel article, loaded) [L, P]. Not calibrated or quantitative.
  - Miami 2012→2025
  - Chicago
  - Mexico City 2003→2025
  - São Paulo 2003→2025
  - Seoul
  - Las Vegas
  - Monterrey
  - Hong Kong: still sodium, while Shenzhen is all LED.
- **NASA Earth Observatory, "Shedding Light on Urban Development"** (15 Nov 2021, C. Small) [L]. An 18-city ISS colour montage that includes London, Singapore, Phoenix, Chicago, Paris and Kuwait City. No per-city lamp-type result.

---

## 2. Per-city evidence (only cities with evidence)

The other 36 of the 50 cities have **no satellite or imagery-derived lamp-colour/type evidence** that I found:

Baghdad, Addis Ababa, Dar es Salaam, Abidjan, Nairobi, Pune, Hefei, Yangon, Jinan, Shijiazhuang, Zhengzhou, Jaipur, Mumbai, Kano, Dongguan, Foshan, Riyadh, Santiago, Delhi, Shenyang, Dhaka, Dallas, Houston, Harbin, Toronto, Cairo, Belo Horizonte, Philadelphia, Boston, New Taipei, Alexandria, Johannesburg, Khartoum.

Notes on that list:
- Hefei appears in SDGSAT-1 urban-agglomeration *brightness* work only. There is no colour result for it.
- Dongguan and Foshan appear in Greater Bay Area SDGSAT-1 population and activity studies, which are not colour studies.
- The list names 33 cities. Tokyo, Singapore and Phoenix are also without real evidence, but they appear in the table below because of weak or qualitative mentions.
- Shantou, Qingdao, Ningbo and Dalian have only possible regional (coastal-zone) coverage and are listed in the table.

| City | Source (evidence level) | Imagery year(s) | Finding |
|---|---|---|---|
| **Madrid** | Robles, Zamorano, Pascual, Sánchez de Miguel, Gallego, Gaston 2021, *Remote Sensing* 13:1511, doi:10.3390/rs13081511 [S] and Gaston lab summary [L]. ISS pair: ESA "Madrid at night – a decade of changes" (Kuipers 2012 vs Cristoforetti 2022, colour-calibrated) [L, P]. ISS worked example in the 2019 RSE paper, image 19 Nov 2017 [S]. *Sci. Adv.* 2022 Europe maps [L]. | Sky station 2010–2020. ISS 2012, 2015 (Cristoforetti, 11 May 2015 [L]), 2017, 2022. | **Mostly HPS until 2015. Partial HPS→LED retrofit in 2015–2016, with HPS largely kept elsewhere, plus dimming control.** Details below the table. |
| **Beijing** | Lv et al. 2024 *Applied Energy* [L abstract]. IJDE 2024 illumination-source paper [S]. RSE 2024 public-space paper [S]. Rybnikova et al. 2021 (ISS colour vs land use) [L]. | SDGSAT-1 2022–2023. ISS date not stated. | LED/HPS classified at 80–95% accuracy. HPS dominates major roads and LED grows on lower-class roads and public areas. I could not see a city-wide LED %. |
| **Shanghai** | Lv et al. 2024 [L abstract]. RSE 2024 coastal zone [S]. *Remote Sensing* 2026 green spaces [S]. Jilin-1 street-light classification over 51 km² [S]. | SDGSAT-1 2022–2023. Jilin-1 about 2017–2019. | LED/HPS map exists. The coastal zone, which includes Shanghai, is 67% white LED; there is no Shanghai-specific figure. Red-dominant light falls on street trees. |
| **Qingdao, Dalian, Ningbo, Shantou** | RSE 2024 "Nighttime light in China's coastal zone" [S] | SDGSAT-1 about 2022–2023 | Probably inside the classified coastal zone (67% white LED overall). **Per-city values are not seen or verified.** |
| **Hong Kong** | Pettit ISS pair 2003→2025 [L, P, via PetaPixel]. *Remote Sensing* 17:3739 (2025), Luojia-1 plus ISS [S; no colour result seen]. | ISS 2003, 2025 | Hong Kong visibly **still sodium-orange in 2025** while neighbouring Shenzhen has turned LED-white. Qualitative only. |
| **New York** | Dobler et al. 2016 *Sensors* [L]. Yu et al. 2026 *Remote Sensing* [S]. Ground-based hyperspectral, not satellite. | 20 Nov 2013; 2018 | HPS dominant in 2013 (about 40 lamp types found). LED dominant by 2018. Context: the city's programme to replace about 250,000 HPS streetlights with LED by 2017. |
| **Tel Aviv** (metro fringe) | Labrousse et al. 2025 JQSRT [S] | SDGSAT-1 Feb 2023 vs Feb 2024 | One highway interchange (Tel Aviv–Jerusalem Highway 1) got brighter after HPS→LED. Not city-wide. |
| **Miami** | Pettit ISS pair [L, P] | 2012 → 2025 | Orange sodium changed to multicoloured/white LED. Qualitative. |
| **Mexico City** | Pettit ISS pair [L, P] | 2003 → 2025 | Orange sodium changed to white LED. Qualitative. |
| **São Paulo** | Pettit ISS pair [L, P] | 2003 → 2025 | Yellow-orange changed to cooler white. Qualitative. |
| **Atlanta** | Rybnikova et al. 2021 *Sensors* [L] | ISS (date not stated) | Colour bands vs land use only. Blue is associated with industrial and commercial areas. No lamp-type shares. |
| **Tokyo** | A search-result snippet attributed to NASA material [S; primary source not loaded] | ISS (undated) | Cooler blue-green city light, attributed to more mercury-vapour and less sodium lighting. Weak. |
| **Singapore, Phoenix** | NASA Earth Observatory 2021, C. Small 18-city ISS montage [L, P] | ISS (undated) | They appear in a colour montage chosen for diverse lightscapes. No lamp-type finding. |

### Madrid details

- **What was installed.** The Philips / City of Madrid contract (announced Dec 2014, installed 2014–2015) replaced about **225,000 luminaires**. Only **84,000** were LED (51,000 globe lanterns and 33,000 LED plates in existing lampposts). The remaining about 141,000 got "more efficient non-LED" lamps, plus CityTouch remote dimming. The target was a 44% energy saving [L, New Atlas; S, Buildings.com].
- **What the sky station saw.** Most of the retrofitted lamps became 3000 K LED [S]. Johnson B-band sky brightness **fell 14% in 2011–2015, then rose 32% in 2015–2019** [L, Gaston lab summary of Robles et al. 2021].
- **What the ISS images show.** Visibly whiter emissions after the retrofit.
- **Answer to the Madrid question: both.** Roughly a third of the city's luminaires went HPS→LED (3000 K). The majority stayed discharge lamps, presumably upgraded HPS, though I did not see this confirmed. The pre-2015 darkening is consistent with dimming or austerity, and blue sky brightness then jumped.

---

## 3. Recommendation for a 2012–2024, 50-city study

**No space dataset gives a consistent colour or CCT time series for 2012–2024 across all 50 cities.**

1. **SDGSAT-1 GLI is the most usable single dataset.**
   - It is global, free for research (apply through sdgsat.ac.cn), has calibrated RGB at 40 m, and has published LED/HPS classifiers you could reuse (Lv et al. 2024; RSE 2024 coastal-zone indices).
   - It is the only realistic way to get an **end-point (2022–2024) lamp-type or blue-ratio cross-section** for all 50 cities, including the African and South Asian ones.
   - Limits:
     - It starts in 2022, so there is no 2012–2021 baseline.
     - Acquisitions are tasked and irregular (11-day repeat), so check the scene archive city by city for cloud-free scenes.
     - Night imaging is at about 21:30–22:00 local only.
     - Pixels mix sources at 40 m, and dim residential streets may fall below detection (Levin 2023).
     - The red band extends to 894 nm.
     - Classifiers were trained in DC and China, so transfer to other lamp stocks (e.g. Cairo, Lagos-type mixed MH/fluorescent) is untested.
     - Use is restricted to research, with attribution required.
2. **ISS astronaut photos are the only source that reaches back to about 2003–2015 (pre-LED).**
   - Use them for **historical before/after checks in individual cities**, where suitable night frames exist (search the NASA Gateway to Astronaut Photography per city).
   - Calibrated quantitative products exist only for Europe (Madrid, *Sci. Adv.* 2022, Zenodo 6638505, 500 m, 2012–13 vs 2014–20).
   - Elsewhere you would have to calibrate yourself (Sánchez de Miguel 2021 pipeline).
   - Coverage is opportunistic: varying cameras, dates and angles, with many cities missing for key years.
3. **Jilin-1** is very high resolution RGB but commercial and single-scene. It is only worth buying for a small validation subset.
4. **Luojia-1, VIIRS, DMSP and EROS-B** give no colour. Luojia-1 is confirmed panchromatic (460–980 nm).
5. **Practical design:**
   - Use VIIRS for the 2012–2024 intensity trend.
   - Use SDGSAT-1 (2022–24) to estimate the current LED share or B/G ratio per city.
   - Use ISS frames where available for pre-LED colour at the baseline.
   - Add documented municipal retrofit records (e.g. Madrid 2015, NYC 2013–17) as ground truth.
   - Treat VIIRS trends in high-LED cities as underestimating blue-light growth. The *Sci. Adv.* 2022 paper found a 24% rise in blue emissions across Europe that panchromatic sensors largely miss.

## Key URLs
- SDGSAT-1 Open Science Program: https://www.sdgsat.ac.cn/ ; eoPortal: https://www.eoportal.org/satellite-missions/sdgsat-1
- Lv et al. 2024: https://ideas.repec.org/a/eee/appene/v355y2024ics0306261923017191.html
- IJDE 2024: https://www.tandfonline.com/doi/full/10.1080/17538947.2023.2297013
- RSE 2024 coastal: https://www.sciencedirect.com/science/article/abs/pii/S0034425724001159
- Sci. Adv. 2022: https://pmc.ncbi.nlm.nih.gov/articles/PMC9473566/ ; Zenodo 10.5281/zenodo.6638505
- ISS calibration 2021: https://arxiv.org/abs/2108.07050
- Madrid sky 2021: https://doi.org/10.3390/rs13081511 ; http://kevingaston.com/lighting-madrids-night-sky/
- Madrid Philips retrofit: https://newatlas.com/philips-connected-led-city-lighting-madrid/35304/
- ESA Madrid 2012/2022: https://www.esa.int/ESA_Multimedia/Images/2022/10/Madrid_at_night_A_decade_of_changes_in_street_lighting
- Levin 2023: https://pmc.ncbi.nlm.nih.gov/articles/PMC10575406/
- NYC hyperspectral: https://pmc.ncbi.nlm.nih.gov/articles/PMC5191028/ ; https://doi.org/10.3390/rs18050799
- Pettit pairs: https://petapixel.com/2026/09/08/astronauts-before-and-after-photos-show-how-cities-switched-from-orange-to-white-light/
- Granada ISS: https://arxiv.org/html/2305.12009
- Rybnikova 2021: https://pmc.ncbi.nlm.nih.gov/articles/PMC8618994/
