#!/usr/bin/env python3
"""
Seed word definitions for P–S words using Claude-generated data.

Usage:
    python scripts/seed_definitions_ps.py                # insert missing only
    python scripts/seed_definitions_ps.py --overwrite    # replace existing
    python scripts/seed_definitions_ps.py --csv          # also dump CSV
"""
import argparse
import asyncio
import csv
import os
import pathlib
import sys

import asyncpg
from dotenv import load_dotenv

load_dotenv()

_WORDS_FILE = pathlib.Path(__file__).parent.parent / "data" / "words.txt"

DEFINITIONS: dict[str, dict] = {

    # ── P ──────────────────────────────────────────────────────────────────

    "PAEAN": {"pos": "noun", "meaning": "a song of praise or triumph; an enthusiastic expression of praise", "example": "The critic wrote a paean to the director's latest film."},
    "PAGAN": {"pos": "noun", "meaning": "a person holding religious beliefs outside main world religions; a heathen", "example": "Ancient pagan festivals marked the change of seasons."},
    "PAINT": {"pos": "verb", "meaning": "to apply color to a surface; to create a picture with paint", "example": "She painted the front door a deep navy blue."},
    "PANDA": {"pos": "noun", "meaning": "a large black-and-white bear-like mammal native to China", "example": "The giant panda feeds almost exclusively on bamboo."},
    "PANEL": {"pos": "noun", "meaning": "a flat section of a surface; a group of people assembled to discuss or judge", "example": "A panel of experts reviewed the proposals."},
    "PANIC": {"pos": "noun", "meaning": "sudden uncontrollable fear causing irrational behavior", "example": "A fire alarm sent the crowd into panic."},
    "PANSY": {"pos": "noun", "meaning": "a garden plant with brightly colored flowers; a weak or timid person", "example": "Pansies bloomed in purple and yellow along the border."},
    "PAPER": {"pos": "noun", "meaning": "material manufactured in thin sheets from pulp; a newspaper; an essay", "example": "She submitted her research paper before the deadline."},
    "PARKA": {"pos": "noun", "meaning": "a large windproof hooded jacket, originally worn in arctic regions", "example": "She zipped up her parka against the biting wind."},
    "PARSE": {"pos": "verb", "meaning": "to analyze a sentence grammatically; to examine or interpret carefully", "example": "She paused to parse the legal language in the contract."},
    "PARTY": {"pos": "noun", "meaning": "a social gathering; a political group; one side in a legal agreement", "example": "The birthday party lasted well into the evening."},
    "PASTA": {"pos": "noun", "meaning": "an Italian food made from dough of flour and water, shaped into various forms", "example": "She made fresh pasta from scratch for Sunday dinner."},
    "PASTE": {"pos": "noun", "meaning": "a thick soft moist substance; adhesive glue; to stick using paste", "example": "He used paste to mount the photos in the album."},
    "PATCH": {"pos": "noun", "meaning": "a piece of material covering a hole; a small area; to mend", "example": "She sewed a patch over the tear in his jacket."},
    "PATIO": {"pos": "noun", "meaning": "a paved outdoor area adjoining a house", "example": "They ate breakfast on the sunny patio."},
    "PAUSE": {"pos": "verb", "meaning": "to stop temporarily before continuing; a break in speech or action", "example": "She paused dramatically before revealing the answer."},
    "PEACE": {"pos": "noun", "meaning": "freedom from disturbance; a state free from war", "example": "The treaty brought peace after decades of conflict."},
    "PEACH": {"pos": "noun", "meaning": "a round fruit with sweet flesh and a fuzzy skin; a pinkish-orange color", "example": "She bit into a ripe peach, juice running down her chin."},
    "PEARL": {"pos": "noun", "meaning": "a smooth lustrous gem formed inside a mollusk; something precious", "example": "She wore a single strand of pearls to the event."},
    "PECAN": {"pos": "noun", "meaning": "a smooth pinkish-brown nut from a North American tree", "example": "She made a pecan pie for Thanksgiving."},
    "PEDAL": {"pos": "noun", "meaning": "a foot-operated lever on a bicycle, piano, or machine", "example": "He pushed hard on the pedals climbing the hill."},
    "PENAL": {"pos": "adjective", "meaning": "relating to the punishment of crime; involving a legal penalty", "example": "Reforms to the penal code were long overdue."},
    "PENNY": {"pos": "noun", "meaning": "a coin worth one cent; a small British coin; a tiny sum", "example": "Every penny counted when they were saving for the house."},
    "PEONY": {"pos": "noun", "meaning": "a plant with large round fragrant flowers in red, pink, or white", "example": "Peonies filled the garden with a sweet heady scent."},
    "PERCH": {"pos": "noun", "meaning": "a place where a bird rests; a freshwater fish; a high position", "example": "The parrot returned to its perch after every flight."},
    "PERIL": {"pos": "noun", "meaning": "serious and immediate danger; a source of risk", "example": "The sailors knew the perils of rounding the cape."},
    "PERKY": {"pos": "adjective", "meaning": "cheerful and lively; self-confident and assertive", "example": "She was annoyingly perky first thing in the morning."},
    "PESKY": {"pos": "adjective", "meaning": "annoying and troublesome (informal)", "example": "Those pesky mosquitoes ruined the picnic."},
    "PESTO": {"pos": "noun", "meaning": "a sauce of crushed basil, pine nuts, garlic, olive oil, and cheese", "example": "She tossed the pasta with homemade pesto."},
    "PETAL": {"pos": "noun", "meaning": "a delicate flat part of a flower; a term of endearment", "example": "Rose petals were scattered across the path."},
    "PETTY": {"pos": "adjective", "meaning": "of little importance; giving undue importance to small matters", "example": "Don't let petty arguments ruin the holiday."},
    "PHASE": {"pos": "noun", "meaning": "a distinct period or stage in a process; to introduce gradually", "example": "The project moved into its second phase on schedule."},
    "PHONE": {"pos": "noun", "meaning": "a telephone; to call someone by telephone", "example": "She reached for her phone to check the time."},
    "PHONY": {"pos": "adjective", "meaning": "not genuine; fraudulent; a person who is not what they claim to be", "example": "His accent turned out to be completely phony."},
    "PHOTO": {"pos": "noun", "meaning": "a picture taken with a camera; a photograph", "example": "She framed the photo of their first holiday together."},
    "PIANO": {"pos": "noun", "meaning": "a large keyboard instrument with strings struck by felt-covered hammers", "example": "She practiced piano for two hours every morning."},
    "PIECE": {"pos": "noun", "meaning": "a portion of something; a single item; a work of art or music", "example": "He played a beautiful piece by Schubert."},
    "PIETY": {"pos": "noun", "meaning": "devout reverence toward God or religion; dutiful respect", "example": "She wore her piety quietly, without any display."},
    "PILOT": {"pos": "noun", "meaning": "a person who flies an aircraft; one who steers a ship; a trial episode", "example": "The pilot landed the plane smoothly in the crosswind."},
    "PINCH": {"pos": "verb", "meaning": "to grip tightly between finger and thumb; a small amount; a difficulty", "example": "In a pinch, vinegar works as a cleaning agent."},
    "PIQUE": {"pos": "noun", "meaning": "a feeling of irritation from wounded pride; to arouse interest", "example": "The mysterious title piqued her curiosity."},
    "PITCH": {"pos": "noun", "meaning": "the highness or lowness of a sound; a sports field; to throw; to sell persuasively", "example": "The sales pitch lasted twenty minutes."},
    "PITHY": {"pos": "adjective", "meaning": "concise and forcefully expressive; brief but meaningful", "example": "He gave a pithy response that said everything."},
    "PIVOT": {"pos": "noun", "meaning": "a fixed point supporting rotation; a crucial factor; to turn on a pivot", "example": "She pivoted her strategy after the first quarter results."},
    "PIXEL": {"pos": "noun", "meaning": "the smallest unit of a digital image or screen display", "example": "The photo was blurry because the resolution was too few pixels."},
    "PIXIE": {"pos": "noun", "meaning": "a supernatural being in folklore; a small mischievous fairy-like creature", "example": "The child dressed as a pixie for the school play."},
    "PIZZA": {"pos": "noun", "meaning": "a flat round bread base with toppings of tomato, cheese, and other ingredients", "example": "They ordered a pizza to celebrate finishing the project."},
    "PLACE": {"pos": "noun", "meaning": "a particular position or location; to put in a position", "example": "She found a place by the window and sat down."},
    "PLAID": {"pos": "noun", "meaning": "a pattern of crossed horizontal and vertical bands; tartan", "example": "He wore a plaid flannel shirt to the bonfire."},
    "PLAIN": {"pos": "adjective", "meaning": "not decorated; easy to understand; a large flat area of land", "example": "She preferred plain food with no sauces."},
    "PLANE": {"pos": "noun", "meaning": "an aircraft; a flat surface; a woodworking tool; to smooth wood", "example": "The plane touched down an hour ahead of schedule."},
    "PLANK": {"pos": "noun", "meaning": "a long flat piece of timber; a policy in a political platform", "example": "Education was a central plank of the manifesto."},
    "PLANT": {"pos": "noun", "meaning": "a living organism that grows in soil; a factory; to place in the ground", "example": "She watered every plant in the greenhouse."},
    "PLATE": {"pos": "noun", "meaning": "a flat dish for food; a thin flat sheet of metal; to coat with metal", "example": "He balanced the full plate carefully as he walked."},
    "PLAZA": {"pos": "noun", "meaning": "a public square or marketplace; a shopping centre", "example": "They arranged to meet at the fountain in the plaza."},
    "PLEAD": {"pos": "verb", "meaning": "to make an emotional appeal; to state formally in court", "example": "He pleaded not guilty to all charges."},
    "PLEAT": {"pos": "noun", "meaning": "a fold of fabric stitched in place; to fold in pleats", "example": "Her skirt had deep pleats at the front."},
    "PLUCK": {"pos": "verb", "meaning": "to pick a flower or fruit; to pull at strings; courage (informal)", "example": "It took pluck to stand up to the whole committee."},
    "PLUMB": {"pos": "adverb", "meaning": "exactly; at right angles to the horizontal; to understand fully", "example": "The post must be plumb or the fence will lean."},
    "PLUME": {"pos": "noun", "meaning": "a long prominent feather; a cloud of smoke rising into the air", "example": "A plume of black smoke rose above the horizon."},
    "PLUMP": {"pos": "adjective", "meaning": "full and rounded in form; slightly fat; to drop or sit heavily", "example": "She plumped the cushions and straightened the sofa."},
    "PLUSH": {"pos": "adjective", "meaning": "richly luxurious; a fabric with a soft velvet-like surface", "example": "The hotel suite was plush and elegantly furnished."},
    "POACH": {"pos": "verb", "meaning": "to cook gently in simmering liquid; to take something illegally", "example": "She poached eggs in barely simmering water."},
    "POINT": {"pos": "noun", "meaning": "a sharp tip; an argument or idea; a unit of scoring; to indicate direction", "example": "He made several excellent points in his argument."},
    "POISE": {"pos": "noun", "meaning": "graceful and elegant bearing; composure and self-assurance", "example": "She answered every difficult question with remarkable poise."},
    "POKER": {"pos": "noun", "meaning": "a card game involving betting; a metal rod for stirring a fire", "example": "He had a poker face you could never read."},
    "POLAR": {"pos": "adjective", "meaning": "relating to the poles of the earth; having two opposite qualities", "example": "Polar bears are perfectly adapted to arctic conditions."},
    "POLIO": {"pos": "noun", "meaning": "an infectious viral disease causing muscle weakness and sometimes paralysis", "example": "Polio vaccination campaigns eradicated the disease in most countries."},
    "POLKA": {"pos": "noun", "meaning": "a lively dance of Bohemian origin; a pattern of regularly spaced dots", "example": "She wore a white dress with a polka dot pattern."},
    "POLYP": {"pos": "noun", "meaning": "a small growth on a mucous membrane; a coral or sea anemone", "example": "The colonoscopy detected a small polyp."},
    "POSSE": {"pos": "noun", "meaning": "a group of people with a common interest; a sheriff's force (historical)", "example": "He arrived with his whole posse in tow."},
    "POSIT": {"pos": "verb", "meaning": "to put forward as fact or as a basis for argument; to assume", "example": "She posited that the anomaly was caused by interference."},
    "POUCH": {"pos": "noun", "meaning": "a small bag or pocket; the marsupial's abdominal pocket for young", "example": "The joey peeked out from its mother's pouch."},
    "POUND": {"pos": "noun", "meaning": "a unit of weight; British currency; to strike heavily and repeatedly", "example": "Rain pounded the roof throughout the night."},
    "POWER": {"pos": "noun", "meaning": "the ability to do something; political authority; electrical energy", "example": "Knowledge is power."},
    "PRANK": {"pos": "noun", "meaning": "a practical joke or trick", "example": "He pulled a prank that nobody found as funny as he did."},
    "PRAWN": {"pos": "noun", "meaning": "a marine crustacean resembling a large shrimp", "example": "She ordered garlic prawns as a starter."},
    "PREEN": {"pos": "verb", "meaning": "to clean and smooth feathers; to spend time making oneself look smart", "example": "She preened in the mirror before the big interview."},
    "PRESS": {"pos": "verb", "meaning": "to apply pressure to; to iron clothes; journalists collectively", "example": "The press gathered outside the courthouse."},
    "PRICE": {"pos": "noun", "meaning": "the amount of money expected for something; a cost or penalty", "example": "Success comes at a price she was willing to pay."},
    "PRIDE": {"pos": "noun", "meaning": "satisfaction in one's achievements; excessive self-esteem; a group of lions", "example": "She watched the graduates with pride."},
    "PRIME": {"pos": "adjective", "meaning": "of first importance; of the best quality; a prime number; to prepare", "example": "She was in the prime of her career."},
    "PRINT": {"pos": "verb", "meaning": "to produce text or images on paper; to write in block letters", "example": "Please print your name clearly at the top."},
    "PRIOR": {"pos": "adjective", "meaning": "existing or coming before; the head of a priory", "example": "Prior experience is essential for this role."},
    "PRISM": {"pos": "noun", "meaning": "a transparent solid that refracts light into a spectrum; any triangular prism shape", "example": "The prism split the white light into a rainbow."},
    "PRIVY": {"pos": "adjective", "meaning": "sharing in the knowledge of something secret; an outdoor toilet", "example": "Only three people were privy to the plan."},
    "PRIZE": {"pos": "noun", "meaning": "a reward for achievement; something highly valued; to value highly", "example": "She treasured the prize she had worked years to win."},
    "PROBE": {"pos": "verb", "meaning": "to physically explore something; to investigate thoroughly", "example": "Investigators probed the company's finances."},
    "PRONE": {"pos": "adjective", "meaning": "likely to suffer from something; lying face downward", "example": "He was prone to exaggeration."},
    "PROOF": {"pos": "noun", "meaning": "evidence establishing a fact; a trial print; the strength of alcohol", "example": "The proof of her theory came from the unexpected results."},
    "PROSE": {"pos": "noun", "meaning": "written or spoken language in ordinary form without metrical structure", "example": "His prose was economical and precise."},
    "PROUD": {"pos": "adjective", "meaning": "feeling deep satisfaction over something; having self-respect; arrogant", "example": "She was proud of everything her children had achieved."},
    "PROVE": {"pos": "verb", "meaning": "to demonstrate the truth of; to show to be correct", "example": "She set out to prove her theory was right."},
    "PROWL": {"pos": "verb", "meaning": "to move around quietly in search of prey or opportunity", "example": "A cat prowled the alleyway looking for mice."},
    "PROXY": {"pos": "noun", "meaning": "a person authorized to act on behalf of another; a substitute", "example": "She voted by proxy at the shareholders meeting."},
    "PRUDE": {"pos": "noun", "meaning": "a person who is easily shocked by sexual matters; overly modest", "example": "He called her a prude for being offended by the joke."},
    "PRUNE": {"pos": "verb", "meaning": "to trim a tree or shrub; to reduce by removing what is unwanted", "example": "She pruned the roses back hard in February."},
    "PSALM": {"pos": "noun", "meaning": "a sacred song or hymn from the Book of Psalms", "example": "The congregation sang a psalm before the sermon."},
    "PSYCH": {"pos": "verb", "meaning": "to intimidate mentally; to prepare psychologically; psychology (informal)", "example": "She psyched herself up before the big presentation."},
    "PULSE": {"pos": "noun", "meaning": "a rhythmic beat of the heart; the regular throb of an artery; edible seeds", "example": "The nurse took his pulse and noted it in the chart."},
    "PUNCH": {"pos": "verb", "meaning": "to strike with the fist; to make a hole in; a drink made from fruit juice", "example": "He punched above his weight in the negotiations."},
    "PUPIL": {"pos": "noun", "meaning": "a student being taught; the dark circular opening in the eye", "example": "The pupils dilated in the dim light."},
    "PUPPY": {"pos": "noun", "meaning": "a young dog", "example": "The puppy chewed everything in sight."},
    "PUREE": {"pos": "noun", "meaning": "a smooth cream of liquidized or sieved vegetables or fruit", "example": "She served the soup with a swirl of red pepper puree."},
    "PURGE": {"pos": "verb", "meaning": "to rid of unwanted elements; to remove people from an organization forcibly", "example": "The new leader purged the party of dissidents."},
    "PURSE": {"pos": "noun", "meaning": "a small bag for money; a sum offered as a prize; to press the lips together", "example": "She pursed her lips in disapproval."},
    "PUSHY": {"pos": "adjective", "meaning": "excessively assertive or ambitious in a way that annoys others", "example": "He was too pushy and it put people off."},
    "PYGMY": {"pos": "noun", "meaning": "a member of small-statured peoples; anything very small of its kind", "example": "Pygmy hippos are far smaller than their common relatives."},
    "PYLON": {"pos": "noun", "meaning": "a tall tower-like structure supporting electrical power cables", "example": "Pylons marched across the hillside in a long line."},
    "PYRES": {"pos": "noun", "meaning": "heaps of combustible material for burning a body as a funeral rite", "example": "Funeral pyres burned along the river at dusk."},

    # ── Q ──────────────────────────────────────────────────────────────────

    "QUACK": {"pos": "noun", "meaning": "the harsh sound a duck makes; a fraudulent doctor or medicine seller", "example": "He turned out to be a quack selling fake cures."},
    "QUAFF": {"pos": "verb", "meaning": "to drink heartily and with enjoyment", "example": "They quaffed cold beer after the long hike."},
    "QUAIL": {"pos": "noun", "meaning": "a small short-tailed game bird; to feel or show fear", "example": "She quailed at the thought of speaking in front of thousands."},
    "QUAKE": {"pos": "verb", "meaning": "to shake or tremble; an earthquake", "example": "The ground began to quake beneath their feet."},
    "QUALM": {"pos": "noun", "meaning": "an uneasy feeling about whether one is doing the right thing; a scruple", "example": "She had no qualms about voicing her opinion."},
    "QUARK": {"pos": "noun", "meaning": "a fundamental subatomic particle; a type of soft cheese", "example": "Quarks are the building blocks of protons and neutrons."},
    "QUART": {"pos": "noun", "meaning": "a unit of liquid capacity equal to a quarter of a gallon", "example": "He drank a full quart of water after the run."},
    "QUASH": {"pos": "verb", "meaning": "to reject or void; to put an end to; to suppress", "example": "The court quashed the conviction on appeal."},
    "QUEEN": {"pos": "noun", "meaning": "the female ruler of a state; the most powerful chess piece; a drag queen", "example": "The queen opened parliament with a formal address."},
    "QUEER": {"pos": "adjective", "meaning": "strange or odd; relating to sexuality outside the norm (now often reclaimed)", "example": "There was something queer about his reaction."},
    "QUELL": {"pos": "verb", "meaning": "to put an end to; to suppress or subdue; to calm", "example": "Police moved in to quell the disturbance."},
    "QUERY": {"pos": "noun", "meaning": "a question; a request for information; to put a question", "example": "She sent a query to customer support and waited days for a reply."},
    "QUEST": {"pos": "noun", "meaning": "a long or arduous search; a journey toward a goal", "example": "The quest for the perfect recipe took years."},
    "QUEUE": {"pos": "noun", "meaning": "a line of people or vehicles waiting their turn", "example": "The queue stretched around the block."},
    "QUICK": {"pos": "adjective", "meaning": "moving fast; done in a short time; mentally agile", "example": "She had a quick mind and saw the solution immediately."},
    "QUIET": {"pos": "adjective", "meaning": "making little or no noise; calm and undisturbed", "example": "The library was blessedly quiet on a Tuesday morning."},
    "QUIFF": {"pos": "noun", "meaning": "a piece of hair brushed upward or backward from the forehead", "example": "He styled his quiff with pomade every morning."},
    "QUILL": {"pos": "noun", "meaning": "the hollow shaft of a feather; a pen made from this; a porcupine's spine", "example": "Letters were once written with a goose quill."},
    "QUILT": {"pos": "noun", "meaning": "a padded bed cover made of fabric layers stitched together", "example": "She curled up under the old patchwork quilt."},
    "QUIRK": {"pos": "noun", "meaning": "a peculiar behavioral habit; an unexpected twist", "example": "His quirks were endearing once you got used to them."},
    "QUITE": {"pos": "adverb", "meaning": "to the utmost degree; fairly or moderately", "example": "It was quite warm for October."},
    "QUOTA": {"pos": "noun", "meaning": "a fixed share of something to be done or achieved", "example": "Sales staff were under pressure to meet their weekly quota."},
    "QUOTE": {"pos": "verb", "meaning": "to repeat words said or written by another; a cited passage; a price estimate", "example": "She quoted the poet's most famous line."},

    # ── R ──────────────────────────────────────────────────────────────────

    "RABBI": {"pos": "noun", "meaning": "a Jewish scholar or teacher; the spiritual leader of a Jewish congregation", "example": "The rabbi led the congregation in prayer."},
    "RABID": {"pos": "adjective", "meaning": "having rabies; extreme and fanatical in belief", "example": "A rabid fan camped overnight to get front-row seats."},
    "RADAR": {"pos": "noun", "meaning": "a system using radio waves to detect objects; awareness of something", "example": "The new artist was already on everyone's radar."},
    "RADIO": {"pos": "noun", "meaning": "a device for receiving broadcast audio; wireless communication", "example": "She listened to the morning news on the radio."},
    "RADON": {"pos": "noun", "meaning": "a radioactive inert gas produced by the decay of radium", "example": "Radon can accumulate in poorly ventilated basements."},
    "RALLY": {"pos": "verb", "meaning": "to come together again; to recover strength; a mass meeting of supporters", "example": "Thousands attended the political rally."},
    "RAMEN": {"pos": "noun", "meaning": "Japanese noodle soup with broth, meat, and vegetables", "example": "She warmed up with a bowl of rich ramen after the cold walk."},
    "RANCH": {"pos": "noun", "meaning": "a large farm for raising cattle or other livestock", "example": "The ranch stretched across thousands of acres of grassland."},
    "RANGE": {"pos": "noun", "meaning": "the area over which something extends; a variety; a mountain chain; to vary", "example": "The range of colors was breathtaking."},
    "RAPID": {"pos": "adjective", "meaning": "happening in a short time; moving quickly", "example": "She made rapid progress in her first month."},
    "RAVEN": {"pos": "noun", "meaning": "a large black crow; a glossy black color", "example": "A raven perched on the castle wall and watched them."},
    "RAYON": {"pos": "noun", "meaning": "a synthetic fiber made from cellulose; fabric woven from this", "example": "The blouse was made of soft rayon."},
    "REACH": {"pos": "verb", "meaning": "to stretch out to touch; to arrive at; the extent of reach", "example": "She reached for the top shelf without a step."},
    "REACT": {"pos": "verb", "meaning": "to respond to something; to undergo a chemical reaction", "example": "How you react to failure determines your success."},
    "READY": {"pos": "adjective", "meaning": "prepared for action; willing to do something", "example": "Everything was ready for the big launch."},
    "REALM": {"pos": "noun", "meaning": "a kingdom; a field or domain of activity", "example": "She moved effortlessly in the realm of international diplomacy."},
    "REBEL": {"pos": "noun", "meaning": "a person who resists authority; to rise against established power", "example": "She was always a rebel who questioned every rule."},
    "REFER": {"pos": "verb", "meaning": "to direct attention to; to send for treatment; to look something up", "example": "I'll refer you to the relevant chapter."},
    "REGAL": {"pos": "adjective", "meaning": "relating to or fit for a king or queen; magnificent", "example": "She carried herself with regal grace."},
    "REHAB": {"pos": "noun", "meaning": "a course of treatment for drug or alcohol addiction; physical rehabilitation", "example": "He spent six weeks in rehab after the accident."},
    "REIGN": {"pos": "verb", "meaning": "to rule as a king or queen; to be the dominant force", "example": "Silence reigned over the empty house."},
    "RELAX": {"pos": "verb", "meaning": "to become less tense; to rest; to make a rule less strict", "example": "She finally relaxed once the exam was over."},
    "RELAY": {"pos": "noun", "meaning": "a race where team members each run a section; to pass a message along", "example": "They won gold in the four-by-four relay."},
    "RELIC": {"pos": "noun", "meaning": "an object from the past; a surviving object of historical interest", "example": "The museum displayed relics from the Bronze Age."},
    "REMIT": {"pos": "verb", "meaning": "to send money in payment; to cancel a debt; the task assigned to someone", "example": "This issue falls outside our remit."},
    "RENEW": {"pos": "verb", "meaning": "to resume after an interruption; to extend the period of validity", "example": "She renewed her passport before the trip."},
    "REPAY": {"pos": "verb", "meaning": "to pay back money; to reward or retaliate", "example": "I'll repay your kindness one day."},
    "REPEL": {"pos": "verb", "meaning": "to drive away; to be repellent to; to resist invasion", "example": "Citronella is said to repel mosquitoes."},
    "REPLY": {"pos": "verb", "meaning": "to say or write in response; an answer", "example": "She replied within minutes of receiving the message."},
    "RERUN": {"pos": "noun", "meaning": "a repeat broadcast; something done over again", "example": "The station played reruns of the classic sitcom."},
    "RESIN": {"pos": "noun", "meaning": "a sticky substance secreted by plants; a synthetic polymer used in plastics", "example": "Pine resin dripped down the bark."},
    "RETRO": {"pos": "adjective", "meaning": "imitative of a style from the recent past; nostalgically old-fashioned", "example": "The café had a retro feel with its vinyl booths."},
    "REVEL": {"pos": "verb", "meaning": "to enjoy oneself in a lively way; to take great delight in", "example": "She reveled in the unexpected success."},
    "RHINO": {"pos": "noun", "meaning": "a large thick-skinned herbivore with one or two horns; money (informal)", "example": "The white rhino is critically endangered."},
    "RHYME": {"pos": "noun", "meaning": "words with corresponding sounds at the end; a short poem with such words", "example": "She made up a rhyme to help the children remember the dates."},
    "RIDGE": {"pos": "noun", "meaning": "a long narrow hilltop or mountain crest; a raised strip on a surface", "example": "They hiked along the ridge with views on both sides."},
    "RIFLE": {"pos": "noun", "meaning": "a long-barreled gun fired from the shoulder; to search through roughly", "example": "Someone had rifled through her desk drawers."},
    "RIGHT": {"pos": "adjective", "meaning": "morally good; correct; on the east side when facing north", "example": "She was right to trust her instinct."},
    "RIGID": {"pos": "adjective", "meaning": "not flexible; unable to be bent; strictly maintained", "example": "He followed a rigid daily schedule."},
    "RIGOR": {"pos": "noun", "meaning": "the quality of being thorough and careful; strict precision", "example": "Academic rigor was expected of every student."},
    "RINSE": {"pos": "verb", "meaning": "to wash lightly; to remove soap or impurities with clean water", "example": "Rinse the vegetables before adding them to the pot."},
    "RISKY": {"pos": "adjective", "meaning": "involving the possibility of danger or loss", "example": "It was a risky move but it paid off."},
    "RIVAL": {"pos": "noun", "meaning": "a person or group competing with another for the same objective", "example": "The two rivals shook hands before the final match."},
    "RIVER": {"pos": "noun", "meaning": "a large natural stream of water flowing to the sea or a lake", "example": "The river wound through the valley for miles."},
    "RIVET": {"pos": "verb", "meaning": "to hold firmly; to completely fascinate; a metal fastener", "example": "The documentary riveted the audience from start to finish."},
    "ROAST": {"pos": "verb", "meaning": "to cook by dry heat in an oven; to tease someone harshly (informal)", "example": "They roasted the chicken with garlic and lemon."},
    "ROBIN": {"pos": "noun", "meaning": "a small songbird with a red breast, associated with Christmas", "example": "A robin sang in the bare branches outside the window."},
    "ROBOT": {"pos": "noun", "meaning": "an automated machine that can carry out complex tasks", "example": "The factory replaced many workers with robots."},
    "ROCKY": {"pos": "adjective", "meaning": "consisting of rock; unsteady; presenting difficulties", "example": "Their relationship had a rocky start but settled down."},
    "RODEO": {"pos": "noun", "meaning": "an exhibition of cowboy skills such as riding and lasso work", "example": "Competitors traveled from across the state for the rodeo."},
    "ROGUE": {"pos": "noun", "meaning": "a dishonest person; something that behaves erratically", "example": "A rogue elephant had wandered from the herd."},
    "ROOMY": {"pos": "adjective", "meaning": "having plenty of space; spacious", "example": "The new apartment was roomy and full of light."},
    "ROOST": {"pos": "verb", "meaning": "to settle for sleep, as a bird does; a bird's resting place", "example": "Chickens returned to roost at sunset."},
    "ROUGE": {"pos": "noun", "meaning": "a red powder or cream used as cosmetic blusher", "example": "She dusted rouge lightly across her cheekbones."},
    "ROUGH": {"pos": "adjective", "meaning": "not smooth; not gentle; approximately; hard and unpleasant", "example": "It had been a rough week and she needed rest."},
    "ROUND": {"pos": "adjective", "meaning": "shaped like a circle; a complete stage in a competition; to make circular", "example": "They made it through to the next round."},
    "ROUSE": {"pos": "verb", "meaning": "to wake from sleep; to stir up or excite", "example": "A loud bang roused them from sleep."},
    "ROUTE": {"pos": "noun", "meaning": "a way or course taken to reach a destination", "example": "She chose the scenic route along the coast."},
    "ROWDY": {"pos": "adjective", "meaning": "noisy and disorderly; boisterous", "example": "The rowdy crowd needed to be calmed down."},
    "ROYAL": {"pos": "adjective", "meaning": "relating to a king or queen; magnificent in scale", "example": "The royal family attended the ceremony in full."},
    "RUGBY": {"pos": "noun", "meaning": "a team sport played with an oval ball that can be carried or kicked", "example": "He played rugby at county level for three years."},
    "RULER": {"pos": "noun", "meaning": "a person who rules; a measuring stick with marked units", "example": "She used a ruler to draw straight lines."},
    "RUMBA": {"pos": "noun", "meaning": "a rhythmic Cuban dance; the music for such a dance", "example": "They took rumba classes before their Caribbean cruise."},
    "RUMOR": {"pos": "noun", "meaning": "information spread without confirmation of its truth", "example": "Rumors of a merger sent the share price soaring."},
    "RUNES": {"pos": "noun", "meaning": "letters in ancient Germanic alphabets; mysterious symbols with power", "example": "The stone was carved with runes of an unknown meaning."},
    "RURAL": {"pos": "adjective", "meaning": "in, relating to, or characteristic of the countryside", "example": "She longed for a quieter rural life after years in the city."},
    "RUSTY": {"pos": "adjective", "meaning": "affected by rust; impaired by lack of practice", "example": "Her French was a bit rusty after ten years away."},

    # ── S ──────────────────────────────────────────────────────────────────

    "SABER": {"pos": "noun", "meaning": "a heavy cavalry sword with a curved blade; a type of fencing sword", "example": "The hussar drew his saber and charged."},
    "SABLE": {"pos": "noun", "meaning": "a small carnivorous mammal valued for its fur; the color black in heraldry", "example": "The coat was trimmed with sable fur."},
    "SAINT": {"pos": "noun", "meaning": "a holy person officially recognized by a church; a very virtuous person", "example": "She was no saint, but she was honest."},
    "SALAD": {"pos": "noun", "meaning": "a cold dish of raw vegetables; a mixture", "example": "She tossed a green salad with lemon vinaigrette."},
    "SALON": {"pos": "noun", "meaning": "a hairdressing establishment; a regular social gathering of prominent people", "example": "She had her hair done at a salon in the city."},
    "SALSA": {"pos": "noun", "meaning": "a spicy tomato-based sauce; a Latin dance and music style", "example": "They took salsa classes on Tuesday evenings."},
    "SALTY": {"pos": "adjective", "meaning": "tasting of or containing salt; resentful or bitter (informal)", "example": "He was salty about losing the argument."},
    "SALVE": {"pos": "noun", "meaning": "a soothing ointment; something that soothes wounded feelings", "example": "The apology was salve to her wounded pride."},
    "SAMBA": {"pos": "noun", "meaning": "a Brazilian dance of African origin with a fast rhythm", "example": "The carnival burst into life with samba dancers."},
    "SASSY": {"pos": "adjective", "meaning": "boldly self-confident; impudent in an endearing way", "example": "She gave a sassy reply that made everyone laugh."},
    "SATIN": {"pos": "noun", "meaning": "a smooth glossy fabric with a sheen on one side", "example": "The bride wore a gown of ivory satin."},
    "SATYR": {"pos": "noun", "meaning": "in Greek myth, a woodland deity with a man's body and a goat's legs", "example": "A marble satyr danced at the edge of the fountain."},
    "SAUCE": {"pos": "noun", "meaning": "a liquid condiment served with food; impudence (British informal)", "example": "She poured a rich tomato sauce over the pasta."},
    "SAUCY": {"pos": "adjective", "meaning": "bold and sexually suggestive; impudent in an amusing way", "example": "The comedy had a saucy edge that delighted audiences."},
    "SAUNA": {"pos": "noun", "meaning": "a room heated to a high temperature used for bathing and relaxation", "example": "After skiing, they warmed up in the hotel sauna."},
    "SAVOR": {"pos": "verb", "meaning": "to enjoy food or an experience slowly and appreciatively", "example": "She savored every moment of the long weekend."},
    "SAVVY": {"pos": "adjective", "meaning": "shrewd and knowledgeable; practical understanding", "example": "She was politically savvy and never said more than necessary."},
    "SCALD": {"pos": "verb", "meaning": "to injure with boiling water or steam; to heat almost to boiling", "example": "Be careful not to scald yourself when pouring the water."},
    "SCALE": {"pos": "noun", "meaning": "the size of something; a weighing device; a fish's protective plate; to climb", "example": "The scale of the project was overwhelming."},
    "SCALP": {"pos": "noun", "meaning": "the skin covering the top of the head; to resell tickets at high prices", "example": "She massaged her scalp while shampooing."},
    "SCAMP": {"pos": "noun", "meaning": "a mischievous person, especially a child; a rascal", "example": "The little scamp had hidden the TV remote."},
    "SCANT": {"pos": "adjective", "meaning": "barely sufficient; less than is expected", "example": "She paid scant attention to the instructions."},
    "SCARE": {"pos": "verb", "meaning": "to cause fright; a sudden fear or alarm", "example": "The fox gave the chickens quite a scare."},
    "SCARF": {"pos": "noun", "meaning": "a strip of fabric worn around the neck or head; to eat rapidly (informal)", "example": "She wrapped a thick scarf around her neck."},
    "SCARY": {"pos": "adjective", "meaning": "causing fear or fright; frightening", "example": "The abandoned house was genuinely scary at night."},
    "SCENE": {"pos": "noun", "meaning": "a place where something happens; a section of a film; a public display of emotion", "example": "She arrived at the scene just after the accident."},
    "SCENT": {"pos": "noun", "meaning": "a distinctive pleasant smell; a trail left by an animal; perfume", "example": "The scent of pine filled the mountain air."},
    "SCOFF": {"pos": "verb", "meaning": "to speak scornfully; to eat rapidly (British informal)", "example": "He scoffed at the idea that it could fail."},
    "SCOLD": {"pos": "verb", "meaning": "to reprimand or rebuke angrily", "example": "She was scolded for arriving late."},
    "SCONE": {"pos": "noun", "meaning": "a small light baked good, typically eaten with butter and jam", "example": "She served warm scones with clotted cream and jam."},
    "SCOOP": {"pos": "noun", "meaning": "a spoon-like utensil for scooping; an exclusive news story", "example": "The journalist got the scoop of the year."},
    "SCOPE": {"pos": "noun", "meaning": "the extent of the area covered; an optical instrument; opportunity", "example": "The scope of her research was impressively broad."},
    "SCORE": {"pos": "noun", "meaning": "the number of points in a game; a musical notation; to achieve", "example": "The final score was three goals to two."},
    "SCORN": {"pos": "noun", "meaning": "open contempt; the feeling that someone is unworthy", "example": "She dismissed the suggestion with scorn."},
    "SCOUR": {"pos": "verb", "meaning": "to clean by rubbing hard; to search an area thoroughly", "example": "She scoured every charity shop for the perfect dress."},
    "SCOUT": {"pos": "noun", "meaning": "a person sent ahead to gather information; a talent spotter; to explore", "example": "The talent scout spotted her at a local audition."},
    "SCOWL": {"pos": "verb", "meaning": "to frown in an angry or displeased way", "example": "He scowled at the interruption."},
    "SCRAM": {"pos": "verb", "meaning": "to leave quickly; to go away (informal)", "example": "Get out of here! Scram!"},
    "SCRAP": {"pos": "noun", "meaning": "a small piece; waste material; a fight or argument; to discard", "example": "They collected every scrap of information they could find."},
    "SCREW": {"pos": "noun", "meaning": "a metal fastener with a spiral thread; to fasten with screws", "example": "The shelf held firm with four sturdy screws."},
    "SCRUB": {"pos": "verb", "meaning": "to clean by rubbing hard; to cancel (informal)", "example": "She scrubbed the floor until it gleamed."},
    "SCRUM": {"pos": "noun", "meaning": "a rugby formation; a disorderly crowd; a short agile development method", "example": "The team adopted scrum to improve their delivery speed."},
    "SCUBA": {"pos": "noun", "meaning": "self-contained underwater breathing apparatus used for diving", "example": "They went scuba diving on the coral reef."},
    "SEDAN": {"pos": "noun", "meaning": "a car with a closed body and separate boot; a historical enclosed chair", "example": "He pulled up in a sleek black sedan."},
    "SEIZE": {"pos": "verb", "meaning": "to grab suddenly; to take by force; to take legal possession", "example": "She seized the opportunity with both hands."},
    "SENSE": {"pos": "noun", "meaning": "any of the faculties of hearing, sight, etc.; an awareness; good judgment", "example": "She had the good sense to leave before it turned ugly."},
    "SEPIA": {"pos": "noun", "meaning": "a reddish-brown color associated with old photographs; a brown pigment", "example": "The old photographs had a warm sepia tone."},
    "SERUM": {"pos": "noun", "meaning": "the clear fluid separated from blood; a medical preparation for immunity", "example": "An anti-venom serum was administered immediately."},
    "SERVE": {"pos": "verb", "meaning": "to work for; to provide food or drink; to deliver a legal document", "example": "She served the committee faithfully for ten years."},
    "SETUP": {"pos": "noun", "meaning": "the way something is organized; an arrangement; a trap (informal)", "example": "The studio setup was complex but efficient."},
    "SEVEN": {"pos": "noun", "meaning": "the number 7; a group of seven", "example": "The seven continents span the globe."},
    "SEVER": {"pos": "verb", "meaning": "to cut; to put an end to a connection", "example": "They severed ties with the supplier after the dispute."},
    "SHADE": {"pos": "noun", "meaning": "partial darkness caused by blocking light; a color variant; a ghost", "example": "They rested in the shade of a large oak tree."},
    "SHAFT": {"pos": "noun", "meaning": "a long narrow passage; a rotating rod; a beam of light; to cheat (informal)", "example": "Light fell in a single shaft through the narrow window."},
    "SHAKE": {"pos": "verb", "meaning": "to move with rapid short movements; to disturb or shock", "example": "She shook her head to clear her thoughts."},
    "SHAKY": {"pos": "adjective", "meaning": "shaking; unstable; not reliable", "example": "The evidence for the theory was shaky at best."},
    "SHALE": {"pos": "noun", "meaning": "a fine-grained sedimentary rock that splits easily into layers", "example": "The cliff was made of crumbling shale."},
    "SHAME": {"pos": "noun", "meaning": "the feeling of humiliation from a wrong act; a regrettable situation", "example": "She felt a deep shame for what she had done."},
    "SHAPE": {"pos": "noun", "meaning": "the form of an object; to give form to; physical condition", "example": "She was in excellent shape after months of training."},
    "SHARE": {"pos": "verb", "meaning": "to divide and distribute; to use together; a unit of company ownership", "example": "She shared what she knew with the rest of the team."},
    "SHARK": {"pos": "noun", "meaning": "a large predatory ocean fish; a dishonest person; an expert (informal)", "example": "He was a card shark who rarely lost."},
    "SHARP": {"pos": "adjective", "meaning": "having a fine edge; quick and intelligent; abrupt and harsh", "example": "She gave him a sharp look across the table."},
    "SHAVE": {"pos": "verb", "meaning": "to cut hair close to the skin; to reduce by a small amount", "example": "He shaved every morning without fail."},
    "SHAWL": {"pos": "noun", "meaning": "a piece of fabric worn over the shoulders or head", "example": "She pulled the shawl tight against the evening chill."},
    "SHEAF": {"pos": "noun", "meaning": "a bundle of grain stalks; a bundle of papers", "example": "She handed him a sheaf of documents to review."},
    "SHEAR": {"pos": "verb", "meaning": "to cut or clip; to strip by cutting; to break under sideways force", "example": "Farmers sheared the sheep before the summer heat."},
    "SHEEP": {"pos": "noun", "meaning": "a woolly domesticated ruminant; a timid follower of others", "example": "A flock of sheep grazed on the hillside."},
    "SHELF": {"pos": "noun", "meaning": "a flat horizontal surface fixed to a wall for storing items", "example": "She lined the shelf with her collection of paperbacks."},
    "SHELL": {"pos": "noun", "meaning": "the hard outer covering of a nut or egg; to bombard with artillery", "example": "She combed the beach for interesting shells."},
    "SHIFT": {"pos": "noun", "meaning": "a movement or change; a period of work; to move", "example": "A shift in public opinion changed everything."},
    "SHINE": {"pos": "verb", "meaning": "to emit or reflect light; to excel; to polish", "example": "She shone at every subject she attempted."},
    "SHIRE": {"pos": "noun", "meaning": "a county in England; a large draft horse breed", "example": "They drove through the English shires in the summer."},
    "SHIRK": {"pos": "verb", "meaning": "to avoid a duty or responsibility", "example": "He never shirked hard work."},
    "SHIRT": {"pos": "noun", "meaning": "a garment for the upper body with a collar, sleeves, and buttons", "example": "He rolled up his shirt sleeves and got to work."},
    "SHOCK": {"pos": "noun", "meaning": "a sudden disturbing event; an electric jolt; a bushy mass of hair", "example": "The news came as a complete shock to everyone."},
    "SHORE": {"pos": "noun", "meaning": "the land along the edge of a sea or lake; to support with a prop", "example": "They walked along the shore as the tide came in."},
    "SHORT": {"pos": "adjective", "meaning": "of less than average length or duration; lacking enough", "example": "They were short of staff during the holiday season."},
    "SHOUT": {"pos": "verb", "meaning": "to call out loudly; a round of drinks (British informal)", "example": "She shouted across the room to get his attention."},
    "SHOVE": {"pos": "verb", "meaning": "to push roughly; to put something carelessly", "example": "He shoved the papers into his bag and left."},
    "SHRED": {"pos": "verb", "meaning": "to tear into small pieces; to cut into thin strips", "example": "She shredded the old bank statements."},
    "SHREW": {"pos": "noun", "meaning": "a small mouse-like insectivore; a sharp-tongued scolding woman", "example": "She was called a shrew but was simply assertive."},
    "SHRUB": {"pos": "noun", "meaning": "a woody plant smaller than a tree with multiple stems", "example": "Flowering shrubs bordered the path."},
    "SHRUG": {"pos": "verb", "meaning": "to raise the shoulders to express indifference or uncertainty", "example": "He shrugged and said he didn't know the answer."},
    "SIEGE": {"pos": "noun", "meaning": "a military operation surrounding a place to force surrender", "example": "The castle fell after a six-month siege."},
    "SIEVE": {"pos": "noun", "meaning": "a utensil with a mesh for straining or separating; to put through a sieve", "example": "She sifted the flour through a fine sieve."},
    "SIGHT": {"pos": "noun", "meaning": "the ability to see; something seen; a device on a weapon for aiming", "example": "The view from the summit was a magnificent sight."},
    "SILKY": {"pos": "adjective", "meaning": "smooth and glossy like silk; softly persuasive", "example": "The dog had a long silky coat."},
    "SILLY": {"pos": "adjective", "meaning": "lacking in common sense; absurd and trivial", "example": "It was a silly misunderstanding that caused all the trouble."},
    "SINCE": {"pos": "preposition", "meaning": "from a point in the past until now; because", "example": "Things have changed a lot since then."},
    "SINEW": {"pos": "noun", "meaning": "a tendon connecting muscle to bone; strength and resilience", "example": "The task required sinew as much as brainpower."},
    "SIREN": {"pos": "noun", "meaning": "an alarm device producing a wailing sound; a dangerously alluring woman", "example": "The siren of an ambulance broke the quiet afternoon."},
    "SIXTH": {"pos": "noun", "meaning": "the ordinal form of six; one of six equal parts", "example": "She finished sixth in her first professional race."},
    "SIXTY": {"pos": "noun", "meaning": "the number 60; between fifty-nine and sixty-one", "example": "He retired at sixty with a full pension."},
    "SKATE": {"pos": "verb", "meaning": "to glide on ice or roller skates; to avoid a difficult subject", "example": "She skated over the uncomfortable topic."},
    "SKEIN": {"pos": "noun", "meaning": "a loosely coiled bundle of yarn; a tangled or complicated arrangement", "example": "She unwound the skein of wool carefully."},
    "SKILL": {"pos": "noun", "meaning": "the ability to do something well acquired through training or experience", "example": "Coding is a skill that takes years to master."},
    "SKULK": {"pos": "verb", "meaning": "to lurk or move stealthily to avoid detection", "example": "He skulked around the edges of the party."},
    "SKULL": {"pos": "noun", "meaning": "the bony framework of the head enclosing the brain", "example": "A skull and crossbones marked the poison."},
    "SKUNK": {"pos": "noun", "meaning": "a North American mammal that sprays a foul-smelling liquid in defense", "example": "The dog had a run-in with a skunk."},
    "SLACK": {"pos": "adjective", "meaning": "not taut; lacking effort; not busy; to become loose", "example": "She was accused of being slack in her work."},
    "SLANG": {"pos": "noun", "meaning": "informal words used in casual speech, often specific to a group", "example": "The teenagers used slang she couldn't understand."},
    "SLANT": {"pos": "noun", "meaning": "a sloping direction; a bias or particular point of view", "example": "The article had a distinctly political slant."},
    "SLASH": {"pos": "verb", "meaning": "to cut with a sweeping blow; to reduce drastically", "example": "The company slashed prices to clear old stock."},
    "SLATE": {"pos": "noun", "meaning": "a fine-grained grey-blue rock; a writing tablet; to criticize severely", "example": "The film was slated by every critic."},
    "SLAVE": {"pos": "noun", "meaning": "a person forced to work without freedom or pay; to work very hard", "example": "She slaved over the report all weekend."},
    "SLEEK": {"pos": "adjective", "meaning": "smooth and glossy; elegantly streamlined", "example": "The car's sleek lines turned heads wherever it went."},
    "SLEEP": {"pos": "verb", "meaning": "to rest in a state of reduced consciousness; to be dormant", "example": "She slept soundly for the first time in weeks."},
    "SLEET": {"pos": "noun", "meaning": "a mixture of rain and snow; to fall as sleet", "example": "Sleet battered the windows throughout the night."},
    "SLICE": {"pos": "noun", "meaning": "a thin flat piece cut from something; to cut into slices", "example": "She cut a thick slice of bread."},
    "SLICK": {"pos": "adjective", "meaning": "smooth and glossy; done efficiently; a patch of oil on water", "example": "His presentation was polished and slick."},
    "SLIDE": {"pos": "verb", "meaning": "to move smoothly; a playground structure for sliding; a photographic transparency", "example": "Stock prices continued to slide throughout the session."},
    "SLIME": {"pos": "noun", "meaning": "an unpleasantly moist and sticky substance", "example": "The pond's edge was covered in green slime."},
    "SLIMY": {"pos": "adjective", "meaning": "covered with slime; disgustingly obsequious (informal)", "example": "He gave her a slimy smile she didn't trust."},
    "SLING": {"pos": "noun", "meaning": "a bandage supporting an injured arm; a strap for throwing stones", "example": "She wore her arm in a sling for three weeks."},
    "SLOPE": {"pos": "noun", "meaning": "a surface tilted from horizontal; to be inclined at an angle", "example": "The gentle slope led down to the stream."},
    "SLOTH": {"pos": "noun", "meaning": "reluctance to work; laziness; a slow-moving tropical mammal", "example": "A three-toed sloth hung motionless from the branch."},
    "SLUMP": {"pos": "verb", "meaning": "to sit or fall heavily; to decrease suddenly in value", "example": "Sales slumped dramatically in the third quarter."},
    "SLURP": {"pos": "verb", "meaning": "to eat or drink with a loud sucking noise", "example": "He slurped his noodles enthusiastically."},
    "SLUSH": {"pos": "noun", "meaning": "partially melted snow or ice; mawkishly sentimental material", "example": "She picked her way through the grey street slush."},
    "SMACK": {"pos": "verb", "meaning": "to strike sharply; to have a trace of a quality; a sharp blow", "example": "It smacked of desperation to make such a move."},
    "SMALL": {"pos": "adjective", "meaning": "of little size; less than usual; humble", "example": "Small gestures often mean the most."},
    "SMART": {"pos": "adjective", "meaning": "intelligent; well-dressed; causing a stinging pain", "example": "She was the smartest person in the room."},
    "SMASH": {"pos": "verb", "meaning": "to break violently into pieces; a great success; a hard tennis shot", "example": "The film was a box-office smash."},
    "SMEAR": {"pos": "verb", "meaning": "to coat or mark untidily; to damage a reputation unfairly", "example": "The campaign tried to smear his reputation."},
    "SMELL": {"pos": "verb", "meaning": "to perceive an odor; to have a particular scent", "example": "The bakery smelled of warm bread and cinnamon."},
    "SMILE": {"pos": "verb", "meaning": "to form a pleased or kind expression by turning up the corners of the mouth", "example": "She smiled whenever she thought of that holiday."},
    "SMIRK": {"pos": "verb", "meaning": "to smile in a smug or self-satisfied way", "example": "He smirked when he knew he had won the argument."},
    "SMITH": {"pos": "noun", "meaning": "a person who works with metal; a craftsperson using forge or hammer", "example": "The blacksmith—a smith of great skill—shaped the horseshoe."},
    "SMOKE": {"pos": "noun", "meaning": "visible vapor from burning material; to inhale from a cigarette", "example": "Smoke drifted lazily from the chimney."},
    "SMOKY": {"pos": "adjective", "meaning": "filled with smoke; having the flavor of smoked food", "example": "The bar was small and rather smoky."},
    "SNACK": {"pos": "noun", "meaning": "a small amount of food eaten between meals", "example": "She grabbed a quick snack before heading out."},
    "SNAFU": {"pos": "noun", "meaning": "a confused or chaotic state; a disastrously mismanaged situation (informal)", "example": "The whole launch was a complete snafu."},
    "SNAIL": {"pos": "noun", "meaning": "a slow-moving mollusk with a spiral shell; a very slow person", "example": "The project moved at a snail's pace."},
    "SNAKE": {"pos": "noun", "meaning": "a long limbless reptile; a treacherous person; to move in a winding path", "example": "The queue snaked around the block."},
    "SNARE": {"pos": "noun", "meaning": "a trap for catching animals; something that traps or ensnares", "example": "He walked straight into the snare."},
    "SNARK": {"pos": "noun", "meaning": "sharp and critical remarks made with wit; sarcastic commentary (informal)", "example": "His review was full of snark but not much insight."},
    "SNARL": {"pos": "verb", "meaning": "to growl aggressively; to become tangled; to speak angrily", "example": "Traffic snarled at the intersection all afternoon."},
    "SNEAK": {"pos": "verb", "meaning": "to move or take secretly; a person who tells on others furtively", "example": "She sneaked a look at the answers."},
    "SNEER": {"pos": "verb", "meaning": "to smile or speak contemptuously; to show contempt", "example": "He sneered at the suggestion but privately agreed."},
    "SNIDE": {"pos": "adjective", "meaning": "derogatory in a subtle way; underhand", "example": "She made a snide remark about his outfit."},
    "SNIPE": {"pos": "verb", "meaning": "to shoot at targets from hiding; to make snide criticism", "example": "Critics sniped from the sidelines without offering solutions."},
    "SNOOP": {"pos": "verb", "meaning": "to investigate or look around secretly; a person who snoops", "example": "She caught him snooping through her messages."},
    "SNORE": {"pos": "verb", "meaning": "to breathe with a hoarse snorting sound while asleep", "example": "His snoring kept the whole dormitory awake."},
    "SNORT": {"pos": "verb", "meaning": "to force air through the nose noisily; to laugh derisively", "example": "She snorted with laughter at the absurdity of it."},
    "SNOUT": {"pos": "noun", "meaning": "the projecting nose and mouth of an animal; a person's nose (informal)", "example": "The pig's snout rooted through the mud."},
    "SNOWY": {"pos": "adjective", "meaning": "covered in snow; as white as snow", "example": "A snowy owl watched from the branch above."},
    "SNUFF": {"pos": "verb", "meaning": "to extinguish a candle; to inhale powdered tobacco through the nose", "example": "She snuffed out the candle and went to bed."},
    "SOBER": {"pos": "adjective", "meaning": "not affected by alcohol; serious and thoughtful; muted in color", "example": "He gave a sober assessment of the situation."},
    "SOGGY": {"pos": "adjective", "meaning": "very wet and soft; heavy with moisture", "example": "The picnic ended in soggy sandwiches after the rain."},
    "SOLAR": {"pos": "adjective", "meaning": "relating to or determined by the sun", "example": "The house was fitted with solar panels on the roof."},
    "SOLID": {"pos": "adjective", "meaning": "firm and stable; not hollow; dependable", "example": "She had a solid reputation built over decades."},
    "SOLVE": {"pos": "verb", "meaning": "to find the answer to a problem or mystery", "example": "It took three days to solve the puzzle."},
    "SONAR": {"pos": "noun", "meaning": "a system using sound waves to detect underwater objects", "example": "The submarine used sonar to navigate."},
    "SONIC": {"pos": "adjective", "meaning": "relating to or using sound waves", "example": "Sonic booms rattled windows miles away."},
    "SORRY": {"pos": "adjective", "meaning": "feeling regret; expressing apology; in a poor state", "example": "She said she was sorry and meant it."},
    "SOUND": {"pos": "noun", "meaning": "vibrations that travel through air and can be heard; in good condition", "example": "The argument was sound in every particular."},
    "SOUTH": {"pos": "noun", "meaning": "the direction toward the South Pole; the southern part of a place", "example": "They drove south toward the coast."},
    "SPACE": {"pos": "noun", "meaning": "a continuous area; the universe beyond Earth's atmosphere; an interval", "example": "She needed space to think things through."},
    "SPADE": {"pos": "noun", "meaning": "a digging tool with a flat blade; a playing card suit", "example": "He dug the vegetable bed with a long-handled spade."},
    "SPANK": {"pos": "verb", "meaning": "to slap on the buttocks as punishment; to move briskly", "example": "The yacht spanked along at ten knots."},
    "SPARE": {"pos": "adjective", "meaning": "available for use; thin; not being used; to refrain from harming", "example": "Spare a thought for those less fortunate."},
    "SPARK": {"pos": "noun", "meaning": "a small fiery particle; a trace of a quality; to trigger something", "example": "One spark ignited the whole controversy."},
    "SPAWN": {"pos": "verb", "meaning": "to produce eggs; to generate in large numbers; to originate", "example": "The success spawned dozens of imitations."},
    "SPEAK": {"pos": "verb", "meaning": "to say words aloud; to communicate; to give a speech", "example": "She spoke calmly and clearly throughout the debate."},
    "SPEAR": {"pos": "noun", "meaning": "a long pointed weapon; to pierce with a pointed implement", "example": "She speared a piece of broccoli with her fork."},
    "SPEED": {"pos": "noun", "meaning": "rapidity of movement; rate of motion; to move quickly", "example": "The train gathered speed as it left the station."},
    "SPELL": {"pos": "verb", "meaning": "to name the letters of a word; a period of time; a magical formula", "example": "Could you spell that for me?"},
    "SPEND": {"pos": "verb", "meaning": "to pay out money; to use time in a particular way; to exhaust", "example": "She spent the afternoon reading in the garden."},
    "SPERM": {"pos": "noun", "meaning": "the male reproductive cell; semen", "example": "Fertilization occurs when a sperm reaches an egg."},
    "SPICE": {"pos": "noun", "meaning": "a pungent vegetable substance used to flavor food; variety and excitement", "example": "Variety is the spice of life."},
    "SPICY": {"pos": "adjective", "meaning": "flavored with spices; mildly scandalous or risqué", "example": "The curry was deliciously spicy."},
    "SPIEL": {"pos": "noun", "meaning": "a lengthy speech intended to persuade; a sales pitch", "example": "He gave the usual spiel about special offers."},
    "SPIKE": {"pos": "noun", "meaning": "a sharp pointed piece; to add alcohol to a drink; to sabotage", "example": "She spiked the punch with vodka."},
    "SPILL": {"pos": "verb", "meaning": "to flow over the edge of a container; to reveal information", "example": "She spilled coffee down her shirt."},
    "SPINE": {"pos": "noun", "meaning": "the backbone; a sharp pointed projection; the back of a book", "example": "The spine of the novel bore a striking design."},
    "SPITE": {"pos": "noun", "meaning": "a desire to hurt or annoy someone; in spite of means despite", "example": "She smiled in spite of herself."},
    "SPLIT": {"pos": "verb", "meaning": "to divide or break; to share; a division; the gymnastic feat", "example": "They agreed to split the cost evenly."},
    "SPOIL": {"pos": "verb", "meaning": "to damage or impair; to harm character by excessive indulgence", "example": "Don't spoil the surprise by telling her."},
    "SPOOF": {"pos": "noun", "meaning": "a humorous imitation or parody; a gentle hoax", "example": "The show was a loving spoof of the detective genre."},
    "SPOOK": {"pos": "noun", "meaning": "a ghost; a spy; to frighten suddenly", "example": "The sudden noise spooked the horses."},
    "SPOOL": {"pos": "noun", "meaning": "a cylinder around which thread, film, or wire is wound", "example": "She threaded a new spool of cotton into the machine."},
    "SPOON": {"pos": "noun", "meaning": "a utensil with a bowl-shaped end for eating or serving liquid foods", "example": "She stirred the soup with a wooden spoon."},
    "SPORE": {"pos": "noun", "meaning": "a reproductive unit produced by fungi, bacteria, and plants", "example": "Ferns reproduce by releasing spores."},
    "SPORT": {"pos": "noun", "meaning": "a physical activity with rules; to wear or display something", "example": "She sported a new haircut at the reunion."},
    "SPOUT": {"pos": "verb", "meaning": "to shoot liquid forcefully; to speak at length and tediously", "example": "He spouted statistics for twenty minutes."},
    "SPRAY": {"pos": "noun", "meaning": "liquid forced out in tiny drops; a bunch of cut flowers", "example": "She carried a spray of white roses."},
    "SPREE": {"pos": "noun", "meaning": "a spell of unrestrained activity", "example": "She went on a shopping spree to cheer herself up."},
    "SPUNK": {"pos": "noun", "meaning": "courage and determination; spirit (informal)", "example": "The young player had real spunk."},
    "SPURN": {"pos": "verb", "meaning": "to reject with contempt; to kick away", "example": "She spurned every advance he made."},
    "SPURT": {"pos": "verb", "meaning": "to gush out in a sudden stream; a sudden increase in speed or activity", "example": "He put in a spurt on the final lap."},
    "SQUAD": {"pos": "noun", "meaning": "a small group of people with a common purpose; a police unit", "example": "The squad trained together every morning."},
    "SQUAT": {"pos": "verb", "meaning": "to crouch with knees bent; to occupy without legal right; short and wide", "example": "A squat stone tower stood at the harbour entrance."},
    "SQUID": {"pos": "noun", "meaning": "a cephalopod with eight arms and two tentacles", "example": "Grilled squid was on the menu at the seafood restaurant."},
    "STACK": {"pos": "noun", "meaning": "a pile or heap; a large amount; a chimney", "example": "There was a stack of unopened letters on the desk."},
    "STAFF": {"pos": "noun", "meaning": "the employees of an organization; a stick used as a weapon or support", "example": "The staff were given the day off to celebrate."},
    "STAGE": {"pos": "noun", "meaning": "a platform for performance; a point in a process; to organize an event", "example": "She had been on the stage for forty years."},
    "STAID": {"pos": "adjective", "meaning": "respectable and dull; sedate; unadventurous", "example": "The staid committee resisted all new ideas."},
    "STAIN": {"pos": "noun", "meaning": "a mark left by a substance; a blemish on a reputation; to mark", "example": "The red wine left a permanent stain on the tablecloth."},
    "STAIR": {"pos": "noun", "meaning": "a step or set of steps for going between floors", "example": "She climbed the narrow stair to the attic."},
    "STAKE": {"pos": "noun", "meaning": "a pointed post; an interest or involvement; a gambling bet", "example": "The stakes were too high to risk another mistake."},
    "STALE": {"pos": "adjective", "meaning": "no longer fresh; no longer new or interesting", "example": "The bread went stale overnight."},
    "STALK": {"pos": "verb", "meaning": "to pursue stealthily; to walk with a proud gait; the stem of a plant", "example": "She stalked out of the room in fury."},
    "STALL": {"pos": "verb", "meaning": "to stop making progress; to delay; a compartment for one animal", "example": "Negotiations stalled over the question of pay."},
    "STAMP": {"pos": "verb", "meaning": "to bring the foot down heavily; a small adhesive label; to impress a mark", "example": "She stamped her feet to keep warm."},
    "STAND": {"pos": "verb", "meaning": "to be upright; to tolerate; to maintain a position; a structure for support", "example": "She couldn't stand the noise any longer."},
    "STARE": {"pos": "verb", "meaning": "to look fixedly at something for a long time", "example": "She stared at the blank page hoping for inspiration."},
    "STARK": {"pos": "adjective", "meaning": "bare and bleak; sharply clear; complete (as in stark naked)", "example": "The choice was stark: stay or leave."},
    "START": {"pos": "verb", "meaning": "to begin; to cause to begin; a sudden involuntary movement", "example": "She started her new job on a Monday."},
    "STASH": {"pos": "verb", "meaning": "to store safely and secretly; a secret store", "example": "He had a stash of chocolates hidden in his desk."},
    "STATE": {"pos": "noun", "meaning": "the condition of something; a politically organized community; to say formally", "example": "Please state your name and address for the record."},
    "STAVE": {"pos": "noun", "meaning": "a wooden stick or staff; a verse of a poem; to ward off", "example": "Hot soup staved off the cold."},
    "STEAK": {"pos": "noun", "meaning": "a thick slice of meat or fish", "example": "She ordered a medium-rare steak with fries."},
    "STEAL": {"pos": "verb", "meaning": "to take without permission; to move quietly; a bargain", "example": "At that price, it's an absolute steal."},
    "STEAM": {"pos": "noun", "meaning": "water vapor; energy or momentum; to cook using steam vapor", "example": "She was still letting off steam about the meeting."},
    "STEEL": {"pos": "noun", "meaning": "a hard strong alloy of iron and carbon; to mentally prepare oneself", "example": "She steeled herself for the difficult conversation."},
    "STEEP": {"pos": "adjective", "meaning": "rising sharply; extreme in amount; to soak in liquid", "example": "The path was steep and slippery after the rain."},
    "STEER": {"pos": "verb", "meaning": "to guide a vehicle; to guide someone in a direction; a young bull", "example": "She steered the conversation away from politics."},
    "STERN": {"pos": "adjective", "meaning": "serious and demanding; not lenient; the rear of a ship", "example": "The head teacher had a stern manner but was fair."},
    "STICK": {"pos": "noun", "meaning": "a thin piece of wood; a rod; to attach; to remain", "example": "The mud stuck to everything."},
    "STIFF": {"pos": "adjective", "meaning": "not flexible; formal and reserved; strong (as in a stiff drink)", "example": "She poured herself a stiff whisky after the ordeal."},
    "STILL": {"pos": "adjective", "meaning": "not moving; quiet; continuing up to the present; a distillation device", "example": "He stood completely still and listened."},
    "STING": {"pos": "verb", "meaning": "to prick painfully; to feel a sharp pain; a confidence trick", "example": "She was stung into action by the criticism."},
    "STINK": {"pos": "verb", "meaning": "to emit a strong unpleasant smell; to be very bad (informal)", "example": "The whole situation stinks of corruption."},
    "STOIC": {"pos": "adjective", "meaning": "enduring pain or difficulty without complaint; calm under pressure", "example": "She was stoic in the face of enormous adversity."},
    "STONE": {"pos": "noun", "meaning": "a hard mineral material; a gem; a unit of weight of 14 pounds", "example": "She weighed nine stone before she started training."},
    "STOOD": {"pos": "verb", "meaning": "past tense of stand; was upright; remained in a position", "example": "He stood firm even when others wavered."},
    "STOOL": {"pos": "noun", "meaning": "a seat without a back or arms; to inform on someone (informal)", "example": "She perched on a bar stool and ordered a coffee."},
    "STOOP": {"pos": "verb", "meaning": "to bend the body forward; to lower one's moral standards; a forward stoop in posture", "example": "She refused to stoop to threats."},
    "STORE": {"pos": "noun", "meaning": "a place where things are kept; a shop; to keep for future use", "example": "A wonderful surprise was in store for her."},
    "STORK": {"pos": "noun", "meaning": "a large wading bird with a long bill and red legs", "example": "According to tradition, storks bring babies."},
    "STORM": {"pos": "noun", "meaning": "a violent weather event; a strong emotional reaction; to move angrily", "example": "She stormed out of the meeting without a word."},
    "STORY": {"pos": "noun", "meaning": "a narrative account; a news report; a floor of a building", "example": "She had a story to tell that nobody was ready for."},
    "STOUT": {"pos": "adjective", "meaning": "strongly built; brave; a dark beer", "example": "He ordered a pint of stout at the bar."},
    "STOVE": {"pos": "noun", "meaning": "an apparatus for cooking or heating using gas or electricity", "example": "She left a pot simmering on the stove."},
    "STRAP": {"pos": "noun", "meaning": "a strip of material used for fastening; to fasten with a strap", "example": "She tightened the strap on her backpack."},
    "STRAW": {"pos": "noun", "meaning": "dried grain stalks; a hollow tube for drinking; the final straw", "example": "That was the last straw—she finally complained."},
    "STRAY": {"pos": "verb", "meaning": "to move away from where one should be; to deviate", "example": "Her thoughts kept straying during the lecture."},
    "STRIP": {"pos": "verb", "meaning": "to remove covering; to undress; to deprive of; a narrow piece", "example": "They stripped the old paint from the floorboards."},
    "STRUT": {"pos": "verb", "meaning": "to walk with a proud or arrogant bearing; a supporting rod", "example": "He strutted into the room like he owned it."},
    "STUDY": {"pos": "verb", "meaning": "to devote time to learning; a room for reading; an academic work", "example": "She studied medicine for seven years."},
    "STUFF": {"pos": "noun", "meaning": "things or material of an unspecified kind; to fill tightly", "example": "She was made of tougher stuff than they realized."},
    "STUMP": {"pos": "noun", "meaning": "the base of a cut tree; to bewilder; a platform for making speeches", "example": "The question completely stumped the expert."},
    "STUNT": {"pos": "noun", "meaning": "an action to attract attention; a dangerous act; to hinder growth", "example": "The daring stunt was captured on film."},
    "STYLE": {"pos": "noun", "meaning": "a manner of doing things; a distinctive fashion; to design or arrange", "example": "She had her own distinctive style."},
    "SUAVE": {"pos": "adjective", "meaning": "charming, confident, and elegant in manner", "example": "He was suave and charming with everyone he met."},
    "SUEDE": {"pos": "noun", "meaning": "leather with a velvety finish produced by rubbing; cloth resembling this", "example": "She wore ankle boots in soft grey suede."},
    "SUGAR": {"pos": "noun", "meaning": "a sweet crystalline substance obtained from plants; a term of endearment", "example": "She added a spoonful of sugar to her coffee."},
    "SUITE": {"pos": "noun", "meaning": "a set of rooms; a group of related computer programs; a musical composition", "example": "They checked into the honeymoon suite."},
    "SULKY": {"pos": "adjective", "meaning": "moody and resentful; given to sulking", "example": "He was sulky for days after not getting his way."},
    "SUNNY": {"pos": "adjective", "meaning": "bright with sunlight; cheerful and bright in temperament", "example": "She had a sunny personality that lifted every room."},
    "SUPER": {"pos": "adjective", "meaning": "excellent; wonderful; above the usual level (informal)", "example": "You've done a super job with this."},
    "SURGE": {"pos": "noun", "meaning": "a sudden powerful forward movement; a sudden increase", "example": "A surge of electricity blew the fuse."},
    "SURLY": {"pos": "adjective", "meaning": "bad-tempered and unfriendly; churlish", "example": "The surly receptionist barely looked up."},
    "SUSHI": {"pos": "noun", "meaning": "a Japanese dish of vinegared rice with raw fish or other toppings", "example": "They went out for sushi to celebrate."},
    "SWAMP": {"pos": "noun", "meaning": "a wet marshy area; to overwhelm with too much of something", "example": "She was swamped with emails after the announcement."},
    "SWARM": {"pos": "noun", "meaning": "a large group of insects; to move in large numbers", "example": "Tourists swarmed the square on a bank holiday."},
    "SWEAR": {"pos": "verb", "meaning": "to state solemnly; to use offensive language; to take an oath", "example": "She swore she had never seen the document before."},
    "SWEAT": {"pos": "noun", "meaning": "moisture produced by the body when hot or nervous; hard work", "example": "Success is ninety percent sweat and ten percent talent."},
    "SWEEP": {"pos": "verb", "meaning": "to clean with a broom; to move swiftly; a wide curving movement", "example": "She swept the kitchen floor and mopped it down."},
    "SWEET": {"pos": "adjective", "meaning": "having a pleasant sugary taste; kind and pleasant; a confection", "example": "He left a sweet note on her desk."},
    "SWELL": {"pos": "verb", "meaning": "to become larger; to feel pride; the undulation of the sea", "example": "Her pride swelled as they announced her name."},
    "SWIFT": {"pos": "adjective", "meaning": "moving quickly; happening quickly; a fast-flying bird", "example": "She sent a swift reply within minutes."},
    "SWINE": {"pos": "noun", "meaning": "a pig; a contemptible person", "example": "He behaved like an absolute swine toward her."},
    "SWING": {"pos": "verb", "meaning": "to move back and forth; to change mood or opinion suddenly", "example": "Public opinion swung decisively during the campaign."},
    "SWIRL": {"pos": "verb", "meaning": "to move in a twisting or spiraling pattern", "example": "Autumn leaves swirled in the wind."},
    "SWOON": {"pos": "verb", "meaning": "to faint from emotion; to be overwhelmed with admiration", "example": "Audiences swooned at his romantic performances."},
    "SWOOP": {"pos": "verb", "meaning": "to move rapidly downward; to carry out a sudden attack", "example": "Police swooped on the premises at dawn."},
    "SWORD": {"pos": "noun", "meaning": "a weapon with a long metal blade and a handle", "example": "Knights trained with the sword from childhood."},
    "SYNOD": {"pos": "noun", "meaning": "a council of a church; a formal meeting of church officials", "example": "The synod debated the new guidelines for days."},
    "SYNTH": {"pos": "noun", "meaning": "a synthesizer; an electronic musical instrument (informal)", "example": "The producer layered synth sounds over the drum beat."},
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def ensure_table(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS word_definitions (
            word     TEXT PRIMARY KEY,
            pos      TEXT NOT NULL DEFAULT '',
            meaning  TEXT NOT NULL DEFAULT '',
            example  TEXT NOT NULL DEFAULT ''
        )
    """)


async def load_words(path: pathlib.Path) -> list[str]:
    words = []
    with path.open() as f:
        for line in f:
            w = line.strip().upper()
            if len(w) == 5 and w.isalpha():
                words.append(w)
    return words


async def main(overwrite: bool, csv_out: bool) -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("ERROR: DATABASE_URL environment variable is not set.")

    words = await load_words(_WORDS_FILE)
    print(f"Word list: {len(words)} words")

    to_insert = {w: DEFINITIONS[w] for w in words if w in DEFINITIONS}
    print(f"Definitions available: {len(to_insert)}")

    if csv_out:
        csv_path = _WORDS_FILE.parent / "definitions_ps.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["word", "pos", "meaning", "example"])
            writer.writeheader()
            for word in sorted(to_insert):
                writer.writerow({"word": word, **to_insert[word]})
        print(f"CSV written → {csv_path}")

    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=3)
    async with pool.acquire() as conn:
        await ensure_table(conn)

    if overwrite:
        sql = """
            INSERT INTO word_definitions (word, pos, meaning, example)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (word) DO UPDATE SET
                pos=EXCLUDED.pos, meaning=EXCLUDED.meaning, example=EXCLUDED.example
        """
    else:
        sql = """
            INSERT INTO word_definitions (word, pos, meaning, example)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (word) DO NOTHING
        """

    inserted = skipped = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for word, defn in to_insert.items():
                result = await conn.execute(
                    sql, word, defn["pos"], defn["meaning"], defn["example"]
                )
                if result.endswith("1"):
                    inserted += 1
                else:
                    skipped += 1

    await pool.close()
    print(f"\nDone.")
    print(f"  Inserted / updated : {inserted}")
    print(f"  Already existed    : {skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed word definitions for P–S words")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing definitions")
    parser.add_argument("--csv", action="store_true", help="Also write a CSV backup file")
    args = parser.parse_args()
    asyncio.run(main(overwrite=args.overwrite, csv_out=args.csv))
