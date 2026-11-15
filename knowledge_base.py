import glob
import os
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# ==============================================================================
# 1. EXPERIMENTS DATA (EXACT REQUESTED ORDER)
# ==============================================================================
EXPERIMENTS: List[Dict] = [
    {
        "code": "PSI-99",
        "aliases": ["saffire-ii", "saffire ii", "saffire 2"],
        "name": "Spacecraft Fire Experiment-II (SAFFIRE-II)",
        "category": "Prevention & Flammability",
        "total_tests": 13,
        "avg_o2": "22.01%",
        "objective": (
            "Determine large-scale fire growth rates and low-gravity flammability limits "
            "for multiple spacecraft materials, including Silicone, SIBAL fabric, and PMMA/Nomex."
        ),
        "execution": (
            "Conducted 13 tests on samples of varying thickness and composition under "
            "oxygen concentrations near 22% (21.5%–22.1%) and an airflow velocity of 20 cm/s."
        ),
        "results": (
            "Material flammability responses varied dramatically: cotton-fiberglass (SIBAL) "
            "and PMMA burned for 115 to 900 seconds (exceeding 140 seconds in composite/PMMA tests), "
            "whereas silicone samples self-extinguished almost immediately with insignificant burn time."
        ),
        "conclusion": (
            "Selecting flame-resistant materials certified against microgravity criteria "
            "radically reduces fire propagation risks inside spacecraft."
        ),
        "safety_tip": (
            "Test all decorative, structural, and insulating materials under actual operational "
            "spaceflight conditions rather than relying solely on conventional Earth-based safety tests."
        ),
    },
    {
        "code": "PSI-98",
        "aliases": ["saffire-i", "saffire i", "saffire 1"],
        "name": "Spacecraft Fire Safety Experiment-I (SAFFIRE-I)",
        "category": "Prevention & Flammability",
        "total_tests": 2,
        "avg_o2": "21.55%",
        "objective": (
            "Determine how rapidly a large-scale fire grows in microgravity and compare "
            "low-gravity flammability limits with normal gravity on Earth."
        ),
        "execution": (
            "Large samples of SIBAL fabric (40.6 cm x 94 cm, 0.37 cm thick) were ignited "
            "inside an uncrewed cargo spacecraft after departing the International Space Station (ISS) "
            "to avoid endangering the crew."
        ),
        "results": (
            "The fire burned for a much longer duration (420 seconds) when airflow was concurrent "
            "with the flame compared to opposed flow (70 seconds) at an airflow speed of 20 cm/s."
        ),
        "conclusion": (
            "Ventilation direction and airflow velocity inside a spacecraft cabin are decisive "
            "factors in determining fire growth and sustainability in zero gravity."
        ),
        "safety_tip": (
            "When a fire breaks out in an enclosed habitat or spacecraft, shut down ventilation "
            "and airflow systems immediately to starve the flame of oxygen."
        ),
    },
    {
        "code": "PSI-100",
        "aliases": ["saffire-iii", "saffire iii", "saffire 3"],
        "name": "Spacecraft Fire Experiment-III (SAFFIRE-III)",
        "category": "Prevention & Flammability",
        "total_tests": 2,
        "avg_o2": "21.50%",
        "objective": (
            "Investigate large-scale flame spread behavior over SIBAL fabric when exposed "
            "to higher airflow velocities of up to 30 cm/s in microgravity to bound flammability limits."
        ),
        "execution": (
            "Large SIBAL fabric samples (94 cm x 40.6 cm, 0.33 cm thick) were exposed to a "
            "faster 30 cm/s airflow stream in both concurrent and opposed directions."
        ),
        "results": (
            "Increasing the airflow velocity noticeably accelerated the flame spread rate and "
            "increased fire intensity compared to earlier lower-flow experiments."
        ),
        "conclusion": (
            "Strong air currents inside spacecraft cabins can turn small fires into rapidly "
            "spreading blazes that are difficult to control."
        ),
        "safety_tip": (
            "Design HVAC and ventilation systems in enclosed facilities and spacecraft to operate "
            "at low, controlled airflow velocities to reduce fire acceleration risks."
        ),
    },
    {
        "code": "PSI-102",
        "aliases": ["same", "smoke and aerosol"],
        "name": "Smoke and Aerosol Measurement Experiment (SAME)",
        "category": "Fire Detection & Smoke",
        "total_tests": 8,
        "avg_o2": "21.00%",
        "objective": (
            "Quantify liquid smoke particulate sizes and droplet size distributions in microgravity "
            "to develop more accurate spacecraft smoke detectors."
        ),
        "execution": (
            "Samples of spacecraft wire insulation and materials—Teflon, Kapton, Silicone Rubber, "
            "Lampwick, and Dibutyl Phthalate—were heated in the Microgravity Science Glovebox (MSG) "
            "at 5–10 cm/s airflow while measuring mass-loss rates and smoke aging (1 to 20 minutes)."
        ),
        "results": (
            "Measurements revealed that smoke particles generated in space differ significantly in "
            "particle size and agglomeration behavior over time (aging) compared to smoke on Earth."
        ),
        "conclusion": (
            "Terrestrial smoke alarms may fail to detect space fires early or may trigger false "
            "alarms because microgravity alters particulate size signatures."
        ),
        "safety_tip": (
            "Calibrate fire detection systems to match the specific materials present in the "
            "environment and their smoke characteristics to guarantee early detection and avoid false alarms."
        ),
    },
    {
        "code": "PSI-25",
        "aliases": ["bass-ii", "bass ii", "bass 2", "burning and suppression of solids"],
        "name": "Burning and Suppression of Solids - II (BASS-II)",
        "category": "Prevention & Flammability",
        "total_tests": 129,
        "avg_o2": "18.57%",
        "objective": (
            "Study ignition, flame spread, and extinction mechanisms of solid fuels (fabrics, "
            "PMMA films/slabs/rods, wax) in microgravity to improve fire detection and suppression models."
        ),
        "execution": (
            "Executed 129 precision tests on thin strips, rods, and fabrics across varying oxygen "
            "concentrations (approx. 13.6% to 22.2%) while monitoring CO and CO2 gas emissions."
        ),
        "results": (
            "Lowering ambient oxygen concentration to around 15%–17% severely restricted the ability "
            "of solid materials to sustain combustion, while incomplete combustion produced high "
            "levels of toxic carbon monoxide (CO)."
        ),
        "conclusion": (
            "Solid-material fires can be suppressed effectively by controlling ambient oxygen levels "
            "or applying suppressants that inhibit combustion chemistry."
        ),
        "safety_tip": (
            "Equip enclosed spaces with toxic carbon monoxide (CO) sensors alongside smoke "
            "detectors, as incomplete combustion releases lethal gases before large flames appear."
        ),
    },
    {
        "code": "PSI-106",
        "aliases": ["slice", "liftoff"],
        "name": "Structure and Liftoff In Combustion Experiment (SLICE)",
        "category": "Combustion Fundamentals",
        "total_tests": 12,
        "avg_o2": "21.00%",
        "objective": (
            "Understand the internal structure, liftoff height, and stability of laminar diffusion "
            "flames in microgravity using gaseous fuels."
        ),
        "execution": (
            "Conducted 12 co-flow test sessions burning methane (CH4), ethylene (C2H4), and ethane "
            "(C2H6) at varying concentrations diluted with nitrogen (N2) to examine flame-base stability."
        ),
        "results": (
            "Identified the exact threshold where the flame detaches from the fuel nozzle (liftoff) "
            "and quantified how nitrogen dilution cools and extinguishes the flame."
        ),
        "conclusion": (
            "Controlling the inert gas ratio (such as nitrogen) and fuel flow rate governs "
            "whether a diffusion flame stays anchored or extinguishes."
        ),
        "safety_tip": (
            "Use inert gases like nitrogen as a safe and effective method to dilute flammable "
            "gas mixtures and prevent flame stabilization in piping systems and laboratories."
        ),
    },
    {
        "code": "PSI-159",
        "aliases": ["acme", "cfi-g", "cool flames investigation"],
        "name": "ACME / Cool Flames Investigation with Gases (ACME CFI-G)",
        "category": "Suppression & Cool Flames",
        "total_tests": 179,
        "avg_o2": "32.18%",
        "objective": (
            "Determine the physical and chemical conditions required for spherical cool diffusion "
            "flames in microgravity across high oxygen concentrations and varied pressures."
        ),
        "execution": (
            "Conducted 179 tests using hydrocarbon gases (ethane, propane, butane, and 30%/50% "
            "mixtures) across pressures from ~0.5 to 3.0 bar in oxygen-enriched atmospheres (up to ~40%)."
        ),
        "results": (
            "Successfully observed sustained cool-flame combustion at much lower temperatures than "
            "conventional hot flames, continuing even after visible hot ignition extinguished."
        ),
        "conclusion": (
            "Gaseous fuels can keep reacting and burning invisibly without a hot visible flame, "
            "creating a hidden hazard in oxygen-rich environments."
        ),
        "safety_tip": (
            "Never rely solely on visual inspection or high-temperature sensors to detect gas "
            "leaks and combustion; deploy specialized chemical sensors for gases and invisible cool flames."
        ),
    },
    {
        "code": "PSI-142",
        "aliases": ["counterflow", "cool flame transitions"],
        "name": "Quantitative Studies of Cool Flame Transitions Using Counterflow Flames",
        "category": "Suppression & Cool Flames",
        "total_tests": 8,
        "avg_o2": "N/A (Simulation & FLEX Data)",
        "objective": (
            "Conduct simulations and ground-based counterflow studies using FLEX flight data to "
            "analyze the effects of oxygen and ozone concentrations on cool flame extinction limits."
        ),
        "execution": (
            "Combined spaceflight FLEX droplet data with counterflow burner experiments and "
            "numerical simulations (DME, n-heptane, n-decane, n-dodecane) to map cool-to-hot flame transitions."
        ),
        "results": (
            "Adding trace amounts of strong oxidizers such as ozone dramatically shifted cool-flame "
            "extinction limits and made cool flames far more likely to persist."
        ),
        "conclusion": (
            "Low-temperature combustion chemistry is extremely sensitive to oxidizing gases "
            "present in the surrounding atmosphere."
        ),
        "safety_tip": (
            "Strictly isolate oxidizing gases (such as pure oxygen and ozone) from fuel vapors "
            "and flammable materials, as they dangerously lower the ignition threshold."
        ),
    },
    {
        "code": "PSI-108",
        "aliases": ["stdce", "surface tension"],
        "name": "Surface Tension Driven Convection Experiment-1 (STDCE-1)",
        "category": "Fluid Physics / Convection",
        "total_tests": 38,
        "avg_o2": "N/A (Non-burning fluid)",
        "objective": (
            "Investigate thermocapillary fluid flows and temperature distributions driven by "
            "surface tension gradients in microgravity."
        ),
        "execution": (
            "Conducted 38 tests across 5 runs by heating silicone oil (flat and curved free surfaces) "
            "with CO2 lasers (0.31–10.1 W) and cylindrical heaters (1.2–12.9 W) while tracking flow."
        ),
        "results": (
            "Observed fast, stable unicellular thermocapillary flows driven by surface temperature "
            "differences, matching numerical model predictions."
        ),
        "conclusion": (
            "Even without gravity-driven buoyancy, localized heating of liquids induces rapid "
            "fluid motion and convective heat transfer to unexpected regions."
        ),
        "safety_tip": (
            "Shield cooling systems and flammable liquids from localized heat sources (lasers or "
            "heaters), because surface-tension currents can transport heat and trigger sudden vaporization and ignition."
        ),
    },
]


# ==============================================================================
# 2. STORIES DATA ("What about story")
# ==============================================================================
STORIES: List[Dict] = [
    {
        "title": "Apollo 13",
        "subtitle": "April 1970 • Oxygen Tank Explosion & Survival",
        "content": (
            "Apollo 13 was NASA’s third mission to the Moon. The crew members were Jim Lovell, "
            "Fred Haise, and Jack Swigert. They planned to explore an area called Fra Mauro. "
            "After the successful Apollo 11 and Apollo 12 missions, many people thought Apollo 13 "
            "would be a normal mission.\n\n"
            "Before launch, Jack Swigert replaced Ken Mattingly because Mattingly might have caught "
            "measles. The launch also had a problem: one rocket engine stopped early. The other "
            "engines worked for a longer time, so Apollo 13 still reached orbit.\n\n"
            "On the third day of the mission, an oxygen tank exploded. The explosion damaged another "
            "tank and caused the spacecraft to lose oxygen and electrical power. The astronauts could "
            "not land on the Moon anymore.\n\n"
            "The crew moved into the Lunar Module, Aquarius, and used it like a lifeboat. They saved "
            "their supplies while Mission Control helped them find a way back to Earth.\n\n"
            "The investigation found that the heater switches in the oxygen tank had not been changed "
            "when the voltage was increased. During a test before launch, the heaters became very hot "
            "and damaged the insulation inside the tank. The damaged tank later exploded in space.\n\n"
            "The astronauts returned safely to Earth and landed in the Pacific Ocean on April 17, 1970. "
            "Apollo 13 showed the importance of teamwork and quick thinking. The mission also helped "
            "NASA learn how to make spacecraft safer."
        ),
    },
    {
        "title": "Apollo 1 Accident",
        "subtitle": "January 27, 1967 • Pure-Oxygen Cabin Flash Fire",
        "content": (
            "In November 1966, NASA prepared for the first crewed Apollo mission, officially designated "
            "as AS-204 and later known as Apollo 1. The mission was planned to last up to 14 days, "
            "with the main objectives of testing the spacecraft's ability to operate in space and "
            "evaluating the Service Module's main engine.\n\n"
            "The spacecraft, Command Module 012, began construction in August 1964 in Downey, California. "
            "NASA assigned three astronauts to the mission: Virgil \"Gus\" Grissom, Edward White, and "
            "Roger Chaffee. The crew underwent extensive training and practiced the mission using "
            "spacecraft simulators.\n\n"
            "On August 26, 1966, the spacecraft arrived at Kennedy Space Center, where engineers "
            "connected its components and continued testing. After successfully completing altitude "
            "chamber tests in December 1966, the spacecraft was transferred to Launch Pad 34 on "
            "January 3, 1967, for pre-flight testing.\n\n"
            "On January 27, 1967, the three astronauts participated in a test that required the "
            "spacecraft to operate using its internal electrical power. During the test, the cabin "
            "was pressurized with 100% oxygen while the astronauts wore spacesuits and the hatch "
            "remained closed. A sudden flash fire occurred inside the spacecraft and spread rapidly. "
            "The astronauts could not escape, and all three lost their lives due to the accident.\n\n"
            "Following the incident, NASA established an investigative board to determine the cause "
            "of the fire. The investigation identified several technical and management failures that "
            "contributed to the accident. The findings were published in a detailed report, and "
            "congressional hearings were held to examine the incident and NASA's safety procedures.\n\n"
            "After the investigation, NASA redesigned the Apollo spacecraft and introduced several "
            "safety improvements. The original three-piece hatch was replaced with a single hatch "
            "that could be opened from inside or outside within three seconds. NASA also restricted "
            "combustible materials inside the spacecraft and improved its management and safety procedures.\n\n"
            "The Apollo 1 accident highlighted the importance of spacecraft design, material safety, "
            "emergency exits, and effective testing procedures. The lessons learned led to major "
            "improvements in the Apollo spacecraft and helped NASA prepare for future crewed missions "
            "to the Moon."
        ),
    },
    {
        "title": "Fire Aboard the Mir Space Station",
        "subtitle": "February 24, 1997 • Solid-Fuel Oxygen Generator Fire",
        "content": (
            "On February 24, 1997, six crew members were living aboard the Russian space station Mir. "
            "Three of them were Russian cosmonauts, one was an American astronaut, and one was a German "
            "astronaut. That evening, cosmonaut Aleksandr Lazutkin turned on a solid-fuel oxygen "
            "generator in the Kvant-1 module. The canister caught fire and produced a large flame and "
            "thick smoke.\n\n"
            "The fire made the situation dangerous because it blocked the way to one of the Soyuz "
            "spacecraft. The crew could use this spacecraft to escape from Mir in an emergency. The "
            "crew quickly put on oxygen masks. Cosmonaut Valeri Korzun used a fire extinguisher to "
            "fight the flames, while astronaut Jerry Linenger helped hold him steady. The other crew "
            "members passed them more fire extinguishers. The fire eventually went out, and the "
            "station’s structure was not seriously damaged. No crew members were injured.\n\n"
            "After the fire, smoke filled parts of the station. Mir’s life-support system worked for "
            "several hours to clean the air. The crew stayed calm and worked together until conditions "
            "became safe again.\n\n"
            "Investigators studied the damaged oxygen generator. They later decided that small pieces "
            "of latex glove material may have accidentally entered the canister and helped cause the "
            "fire. The exact cause was difficult to confirm because the generator was badly damaged.\n\n"
            "After the accident, Russian space officials improved emergency training for crews and "
            "changed how the oxygen-generator canisters were prepared. The incident also provided "
            "lessons for the International Space Station. It showed how important it is to prepare "
            "for emergencies, follow safety procedures, and work together under pressure."
        ),
    },
]


# ==============================================================================
# 3. NASA APPLICATIONS ("NASA Applications")
# ==============================================================================
NASA_APPLICATIONS: List[Dict] = [
    {
        "title": "Firefighters’ Air Tanks",
        "subtitle": "Lightweight Composite Breathing System (1976)",
        "content": (
            "In 1976, NASA’s Johnson Space Center worked with A-T-O Inc. to develop lighter air "
            "tanks for firefighters. The new backpack breathing system used ideas and technology "
            "from the equipment made for astronauts.\n\n"
            "The system weighed only 20 pounds and provided 30 minutes of air. It was 13 pounds "
            "lighter than conventional firefighting tanks, so firefighters could move more easily "
            "while wearing it. The tank had an aluminum liner wrapped in strong glass fibers. This "
            "made it lighter and helped prevent corrosion.\n\n"
            "The new equipment also had a redesigned face mask that gave firefighters better vision. "
            "A personal warning device told each firefighter when their air was running low. Because "
            "the warning was personal, it did not add more noise to an already busy and stressful scene.\n\n"
            "Fire departments in Houston, Los Angeles, and New York tested the new system. Their "
            "tests helped improve the equipment. This project showed how technology developed for "
            "space could also help firefighters stay safer on Earth."
        ),
    },
    {
        "title": "Fire Detector",
        "subtitle": "Brunswick Incipient Fire Detector (1970s)",
        "content": (
            "In the 1970s, a smoke detector called the Brunswick Incipient Fire Detector was developed "
            "for the Space Shuttle. It worked by sampling the air and looking for tiny particles "
            "produced by combustion. Unlike older detectors, it could tell the difference between "
            "these particles and ordinary dust. This helped reduce false alarms.\n\n"
            "The detector could also warn people about a fire before flames or heavy smoke appeared. "
            "In large places such as mines, several detectors could be connected to one central system. "
            "If a detector found a possible fire, the system could warn workers and show where the "
            "problem was.\n\n"
            "This technology was useful in places where dust might trigger ordinary smoke detectors. "
            "The article says the U.S. Bureau of Mines was interested in testing it to improve mine "
            "safety. The detector was also considered for other industrial and large facilities, such "
            "as factories, communication centers, and power plants."
        ),
    },
    {
        "title": "Project FIRES",
        "subtitle": "Firefighters’ Integrated Response Equipment System",
        "content": (
            "Project FIRES (Firefighters' Integrated Response Equipment System) is a joint initiative "
            "by NASA and the U.S. Fire Administration (USFA) created to curb severe injuries and "
            "fatalities in firefighting. Traditional gear had remained largely unchanged for half a "
            "century, offering inadequate thermal protection while its heavy weight restricted mobility "
            "and caused exhaustion.\n\n"
            "Managed by NASA’s Marshall Space Flight Center alongside contractor Grumman Advanced "
            "Development Division, the project redesigned the firefighter’s entire protective ensemble. "
            "Engineers applied lightweight, fire-resistant materials originally developed for Apollo "
            "spacesuits and spacecraft to provide maximum protection with greater ease of movement.\n\n"
            "After five years of development, the upgraded suit, helmet, boots, and gloves underwent "
            "a nine-month field evaluation across fourteen U.S. fire departments, including Alexandria, "
            "Virginia. Ultimately, Project FIRES established a safer, more agile, and affordable "
            "nationwide standard for firefighting attire."
        ),
    },
]


# ==============================================================================
# 4. CORE KNOWLEDGE CHUNKS FROM PDF GUIDE & EXCEL WORKBOOKS
# ==============================================================================
CORE_DOC_CHUNKS: List[Dict[str, str]] = [
    {
        "source": "ISS Combustion Science Guide (Overview & Authors)",
        "text": (
            "Document: 'A Researcher's Guide to: International Space Station Combustion Science' "
            "(NP-2015-10-034-JSC), published by the NASA ISS Program Science Office, Johnson Space Center. "
            "Authors: Suleyman A. Gokoglu, Daniel L. Dietrich, Dennis P. Stocker, Sandy L. Olson, "
            "Michael C. Hicks (NASA Glenn Research Center), and Paul V. Ferkul (Universities Space "
            "Research Association). Executive Editor: Amelia Rai; Technical Editor: Neesha Hosein; "
            "Designer: Cory Duke. ISS orbits at ~240-250 miles (400 km) altitude, 51 degrees inclination, "
            "90-minute orbital period."
        ),
    },
    {
        "source": "ISS Combustion Science Guide (Why Microgravity?)",
        "text": (
            "Typical flame temperatures are ~2,300 K compared to ~300 K ambient gas, creating an "
            "eight-fold density gradient over 1 cm. On Earth, gravity creates strong buoyant convection "
            "(~1 m/s) that makes flames lift, point upward, and flicker. In microgravity, buoyancy is "
            "suppressed, reducing complex 3-D reacting flows into simpler 1-D spherical or planar systems "
            "and enabling long-duration study of low-stretch (low-velocity) flames, cool flames, "
            "radiative extinction, and realistic spacecraft fire hazards."
        ),
    },
    {
        "source": "ISS Combustion Science Guide (Spacecraft Fire Safety Misconceptions)",
        "text": (
            "NASA identified three critical historical misconceptions about fire in microgravity (page 35): "
            "(1) 'A steady fire cannot exist in a quiescent microgravity environment'—debunked by Mir "
            "candle flames burning >45 minutes and SOFBALL flame balls (~1 Watt) burning >40 minutes. "
            "(2) 'A fire will self-extinguish if ventilation is shut off'—debunked by quiescent flames and "
            "persistent invisible cool flames. "
            "(3) 'Because reduced gravity is inherently safer, terrestrial fire standards (NASA-STD-6001 Test 1) "
            "are conservative'—debunked by BASS and drop-tower tests showing enhanced flammability near "
            "10 cm/s spacecraft ventilation speeds, lower Limiting Oxygen Indices (LOI), critical ignition "
            "heat flux as low as half normal gravity, and upstream flame spread into oncoming airflow. "
            "Additionally, local nitrogen suppression jets can entrain air and temporarily strengthen a flame."
        ),
    },
    {
        "source": "ISS Combustion Science Guide (Droplet Combustion, FLEX & Cool Flames)",
        "text": (
            "FLEX (Flame Extinguishment Experiment) and FLEX-2 operate inside the Combustion Integrated "
            "Rack (CIR) using the Multi-user Droplet Combustion Apparatus (MDCA), deploying 1–5 mm heptane "
            "and methanol droplets in 0–3 atm environments up to 40% O2 with diluents (N2, CO2, He, Xe). "
            "FLEX discovered stable, quasi-steady 'cool flames' (Nayagam et al., 2012) that continue "
            "vaporizing large alkane droplets after hot visible flame radiative extinction, forming a "
            "large vapor cloud before extinguishing at a finite droplet size."
        ),
    },
    {
        "source": "ISS Combustion Science Guide (Gaseous Diffusion Flames, ACME, Premixed, Water Mist & SCWO)",
        "text": (
            "Gaseous diffusion experiments include LSP (STS-83/94/107), TGDF & ELF (STS-87), SPICE (2009, MSG), "
            "SLICE (2012, MSG), and the 5 ACME experiments in CIR: BRE (Burning Rate Emulator), CLD Flame, "
            "E-FIELD Flames (up to 10 kV), Flame Design, and s-Flame. Premixed flames: SOFBALL produced "
            "weak ~1 W stationary flame balls. Fire Safety: Water Mist (Mist on STS-107) led to certified "
            "non-toxic water-mist portable fire extinguishers sent to ISS in Dec 2015 to replace CO2 units. "
            "Super-Critical Processes: SCWO (Super-Critical Water Oxidation) and NASA-CNES SCWM study "
            "hydrothermal flames and salt precipitation (Na2SO4 0.5% w/v) in zero-g."
        ),
    },
    {
        "source": "ISS Combustion Science Guide (Facilities & Appendix Specs)",
        "text": (
            "ISS Combustion Facilities (Appendix p. 52): "
            "CIR (100-L chamber, 8 optical windows, delivered STS-126 Nov 2008). "
            "MDCA: Up Mass 254 kg, Volume 0.48 m3, Power 0.73 kW, Data 72 GB, On-orbit: Yes, POC: Mark Hickman (216.977.7105). "
            "ACME: Up Mass 250 kg, Volume 0.5 m3, Power 0.75 kW, Data 72 GB, diagnostics include radiometers, 2 color cameras, UV camera, 2 HiBMs cameras, PMTs, ion current, gas chromatograph; POC: Mark Hickman. "
            "SoFIE (planned 2019): Up Mass 250 kg, Volume 0.5 m3, Power 0.75 kW, Data 72 GB, same diagnostics as ACME, supports Flame Spread, GEL, Narrow Channel, SMuRF, MIST; POC: Mark Hickman. "
            "MSG (operating since July 2002, 255-L negative-pressure workspace, 1000 W DC power): Mini-facility Up Mass 40 kg, Volume 0.1 m3, Power 0.05 kW, Data 10 GB, supports SPICE, SLICE, BASS; POC: Robert Hawersaat (216.433.8157). "
            "SAMS measures vibratory acceleration; MAMS measures quasi-steady (<0.01 Hz) acceleration. "
            "Telescience Support Center (TSC) has 33 workstations providing 24/7 ground commanding."
        ),
    },
    {
        "source": "Excel Summary Dashboard (All 9 Cleaned Investigations = 391 Tests)",
        "text": (
            "Excel Summary_Dashboard covers 9 investigations totaling 391 cleaned tests: "
            "PSI-98 (SAFFIRE-I): 2 tests (S1: SIBAL Fabric, Concurrent flow 20 cm/s, O2 21.6%, Burn Time 420 s; "
            "S2: SIBAL Fabric, Opposed flow 20 cm/s, O2 21.5%, Burn Time 70 s). "
            "PSI-99 (SAFFIRE-II): 13 entries, avg O2 22.01%. "
            "PSI-100 (SAFFIRE-III): 2 tests, avg O2 21.5%. "
            "PSI-25 (BASS-II): 129 tests, avg O2 18.57% (PIs: Bhattacharjee, Ferkul, Miller, Olson, Fernandez-Pello, T'ien). "
            "PSI-102 (SAME): 8 samples, avg O2 21%. "
            "PSI-159 (ACME CFI-G): 179 tests, avg O2 32.18% (fuels: ethane, propane, butane, 30%/50% mixtures; pressures 0.50665–3.0399 bar; cool flames noted on Day 10 & 11). "
            "PSI-142 (Counterflow Cool Flames): 8 reference datasets with DOIs. "
            "PSI-106 (SLICE): 12 test dates (Feb–Mar 2012), avg O2 21%. "
            "PSI-108 (STDCE-1): 38 tests across Runs 1–5 (CO2 Laser CF and Cylindrical Heater CT)."
        ),
    },
]

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "am",
    "in", "on", "at", "to", "for", "of", "by", "with", "from", "about", "as",
    "into", "and", "or", "but", "not", "no", "what", "which", "who", "whom",
    "where", "when", "why", "how", "do", "does", "did", "can", "could", "would",
    "should", "will", "this", "that", "these", "those", "it", "its", "they",
    "them", "their", "i", "me", "my", "you", "your", "we", "our", "compare",
    "between", "difference", "tell", "give", "explain", "show", "much", "many",
    "long", "please", "used", "using", "happened", "happen",
}

LOW_SIGNAL_WORDS = {"experiment", "experiments", "test", "tests", "sample", "space", "nasa", "iss", "fire"}

# Normalized Arabic -> English domain dictionary (keys are already normalized: أ/إ/آ->ا, ة->ه, ى->ي)
ARABIC_PHRASE_MAP: Dict[str, str] = {
    "سافاير 1": "psi-98 saffire-i",
    "سافير 1": "psi-98 saffire-i",
    "سافاير 2": "psi-99 saffire-ii",
    "سافير 2": "psi-99 saffire-ii",
    "سافاير 3": "psi-100 saffire-iii",
    "سافير 3": "psi-100 saffire-iii",
    "باس 2": "psi-25 bass-ii",
    "سلايس": "psi-106 slice",
    "اكمي": "psi-159 acme cfi-g",
    "سيم": "psi-102 same",
    "ستدسي": "psi-108 stdce-1",
    "ابولو 13": "apollo 13",
    "ابولو 1": "apollo 1",
    "محطه مير": "mir space station",
    "لهب بارد": "cool flame",
    "اللهب البارد": "cool flame",
    "اول اكسيد الكربون": "carbon monoxide co",
    "كاشف الحريق": "fire detector",
    "كاشف الدخان": "smoke detector",
    "جهاز انذار": "smoke detector",
    "خزان الهواء": "air tanks firefighters",
    "خزانات الهواء": "air tanks firefighters",
    "اسطوانه الهواء": "air tanks firefighters",
    "رجال الاطفاء": "firefighters",
    "مشروع فايرز": "project fires",
    "درجه الحراره": "temperature peak burner",
    "سرعه الهواء": "air flow velocity",
    "تدفق الهواء": "air flow direction",
    "اتجاه الهواء": "flow direction concurrent opposed",
    "جاذبيه صغري": "microgravity",
    "انعدام الجاذبيه": "microgravity zero-g",
    "مدة الاحتراق": "burn time duration",
    "مده الاحتراق": "burn time duration",
    "زمن الاحتراق": "burn time duration",
    "وقت الاحتراق": "burn time duration",
    "نسبه الاكسجين": "o2 oxygen percent",
    "تركيز الاكسجين": "o2 oxygen percent",
}

ARABIC_WORD_MAP: Dict[str, str] = {
    "مده": "burn time duration seconds",
    "زمن": "burn time duration seconds",
    "وقت": "burn time duration seconds",
    "احتراق": "burn time combustion",
    "احترق": "burn time burned",
    "يحترق": "burn",
    "اشتعال": "ignition flammability",
    "مشتعل": "flammable",
    "اكسجين": "o2 oxygen percent",
    "هواء": "air flow airflow",
    "تدفق": "flow airflow",
    "اتجاه": "direction concurrent opposed",
    "موازي": "concurrent",
    "نفس": "concurrent",
    "معاكس": "opposed",
    "عكس": "opposed",
    "سرعه": "velocity speed",
    "ماده": "material fuel",
    "مواد": "materials",
    "وقود": "fuel",
    "قماش": "fabric sibal",
    "سيبال": "sibal",
    "سيليكون": "silicone",
    "سليكون": "silicone",
    "تفلون": "teflon",
    "كابتون": "kapton",
    "نومكس": "nomex",
    "اكريليك": "pmma acrylic",
    "بلاستيك": "pmma plastic",
    "ميثان": "methane ch4",
    "ايثان": "ethane c2h6",
    "ايثيلين": "ethylene c2h4",
    "بروبان": "propane",
    "بيوتان": "butane",
    "نيتروجين": "nitrogen",
    "اوزون": "ozone",
    "سمك": "thickness",
    "طول": "length",
    "عرض": "width",
    "حراره": "temperature peak burner",
    "لهب": "flame",
    "حريق": "fire",
    "دخان": "smoke aerosol",
    "جزيئات": "particles particulate",
    "قطرات": "droplets",
    "بارد": "cool",
    "ضغط": "pressure bar",
    "هدف": "objective goal",
    "نتيجه": "results",
    "نتايج": "results",
    "نتائج": "results",
    "طريقه": "execution method",
    "تنفيذ": "execution",
    "استنتاج": "conclusion",
    "سلامه": "safety tip",
    "نصيحه": "safety tip",
    "فرق": "compare difference",
    "مقارنه": "compare difference",
    "سبب": "cause why",
    "لماذا": "cause why",
    "ليه": "cause why",
    "انفجار": "explosion exploded",
    "انفجر": "explosion exploded",
    "انطفاء": "extinction extinguished",
    "اخماد": "suppression",
    "اطفاء": "suppression extinguish",
    "ابولو": "apollo",
    "مير": "mir",
    "رواد": "astronauts crew",
    "رائد": "astronaut",
    "طاقم": "crew",
    "خزان": "tank",
    "كاشف": "detector",
    "بدله": "suit gear",
    "كم": "how many total count",
    "عدد": "total count number",
    "متوسط": "average",
    "مؤلف": "authors",
    "مؤلفين": "authors",
    "كتاب": "guide",
    "دليل": "guide",
    "اطول": "longer",
    "اسرع": "faster accelerated",
    "جاذبيه": "gravity microgravity",
    "فضاء": "space",
    "كربون": "carbon monoxide co",
}


def _normalize_arabic(text: str) -> str:
    # Normalize Arabic-Indic digits to ASCII
    trans_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")
    s = text.translate(trans_digits)
    # Remove Arabic diacritics
    s = re.sub(r"[\u064B-\u065F\u0670]", "", s)
    # Normalize Alef, Teh Marbuta, Alef Maksura, Hamza
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    return s


def _clean_val(val) -> str:
    s = str(val).replace("٫", ".").strip()
    return "" if s.lower() in ("nan", "none", "") else s


def _expand_query_with_arabic_hints(query: str) -> str:
    norm = _normalize_arabic(query)
    lower_norm = norm.lower()
    extra: List[str] = []

    for ar_phrase, en_terms in ARABIC_PHRASE_MAP.items():
        if ar_phrase in lower_norm:
            extra.append(en_terms)

    # Check Arabic words (with and without leading "ال")
    ar_tokens = re.findall(r"[\u0600-\u06FF]+", lower_norm)
    for tok in ar_tokens:
        candidates = [tok]
        if tok.startswith("ال") and len(tok) > 3:
            candidates.append(tok[2:])
        if tok.startswith("وال") and len(tok) > 4:
            candidates.append(tok[3:])
        if tok.startswith("بال") and len(tok) > 4:
            candidates.append(tok[3:])
        if tok.startswith("لل") and len(tok) > 3:
            candidates.append(tok[2:])
        for cand in candidates:
            if cand in ARABIC_WORD_MAP:
                extra.append(ARABIC_WORD_MAP[cand])

    if extra:
        return f"{norm} {' '.join(extra)}".strip()
    return norm


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_.-]+", text.lower())


def build_base_knowledge_chunks() -> List[Dict[str, str]]:
    """Builds baseline knowledge chunks from Experiments, Stories, Apps, and Core PDF/Excel summaries."""
    chunks: List[Dict[str, str]] = list(CORE_DOC_CHUNKS)

    for exp in EXPERIMENTS:
        chunks.append(
            {
                "source": f"Experiment {exp['code']} - {exp['name']}",
                "text": (
                    f"Investigation Code: {exp['code']} | Name: {exp['name']} | "
                    f"Category: {exp['category']} | Total Cleaned Tests: {exp['total_tests']} | "
                    f"Average O2: {exp['avg_o2']}. "
                    f"Objective: {exp['objective']} "
                    f"Execution Method: {exp['execution']} "
                    f"Results: {exp['results']} "
                    f"Scientific Conclusion: {exp['conclusion']} "
                    f"Safety Tip: {exp['safety_tip']}"
                ),
            }
        )

    for story in STORIES:
        chunks.append(
            {
                "source": f"Story: {story['title']}",
                "text": f"{story['title']} ({story['subtitle']}): {story['content']}",
            }
        )

    for app in NASA_APPLICATIONS:
        chunks.append(
            {
                "source": f"NASA Application: {app['title']}",
                "text": f"{app['title']} ({app['subtitle']}): {app['content']}",
            }
        )

    return chunks


def extract_excel_chunks(excel_paths: List[str]) -> Tuple[List[Dict[str, str]], Dict[str, pd.DataFrame]]:
    """Reads all sheets from any local/uploaded Excel files into chunks and DataFrames."""
    chunks: List[Dict[str, str]] = []
    loaded_sheets: Dict[str, pd.DataFrame] = {}

    for path in excel_paths:
        try:
            xls = pd.ExcelFile(path)
            fname = os.path.basename(path)
            for sheet_name in xls.sheet_names:
                df = xls.parse(sheet_name)
                if df.empty:
                    continue
                if sheet_name not in loaded_sheets or len(df) > len(loaded_sheets[sheet_name]):
                    loaded_sheets[sheet_name] = df

                records = df.fillna("").astype(str).to_dict(orient="records")
                batch_size = 3
                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]
                    lines = []
                    for row in batch:
                        compact = " | ".join(
                            f"{k}: {_clean_val(v)}"
                            for k, v in row.items()
                            if _clean_val(v) != ""
                        )
                        if compact:
                            lines.append(compact)
                    if lines:
                        chunks.append(
                            {
                                "source": f"Excel ({fname} -> {sheet_name}, rows {i+1}-{i+len(batch)})",
                                "text": "\n".join(lines),
                            }
                        )
        except Exception:
            continue

    return chunks, loaded_sheets


def extract_pdf_chunks(pdf_paths: List[str]) -> List[Dict[str, str]]:
    """Extracts page-level text chunks from any local/uploaded PDF files."""
    if PdfReader is None:
        return []
    chunks: List[Dict[str, str]] = []
    for path in pdf_paths:
        try:
            reader = PdfReader(path)
            fname = os.path.basename(path)
            for idx, page in enumerate(reader.pages, start=1):
                txt = (page.extract_text() or "").strip()
                if txt:
                    chunks.append(
                        {
                            "source": f"PDF ({fname}, page {idx})",
                            "text": txt,
                        }
                    )
        except Exception:
            continue
    return chunks


def discover_local_files(directory: str = ".") -> Tuple[List[str], List[str]]:
    """Finds .xlsx and .pdf files in the root directory and ./uploaded_kb/."""
    excels = sorted(
        list(dict.fromkeys(
            glob.glob(os.path.join(directory, "*.xlsx"))
            + glob.glob(os.path.join(directory, "uploaded_kb", "*.xlsx"))
        ))
    )
    pdfs = sorted(
        list(dict.fromkeys(
            glob.glob(os.path.join(directory, "*.pdf"))
            + glob.glob(os.path.join(directory, "uploaded_kb", "*.pdf"))
        ))
    )
    return excels, pdfs


def _detect_mentioned_experiments(expanded_query: str) -> List[Dict]:
    q_lower = expanded_query.lower()
    matched = []
    for exp in EXPERIMENTS:
        if exp["code"].lower() in q_lower or any(alias in q_lower for alias in exp["aliases"]):
            matched.append(exp)
    return matched


def _find_matching_excel_rows(
    query: str,
    excel_sheets: Optional[Dict[str, pd.DataFrame]],
    mentioned_codes: List[str],
) -> List[Tuple[str, Dict[str, str]]]:
    """Finds exact rows in Excel sheets matching sample/test IDs (S1, S2, 2-5, B14, CF1, etc.)."""
    if not excel_sheets:
        return []

    q_upper = _normalize_arabic(query).upper()
    sample_tokens = set(
        re.findall(
            r"\b(?:S\d+|B\d+[A-Z]?|M\d+|O\d+[A-Z]?|P\d+[A-Z]?|T\d+[A-Z]?|F\d+|"
            r"CF\d+|CT\d+|SAMPLE-\d+|DATA-\d+|\d+-\d+|\d{5}[A-Z]?\d*)\b",
            q_upper,
        )
    )
    if not sample_tokens:
        return []

    results: List[Tuple[str, Dict[str, str]]] = []
    seen_keys = set()

    ordered_sheets = []
    for code in mentioned_codes:
        if code in excel_sheets:
            ordered_sheets.append((code, excel_sheets[code]))
    if "Master_Unified_Data" in excel_sheets:
        ordered_sheets.append(("Master_Unified_Data", excel_sheets["Master_Unified_Data"]))
    for sname, df in excel_sheets.items():
        if sname not in dict(ordered_sheets) and sname != "Summary_Dashboard":
            ordered_sheets.append((sname, df))

    for sname, df in ordered_sheets:
        id_cols = [
            c for c in df.columns
            if any(k in str(c).lower() for k in ("sample", "test_or_sample", "id"))
        ]
        if not id_cols:
            continue

        for _, row in df.iterrows():
            row_code = _clean_val(row.get("Investigation_Code", ""))
            if mentioned_codes and row_code and row_code not in mentioned_codes:
                continue

            matched_id = ""
            for col in id_cols:
                cell_val = _clean_val(row.get(col, "")).upper()
                if not cell_val:
                    continue
                if cell_val in sample_tokens:
                    matched_id = cell_val
                    break

            if matched_id:
                clean_row = {
                    str(k): _clean_val(v)
                    for k, v in row.items()
                    if _clean_val(v) != ""
                }
                dedup_key = (
                    row_code or sname,
                    matched_id,
                    clean_row.get("Flow_Direction", clean_row.get("Flow Direction", "")),
                )
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    results.append((sname, clean_row))

    return results[:12]


def retrieve_relevant_context(
    query: str,
    chunks: List[Dict[str, str]],
    top_k: int = 5,
    excel_sheets: Optional[Dict[str, pd.DataFrame]] = None,
) -> List[Dict[str, str]]:
    """Keyword-overlap + domain-phrase + exact Excel row retriever."""
    expanded = _expand_query_with_arabic_hints(query)
    raw_tokens = _tokenize(expanded)
    q_tokens = [t for t in raw_tokens if t not in STOPWORDS and len(t) >= 2]
    if not q_tokens:
        return []

    mentioned_exps = _detect_mentioned_experiments(expanded)
    mentioned_codes = [e["code"] for e in mentioned_exps]

    exact_row_chunks: List[Dict[str, str]] = []
    matched_rows = _find_matching_excel_rows(query, excel_sheets, mentioned_codes)
    for sname, row_dict in matched_rows:
        compact = " | ".join(f"{k}: {v}" for k, v in row_dict.items())
        exact_row_chunks.append(
            {
                "source": f"Exact Excel Match ({sname})",
                "text": compact,
            }
        )

    q_counts = Counter(q_tokens)
    q_lower = expanded.lower()

    scored: List[Tuple[float, Dict[str, str]]] = []
    for ch in chunks:
        haystack = f"{ch['source']} {ch['text']}".lower()
        c_tokens = Counter(_tokenize(haystack))

        score = 0.0
        matched_high_signal = 0
        for tok, cnt in q_counts.items():
            if tok in c_tokens:
                weight = 0.5 if tok in LOW_SIGNAL_WORDS else (2.5 if len(tok) >= 4 else 1.5)
                if tok not in LOW_SIGNAL_WORDS:
                    matched_high_signal += 1
                score += min(c_tokens[tok], 3) * cnt * weight

        for code in re.findall(r"psi-\d+", q_lower):
            if code in haystack:
                score += 25.0
                matched_high_signal += 1

        for term in [
            "apollo 13", "apollo 1", "mir", "firefighters", "project fires",
            "fire detector", "saffire", "bass", "acme", "slice", "same",
            "stdce", "cool flame", "flex", "cir", "msg", "sibal", "pmma",
            "nomex", "silicone", "microgravity", "explosion", "sofb", "scwo",
        ]:
            if term in q_lower and term in haystack:
                score += 10.0
                matched_high_signal += 1

        if matched_high_signal > 0 and score >= 2.5:
            scored.append((score, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    combined = exact_row_chunks + [item[1] for item in scored]

    unique_chunks: List[Dict[str, str]] = []
    seen = set()
    for ch in combined:
        if ch["text"] not in seen:
            seen.add(ch["text"])
            unique_chunks.append(ch)
        if len(unique_chunks) >= top_k:
            break

    return unique_chunks


def _format_specific_row_answer(
    expanded_query: str, matched_rows: List[Tuple[str, Dict[str, str]]]
) -> str:
    """Returns ONLY the requested fields from matched Excel rows—zero extra fluff."""
    q = expanded_query.lower()

    asked_burn = any(w in q for w in ("burn time", "duration", "seconds", "how long"))
    asked_o2 = any(w in q for w in ("o2", "oxygen"))
    asked_flow = any(w in q for w in ("flow", "airflow", "direction", "concurrent", "opposed", "velocity", "speed"))
    asked_material = any(w in q for w in ("material", "fuel", "fabric"))
    asked_temp = any(w in q for w in ("temp", "temperature", "burner"))
    asked_co = any(w in q for w in (" co ", "carbon monoxide", "ppm"))
    asked_dimensions = any(w in q for w in ("thickness", "length", "width", "size"))
    asked_compare = any(w in q for w in ("compare", "difference", "vs"))

    specific_ask = any([asked_burn, asked_o2, asked_flow, asked_material, asked_temp, asked_co, asked_dimensions])

    lines: List[str] = []
    for sname, r in matched_rows:
        code = r.get("Investigation_Code", sname)
        sid = r.get("Test_or_Sample_ID") or r.get("Sample Number") or "Sample"
        mat = r.get("Fuel_or_Material") or r.get("Material") or ""
        burn = r.get("Burn_Time_sec") or r.get("Burn Time (s)") or ""
        o2 = r.get("O2_Percent") or r.get("Percent O2 (Note 1)") or ""
        flow = r.get("Air_Flow_cm_s") or r.get("Air Flow (cm/s)") or ""
        fdir = r.get("Flow_Direction") or r.get("Flow Direction") or ""
        obs = r.get("Key_Observations_or_Results") or ""

        parts = []
        if asked_burn or not specific_ask:
            if burn:
                unit = " s" if not str(burn).lower().endswith("s") and burn.replace(".", "").isdigit() else ""
                parts.append(f"**Burn Time:** {burn}{unit}")
        if asked_o2 or not specific_ask:
            if o2:
                parts.append(f"**O₂:** {o2}%")
        if asked_flow or asked_compare or not specific_ask:
            if flow or fdir:
                flow_str = f"{flow} cm/s" if flow and "cm/s" not in flow else flow
                parts.append(f"**Airflow:** {flow_str} ({fdir})".strip())
        if asked_material or not specific_ask:
            if mat:
                parts.append(f"**Material/Fuel:** {mat}")
        if asked_dimensions:
            for dim_k in ("Samle Thickness", "Sample Thickness", "Sample Length", "Sample Width (cm)"):
                if r.get(dim_k):
                    parts.append(f"**{dim_k.replace('Samle', 'Sample')}:** {r[dim_k]}")
        if (asked_temp or asked_co or not specific_ask) and obs:
            parts.append(f"**Observations:** {obs}")

        if not parts:
            parts = [f"**{k}:** {v}" for k, v in list(r.items())[:6]]

        lines.append(f"- **{code} — Sample `{sid}`:** " + " | ".join(parts))

    return "\n".join(lines)


def answer_from_knowledge_base_local(
    query: str,
    relevant_chunks: List[Dict[str, str]],
    excel_sheets: Optional[Dict[str, pd.DataFrame]] = None,
) -> str:
    """
    Focused, direct English grounded answer generator with zero unnecessary additions.
    Understands both English and Arabic questions and answers strictly in English.
    """
    if not relevant_chunks:
        return (
            "Insufficient information: The provided NASA combustion datasets, Researcher's Guide, "
            "and curated documents do not contain enough information to answer this question."
        )

    expanded = _expand_query_with_arabic_hints(query)
    q_lower = expanded.lower()
    mentioned_exps = _detect_mentioned_experiments(expanded)
    mentioned_codes = [e["code"] for e in mentioned_exps]

    # 1. Exact Excel sample/test row lookup (returns ONLY requested attributes)
    matched_rows = _find_matching_excel_rows(query, excel_sheets, mentioned_codes)
    if matched_rows:
        return _format_specific_row_answer(expanded, matched_rows)

    # 2. Specific attribute lookup on a mentioned experiment (returns ONLY requested fields)
    if mentioned_exps:
        asked_obj = any(w in q_lower for w in ("objective", "goal", "purpose"))
        asked_exec = any(w in q_lower for w in ("method", "execution", "how was", "conducted"))
        asked_res = any(w in q_lower for w in ("result", "results", "finding", "burn time", "duration", "discover", "happen"))
        asked_conc = any(w in q_lower for w in ("conclusion", "conclude"))
        asked_safe = any(w in q_lower for w in ("safety", "tip", "lesson", "prevent"))
        asked_stats = any(w in q_lower for w in ("how many", "total tests", "average o2", "count"))

        if any([asked_obj, asked_exec, asked_res, asked_conc, asked_safe, asked_stats]):
            replies = []
            for exp in mentioned_exps:
                pts = []
                if asked_stats:
                    pts.append(f"**Total Cleaned Tests:** {exp['total_tests']} | **Average O₂:** {exp['avg_o2']}")
                if asked_obj:
                    pts.append(f"**Objective:** {exp['objective']}")
                if asked_exec:
                    pts.append(f"**Execution Method:** {exp['execution']}")
                if asked_res:
                    pts.append(f"**Results:** {exp['results']}")
                if asked_conc:
                    pts.append(f"**Scientific Conclusion:** {exp['conclusion']}")
                if asked_safe:
                    pts.append(f"**Safety Tip:** {exp['safety_tip']}")
                replies.append(f"**{exp['code']} — {exp['name']}:**\n" + "\n".join(f"- {p}" for p in pts))
            return "\n\n".join(replies)

    # 3. Direct sentence extraction from top chunks (max 2 focused sentences unless comparison/list requested)
    q_keywords = {
        t for t in _tokenize(expanded)
        if t not in STOPWORDS and t not in LOW_SIGNAL_WORDS and len(t) >= 2
    }
    if not q_keywords:
        q_keywords = {t for t in _tokenize(expanded) if t not in STOPWORDS and len(t) >= 2}

    scored_sentences: List[Tuple[float, str]] = []
    seen = set()

    for ch in relevant_chunks[:3]:
        # Skip raw pipe-delimited Excel rows in prose mode unless there is no prose chunk
        if ch["source"].startswith("Excel (") and len(relevant_chunks) > 1:
            continue
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", ch["text"]) if s.strip()]
        for sent in sentences:
            if len(sent) < 15:
                continue
            s_tokens = set(_tokenize(sent))
            overlap_tokens = q_keywords & s_tokens
            if overlap_tokens:
                score = sum(2.0 if len(t) >= 4 else 1.0 for t in overlap_tokens)
                if sent not in seen:
                    seen.add(sent)
                    scored_sentences.append((score, sent))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    if not scored_sentences:
        return (
            "Insufficient information: The provided NASA combustion datasets, Researcher's Guide, "
            "and curated documents do not contain enough information to answer this question."
        )

    is_broad = any(w in q_lower for w in ("compare", "all", "list", "summary", "explain", "difference"))
    max_sentences = 3 if is_broad else 2

    top_score = scored_sentences[0][0]
    selected = [
        sent for sc, sent in scored_sentences[:max_sentences]
        if sc >= max(1.0, top_score * 0.6)
    ]
    return "\n\n".join(selected)