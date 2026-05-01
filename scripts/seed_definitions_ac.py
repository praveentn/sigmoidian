#!/usr/bin/env python3
"""
Seed word definitions for A–C words using Claude-generated data.

Usage:
    python scripts/seed_definitions_ac.py                # insert missing only
    python scripts/seed_definitions_ac.py --overwrite    # replace existing
    python scripts/seed_definitions_ac.py --csv          # also dump CSV
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

# ---------------------------------------------------------------------------
# Claude-generated definitions  (word → {pos, meaning, example})
# ---------------------------------------------------------------------------
DEFINITIONS: dict[str, dict] = {

    # ── A ──────────────────────────────────────────────────────────────────

    "AARGH": {"pos": "interjection", "meaning": "expressing frustration, exasperation, or despair", "example": "Aargh, I spilled coffee on my keyboard again!"},
    "ABASH": {"pos": "verb", "meaning": "to make someone feel embarrassed, disconcerted, or ashamed", "example": "She was abashed by the sudden burst of applause."},
    "ABATE": {"pos": "verb", "meaning": "to reduce in intensity, amount, or strength; to subside", "example": "The storm began to abate as the evening wore on."},
    "ABBEY": {"pos": "noun", "meaning": "a monastery or convent governed by an abbot or abbess", "example": "They visited a medieval abbey perched on a cliff above the sea."},
    "ABBOT": {"pos": "noun", "meaning": "the head of a monastery or abbey", "example": "The abbot greeted the pilgrims at the gate."},
    "ABHOR": {"pos": "verb", "meaning": "to regard with disgust and hatred; to detest strongly", "example": "She abhorred cruelty in any form."},
    "ABIDE": {"pos": "verb", "meaning": "to tolerate or accept; to remain; to follow a rule", "example": "He could not abide dishonesty."},
    "ABODE": {"pos": "noun", "meaning": "the place where someone lives; a home or dwelling", "example": "Their small cottage was a humble but comfortable abode."},
    "ABORT": {"pos": "verb", "meaning": "to stop before completion; to terminate a process or mission", "example": "Mission control ordered them to abort the launch."},
    "ABOUT": {"pos": "preposition", "meaning": "on the subject of; concerning; approximately", "example": "She wrote a book about her travels in Southeast Asia."},
    "ABOVE": {"pos": "preposition", "meaning": "at a higher level or layer than; more than", "example": "The temperature rose above thirty degrees."},
    "ABUSE": {"pos": "noun", "meaning": "cruel or violent treatment; improper use of something", "example": "The report documented widespread abuse of power."},
    "ABYSS": {"pos": "noun", "meaning": "a deep or seemingly bottomless chasm; an immeasurable depth", "example": "They peered over the edge into the dark abyss below."},
    "ACORN": {"pos": "noun", "meaning": "the nut of an oak tree, set in a cup-shaped base", "example": "The squirrel buried an acorn for the winter."},
    "ACRID": {"pos": "adjective", "meaning": "having an unpleasantly strong and bitter smell or taste", "example": "Acrid smoke poured from the burning tires."},
    "ACTOR": {"pos": "noun", "meaning": "a person who performs roles in plays, films, or television", "example": "The actor delivered his lines with quiet intensity."},
    "ACUTE": {"pos": "adjective", "meaning": "sharp, intense, or severe; showing keen perceptiveness", "example": "She had an acute sense of hearing."},
    "ADAGE": {"pos": "noun", "meaning": "a short traditional saying that expresses a widely held truth", "example": "'Look before you leap' is an old adage worth remembering."},
    "ADAPT": {"pos": "verb", "meaning": "to become adjusted to new conditions; to modify for a new purpose", "example": "Animals must adapt to survive changing environments."},
    "ADDER": {"pos": "noun", "meaning": "a venomous snake; the common European viper", "example": "An adder basked on the sun-warmed rocks."},
    "ADDLE": {"pos": "verb", "meaning": "to confuse or muddle; to cause an egg to become rotten", "example": "Too many questions began to addle his brain."},
    "ADEPT": {"pos": "adjective", "meaning": "very skilled or proficient at something", "example": "She was adept at solving complex puzzles."},
    "ADIEU": {"pos": "interjection", "meaning": "goodbye; a farewell (from French)", "example": "He bade her adieu at the station platform."},
    "ADMIN": {"pos": "noun", "meaning": "administration; the work of managing an organization", "example": "He spent the morning catching up on admin."},
    "ADMIT": {"pos": "verb", "meaning": "to confess; to allow someone to enter a place", "example": "She finally admitted she had forgotten."},
    "ADOBE": {"pos": "noun", "meaning": "a brick made from sun-dried clay; material used in building", "example": "The desert village was built entirely of adobe."},
    "ADOPT": {"pos": "verb", "meaning": "to legally take another's child as one's own; to take up an idea or practice", "example": "They decided to adopt a child from overseas."},
    "ADORE": {"pos": "verb", "meaning": "to love and respect deeply; to be very fond of", "example": "The children adored their grandmother."},
    "ADORN": {"pos": "verb", "meaning": "to make more beautiful with decorations; to ornament", "example": "Flowers adorned every table in the hall."},
    "ADULT": {"pos": "noun", "meaning": "a fully grown person; someone legally of age", "example": "The film was rated for adults only."},
    "AEGIS": {"pos": "noun", "meaning": "protection or support from a powerful person or organization", "example": "The project was carried out under the aegis of the university."},
    "AERIE": {"pos": "noun", "meaning": "the large nest of an eagle or other bird of prey on a high cliff", "example": "The golden eagle returned to its aerie at dusk."},
    "AFFIX": {"pos": "verb", "meaning": "to attach or fasten; to add a stamp, signature, or label", "example": "Please affix your signature to the bottom of the form."},
    "AFTER": {"pos": "preposition", "meaning": "following in time, order, or position", "example": "We went for a walk after dinner."},
    "AGAIN": {"pos": "adverb", "meaning": "once more; another time; returning to a previous state", "example": "Can you say that again? I didn't hear you."},
    "AGAPE": {"pos": "adjective", "meaning": "wide open, especially in surprise; also, selfless Christian love", "example": "Her mouth was agape as she stared at the view."},
    "AGATE": {"pos": "noun", "meaning": "a hard semiprecious stone with streaks of color; used in jewelry", "example": "The ring was set with a polished agate."},
    "AGAVE": {"pos": "noun", "meaning": "a spiky desert plant native to Mexico; used to make tequila", "example": "Tequila is distilled from the blue agave plant."},
    "AGENT": {"pos": "noun", "meaning": "a person who acts on behalf of another; a spy", "example": "Her literary agent negotiated the book deal."},
    "AGGRO": {"pos": "noun", "meaning": "aggressive or violent behavior; trouble (British informal)", "example": "He just wanted a quiet evening without any aggro."},
    "AGILE": {"pos": "adjective", "meaning": "able to move quickly and easily; mentally sharp and adaptable", "example": "She was agile enough to climb the rope in seconds."},
    "AGONY": {"pos": "noun", "meaning": "extreme physical or mental suffering; intense pain or distress", "example": "The long wait was sheer agony."},
    "AGORA": {"pos": "noun", "meaning": "a public open space used for assemblies in ancient Greek cities", "example": "Citizens gathered in the agora to debate the new law."},
    "AGREE": {"pos": "verb", "meaning": "to share the same opinion; to consent to something", "example": "We all agreed to meet at noon."},
    "AHEAD": {"pos": "adverb", "meaning": "further forward in space or time; in advance", "example": "The road ahead was clear."},
    "AIOLI": {"pos": "noun", "meaning": "a garlic mayonnaise from Provence, used as a sauce or dip", "example": "She dipped her fries in a bowl of homemade aioli."},
    "AISLE": {"pos": "noun", "meaning": "a passage between rows of seats or shelves", "example": "The bride walked slowly down the aisle."},
    "ALARM": {"pos": "noun", "meaning": "a warning signal; sudden fear or anxiety", "example": "The fire alarm woke everyone in the building."},
    "ALBUM": {"pos": "noun", "meaning": "a collection of recorded music; a book for photographs or stamps", "example": "The band released their debut album last spring."},
    "ALDER": {"pos": "noun", "meaning": "a tree related to birch that typically grows near water", "example": "Alders lined the bank of the river."},
    "ALERT": {"pos": "adjective", "meaning": "watchful and ready to respond; quick to perceive danger", "example": "The guard remained alert throughout his shift."},
    "ALGAE": {"pos": "noun", "meaning": "simple aquatic organisms that photosynthesize; plants without roots", "example": "Algae coated the surface of the pond."},
    "ALIAS": {"pos": "noun", "meaning": "a false or assumed name used to conceal one's identity", "example": "The spy operated under the alias 'Mr. Grey'."},
    "ALIBI": {"pos": "noun", "meaning": "evidence that one was elsewhere when a crime took place", "example": "His alibi checked out—he was at the cinema."},
    "ALIEN": {"pos": "noun", "meaning": "a foreigner; a being from another world; something unfamiliar", "example": "The concept felt completely alien to her."},
    "ALIGN": {"pos": "verb", "meaning": "to place in a straight line; to associate with a group or cause", "example": "She aligned herself with the reform movement."},
    "ALIKE": {"pos": "adjective", "meaning": "similar in appearance or nature; in the same way", "example": "The twins dressed alike for the occasion."},
    "ALIVE": {"pos": "adjective", "meaning": "living; full of life and energy; active", "example": "She felt completely alive hiking through the mountains."},
    "ALLAY": {"pos": "verb", "meaning": "to reduce or relieve fear, worry, or pain; to calm", "example": "The doctor's words allayed her fears."},
    "ALLEY": {"pos": "noun", "meaning": "a narrow street or passageway; a lane used for bowling", "example": "A cat was prowling in the alley behind the restaurant."},
    "ALLOT": {"pos": "verb", "meaning": "to assign a share or portion of something to someone", "example": "Each team was allotted twenty minutes to present."},
    "ALLOW": {"pos": "verb", "meaning": "to give permission for; to make possible; to permit", "example": "Smoking is not allowed inside the building."},
    "ALLOY": {"pos": "noun", "meaning": "a metal made by combining two or more metallic elements", "example": "Bronze is an alloy of copper and tin."},
    "ALOFT": {"pos": "adverb", "meaning": "up in the air; high above the ground", "example": "The balloon drifted aloft on the morning breeze."},
    "ALOHA": {"pos": "interjection", "meaning": "a Hawaiian word used as a greeting or farewell; hello or goodbye", "example": "She greeted the guests with a warm aloha."},
    "ALONE": {"pos": "adjective", "meaning": "by oneself without others; without help; only", "example": "She preferred to work alone."},
    "ALONG": {"pos": "preposition", "meaning": "moving in a line corresponding to the length of; in company with", "example": "They walked along the river path."},
    "ALOOF": {"pos": "adjective", "meaning": "not friendly or forthcoming; distant and reserved", "example": "He seemed aloof at first, but warmed up later."},
    "ALOUD": {"pos": "adverb", "meaning": "audibly; in a voice loud enough to be heard", "example": "She read the poem aloud to the class."},
    "ALPHA": {"pos": "noun", "meaning": "the first letter of the Greek alphabet; the dominant individual", "example": "He was the alpha of the group, always leading."},
    "ALTAR": {"pos": "noun", "meaning": "a table or flat-topped surface used as a focus for religious rituals", "example": "Candles burned on the stone altar."},
    "ALTER": {"pos": "verb", "meaning": "to change or make different; to modify", "example": "She altered the recipe slightly to suit her taste."},
    "AMASS": {"pos": "verb", "meaning": "to gather together or accumulate a large amount of something", "example": "He amassed a fortune over decades of hard work."},
    "AMAZE": {"pos": "verb", "meaning": "to fill with wonder and surprise; to astonish greatly", "example": "The acrobat's skill amazed the audience."},
    "AMBER": {"pos": "noun", "meaning": "a yellow-brown fossilized tree resin used in jewelry; that color", "example": "Ancient insects were preserved in amber for millions of years."},
    "AMBIT": {"pos": "noun", "meaning": "the scope, extent, or bounds of something", "example": "This matter falls within the ambit of the court."},
    "AMBLE": {"pos": "verb", "meaning": "to walk at a slow, relaxed pace; to stroll", "example": "They ambled through the market without any hurry."},
    "AMEND": {"pos": "verb", "meaning": "to make minor changes to improve or correct a text or law", "example": "Parliament voted to amend the constitution."},
    "AMIGO": {"pos": "noun", "meaning": "a friend (from Spanish); used informally in English", "example": "He greeted the barman with 'Hey amigo!'"},
    "AMISS": {"pos": "adjective", "meaning": "not quite right; inappropriate in the circumstances", "example": "Something felt amiss as soon as she entered the room."},
    "AMITY": {"pos": "noun", "meaning": "a friendly and peaceful relationship; goodwill between people", "example": "The treaty was signed in a spirit of amity."},
    "AMONG": {"pos": "preposition", "meaning": "in the middle of; surrounded by; in the group of", "example": "She sat among friends."},
    "AMPLE": {"pos": "adjective", "meaning": "enough or more than enough; large and spacious", "example": "There was ample time to catch the train."},
    "AMUSE": {"pos": "verb", "meaning": "to entertain; to cause to find something funny", "example": "The comedian's routine amused the whole crowd."},
    "ANGEL": {"pos": "noun", "meaning": "a spiritual being seen as a messenger of God; a kind and helpful person", "example": "She was an angel, always there when people needed help."},
    "ANGER": {"pos": "noun", "meaning": "a strong feeling of displeasure or hostility", "example": "His anger was clear from the tone of his voice."},
    "ANGLE": {"pos": "noun", "meaning": "the space between two intersecting lines; a particular viewpoint", "example": "The photographer chose an unusual angle for the shot."},
    "ANGRY": {"pos": "adjective", "meaning": "feeling or showing strong displeasure or hostility", "example": "She was angry at being kept waiting so long."},
    "ANGST": {"pos": "noun", "meaning": "deep anxiety or dread about one's life or circumstances", "example": "Teenage angst is a common theme in coming-of-age novels."},
    "ANIME": {"pos": "noun", "meaning": "Japanese animated film and television, known for distinctive visual style", "example": "She was passionate about anime and manga."},
    "ANION": {"pos": "noun", "meaning": "a negatively charged ion that is attracted to an anode", "example": "Chloride is a common anion in seawater."},
    "ANISE": {"pos": "noun", "meaning": "a plant with licorice-flavored seeds used in cooking and liqueurs", "example": "The biscotti were flavored with anise."},
    "ANKLE": {"pos": "noun", "meaning": "the joint connecting the foot to the leg", "example": "She twisted her ankle running down the stairs."},
    "ANNEX": {"pos": "verb", "meaning": "to add territory to an existing area by force; to append", "example": "The empire sought to annex the neighboring kingdom."},
    "ANNOY": {"pos": "verb", "meaning": "to irritate or make slightly angry; to bother", "example": "The constant noise began to annoy her."},
    "ANNUL": {"pos": "verb", "meaning": "to declare legally void; to cancel or invalidate officially", "example": "The court moved to annul the fraudulent contract."},
    "ANODE": {"pos": "noun", "meaning": "the positively charged electrode in an electrical device", "example": "Electrons flow from the cathode to the anode."},
    "ANTIC": {"pos": "noun", "meaning": "a silly or playful act; a prank", "example": "The children's antics kept everyone laughing."},
    "ANTSY": {"pos": "adjective", "meaning": "agitated, impatient, or restless (informal)", "example": "She was getting antsy waiting for the results."},
    "ANVIL": {"pos": "noun", "meaning": "a heavy iron block on which hot metal is hammered into shape", "example": "The blacksmith brought his hammer down on the anvil."},
    "AORTA": {"pos": "noun", "meaning": "the main artery of the body, carrying blood from the heart", "example": "A blockage in the aorta can be life-threatening."},
    "APACE": {"pos": "adverb", "meaning": "swiftly; at a fast pace", "example": "Development in the city proceeded apace."},
    "APART": {"pos": "adverb", "meaning": "separated by distance; to one side; into pieces", "example": "The two cities are only an hour apart."},
    "APHID": {"pos": "noun", "meaning": "a tiny insect that feeds on plant sap; a garden pest", "example": "Aphids were attacking the rose bushes."},
    "APNEA": {"pos": "noun", "meaning": "temporary cessation of breathing, especially during sleep", "example": "He was diagnosed with sleep apnea after a study."},
    "APPLE": {"pos": "noun", "meaning": "a round fruit with crisp flesh and a red, yellow, or green skin", "example": "She picked a ripe apple from the tree."},
    "APRON": {"pos": "noun", "meaning": "a protective garment worn over the front of clothes when cooking", "example": "He tied on his apron before starting to cook."},
    "APTLY": {"pos": "adverb", "meaning": "in a way that is suitable or appropriate", "example": "The restaurant was aptly named 'The Rustic Kitchen'."},
    "ARBOR": {"pos": "noun", "meaning": "a garden structure covered by climbing plants; a shaded bower", "example": "Roses climbed over the wooden arbor at the garden entrance."},
    "ARDOR": {"pos": "noun", "meaning": "enthusiasm and passion; great eagerness or zeal", "example": "She pursued her research with unwavering ardor."},
    "ARENA": {"pos": "noun", "meaning": "a large venue for sports or entertainment; a field of activity", "example": "The team entered the arena to thunderous applause."},
    "ARGON": {"pos": "noun", "meaning": "a colorless inert gas that makes up about 1% of the atmosphere", "example": "Argon is used in welding to prevent oxidation."},
    "ARGOT": {"pos": "noun", "meaning": "the specialized slang or jargon of a particular group", "example": "Criminals developed an argot to confuse outsiders."},
    "ARGUE": {"pos": "verb", "meaning": "to give reasons for or against; to quarrel or debate", "example": "They argued for hours about the best approach."},
    "ARISE": {"pos": "verb", "meaning": "to emerge or originate; to get up; to come into existence", "example": "A problem arose with the new software."},
    "ARMOR": {"pos": "noun", "meaning": "protective metal covering worn in battle; any protective covering", "example": "Knights wore armor made of steel plates."},
    "AROMA": {"pos": "noun", "meaning": "a pleasant and distinctive smell; a fragrance", "example": "The aroma of fresh coffee filled the café."},
    "ARRAY": {"pos": "noun", "meaning": "an impressive display or range; an ordered arrangement", "example": "The shop offered an array of handmade goods."},
    "ARROW": {"pos": "noun", "meaning": "a pointed shaft shot from a bow; a symbol indicating direction", "example": "The archer drew back the arrow and released."},
    "ARSON": {"pos": "noun", "meaning": "the criminal act of deliberately setting fire to property", "example": "The investigator suspected arson from the pattern of the fire."},
    "ASCOT": {"pos": "noun", "meaning": "a broad neck cloth worn looped under the chin; a horse-racing event", "example": "He wore a silk ascot to the formal garden party."},
    "ASHEN": {"pos": "adjective", "meaning": "very pale, as if drained of color; ash-gray", "example": "She turned ashen when she heard the news."},
    "ASIDE": {"pos": "adverb", "meaning": "to one side; out of the way; in reserve", "example": "She set the matter aside for the moment."},
    "ASKEW": {"pos": "adjective", "meaning": "not in a straight or level position; crooked", "example": "The picture frame was hanging askew."},
    "ASPEN": {"pos": "noun", "meaning": "a type of poplar tree with leaves that tremble in the slightest breeze", "example": "Aspen leaves shimmered gold in the autumn light."},
    "ASPIC": {"pos": "noun", "meaning": "a savory jelly made from meat stock, used to set cold dishes", "example": "The terrine was served in a clear aspic."},
    "ASSAY": {"pos": "noun", "meaning": "an analysis to determine the content of a metal ore or drug", "example": "An assay confirmed the ore contained high-grade gold."},
    "ASSET": {"pos": "noun", "meaning": "something of value owned by a person or company", "example": "Her experience was her greatest asset."},
    "ASTER": {"pos": "noun", "meaning": "a plant with daisy-like flowers of various colors", "example": "Purple asters bloomed along the garden path."},
    "ASTIR": {"pos": "adjective", "meaning": "in a state of activity or excitement; up and about", "example": "The whole village was astir with the festival preparations."},
    "ATLAS": {"pos": "noun", "meaning": "a book of maps; in mythology, the Titan who held up the heavens", "example": "She flipped through the atlas planning their road trip."},
    "ATOLL": {"pos": "noun", "meaning": "a ring-shaped coral reef enclosing a lagoon", "example": "They anchored in the calm waters inside the atoll."},
    "ATONE": {"pos": "verb", "meaning": "to make amends for wrongdoing; to repair harm caused", "example": "He spent years trying to atone for his mistakes."},
    "ATTIC": {"pos": "noun", "meaning": "a space or room just below the roof of a building", "example": "Old photographs were stored in boxes in the attic."},
    "AUDIO": {"pos": "noun", "meaning": "sound, especially recorded or transmitted sound", "example": "The audio quality on the podcast was excellent."},
    "AUDIT": {"pos": "noun", "meaning": "an official examination of accounts or a process", "example": "The firm underwent a financial audit every year."},
    "AUGER": {"pos": "noun", "meaning": "a tool for boring holes in wood or the ground", "example": "He used an auger to drill post holes for the fence."},
    "AUGHT": {"pos": "noun", "meaning": "anything at all (archaic); zero", "example": "It mattered not one aught to him."},
    "AUGUR": {"pos": "verb", "meaning": "to be a sign of future events; to predict from omens", "example": "The clear skies augured well for the harvest."},
    "AURAL": {"pos": "adjective", "meaning": "relating to the ear or the sense of hearing", "example": "The concert was an aural feast of layered harmonies."},
    "AVAIL": {"pos": "verb", "meaning": "to be of use or benefit to; to take advantage of", "example": "All her efforts were to no avail."},
    "AVERT": {"pos": "verb", "meaning": "to prevent from happening; to turn away one's eyes", "example": "Quick thinking averted a serious accident."},
    "AVIAN": {"pos": "adjective", "meaning": "relating to birds", "example": "The avian flu outbreak caused widespread concern."},
    "AVOID": {"pos": "verb", "meaning": "to keep away from; to refrain from doing something", "example": "She tried to avoid making eye contact."},
    "AWAIT": {"pos": "verb", "meaning": "to wait for; to be in store for someone", "example": "A surprise awaited them at the end of the trail."},
    "AWAKE": {"pos": "adjective", "meaning": "not asleep; alert and aware", "example": "He lay awake for hours thinking."},
    "AWARD": {"pos": "noun", "meaning": "a prize or other recognition of merit", "example": "She won the award for best short story."},
    "AWARE": {"pos": "adjective", "meaning": "having knowledge or perception of a situation or fact", "example": "He was fully aware of the risks involved."},
    "AWFUL": {"pos": "adjective", "meaning": "very bad or unpleasant; extremely terrible", "example": "The weather was awful all week."},
    "AXIOM": {"pos": "noun", "meaning": "a statement regarded as self-evidently true; an accepted principle", "example": "It is an axiom that every human deserves dignity."},
    "AZURE": {"pos": "adjective", "meaning": "bright blue in color, like a clear sky", "example": "The azure sea stretched out beneath the cloudless sky."},

    # ── B ──────────────────────────────────────────────────────────────────

    "BABEL": {"pos": "noun", "meaning": "a confused mixture of sounds or voices; noisy confusion", "example": "A babel of languages filled the crowded marketplace."},
    "BABKA": {"pos": "noun", "meaning": "a sweet braided bread or cake made with yeast, popular in Eastern Europe", "example": "She brought a chocolate babka to the brunch."},
    "BACON": {"pos": "noun", "meaning": "cured and often smoked meat cut from the back or sides of a pig", "example": "The smell of frying bacon filled the kitchen."},
    "BADGE": {"pos": "noun", "meaning": "a small emblem worn to show rank, membership, or achievement", "example": "Officers wore their badges on their lapels."},
    "BAGEL": {"pos": "noun", "meaning": "a dense ring-shaped bread roll with a chewy texture", "example": "She had a toasted bagel with cream cheese for breakfast."},
    "BAGGY": {"pos": "adjective", "meaning": "loose-fitting and hanging in folds", "example": "He wore baggy trousers and an oversized shirt."},
    "BAIRN": {"pos": "noun", "meaning": "a child (Scottish and Northern English dialect)", "example": "The wee bairn was fast asleep in its cot."},
    "BAIZE": {"pos": "noun", "meaning": "a coarse woolen cloth used to cover billiard tables and card tables", "example": "The old snooker table had worn patches in its green baize."},
    "BAKER": {"pos": "noun", "meaning": "a person who makes and sells bread and cakes", "example": "The baker rose at four in the morning to prepare the day's loaves."},
    "BALMY": {"pos": "adjective", "meaning": "pleasantly warm; mild and gentle (of weather)", "example": "They strolled on the beach on a balmy evening."},
    "BALSA": {"pos": "noun", "meaning": "a lightweight wood from a tropical tree, used in model-making", "example": "The model plane was built from balsa wood."},
    "BANAL": {"pos": "adjective", "meaning": "so ordinary as to be uninteresting or predictable; trite", "example": "The film's dialogue was disappointingly banal."},
    "BANDY": {"pos": "verb", "meaning": "to exchange words in an argument; to spread rumors", "example": "His name was being bandied about as a candidate."},
    "BANJO": {"pos": "noun", "meaning": "a stringed musical instrument with a circular resonating body", "example": "He plucked a lively tune on his banjo."},
    "BARON": {"pos": "noun", "meaning": "a nobleman; a powerful figure in a field of business", "example": "A media baron controlled much of the press."},
    "BARGE": {"pos": "noun", "meaning": "a flat-bottomed boat used on rivers and canals", "example": "They hired a barge for a weekend trip along the canal."},
    "BARMY": {"pos": "adjective", "meaning": "mad or crazy (British informal)", "example": "That idea is absolutely barmy."},
    "BASIC": {"pos": "adjective", "meaning": "forming the foundation; fundamental; simple and minimal", "example": "She learned the basic principles of coding in a weekend."},
    "BASIL": {"pos": "noun", "meaning": "a fragrant herb with green leaves used extensively in cooking", "example": "She added fresh basil leaves to the tomato salad."},
    "BASIN": {"pos": "noun", "meaning": "a bowl-shaped vessel for holding water; a river drainage area", "example": "The Amazon basin is the world's largest river basin."},
    "BASIS": {"pos": "noun", "meaning": "the underlying foundation or principle; the reason for an action", "example": "The deal was agreed on the basis of mutual benefit."},
    "BASTE": {"pos": "verb", "meaning": "to pour fat or juices over meat during cooking; to sew loosely", "example": "She basted the turkey every thirty minutes."},
    "BATCH": {"pos": "noun", "meaning": "a quantity of goods produced at one time; a group", "example": "She baked a batch of cookies for the school fair."},
    "BATHE": {"pos": "verb", "meaning": "to wash one's body; to swim; to immerse in liquid", "example": "He bathed in the cool river to escape the heat."},
    "BATIK": {"pos": "noun", "meaning": "a method of fabric dyeing using wax resist; cloth so decorated", "example": "She wore a beautiful batik sarong."},
    "BATON": {"pos": "noun", "meaning": "a thin stick used to conduct an orchestra; a relay runner's stick", "example": "She passed the baton and their team took the lead."},
    "BATTY": {"pos": "adjective", "meaning": "mad or eccentric (informal)", "example": "He had some batty ideas, but people loved him anyway."},
    "BAWDY": {"pos": "adjective", "meaning": "dealing with sexual matters in a humorous and indirect way", "example": "The tavern rang with bawdy songs."},
    "BAYOU": {"pos": "noun", "meaning": "a slow-moving body of water in a swampy area of the southern USA", "example": "They paddled a canoe through the murky bayou."},
    "BEACH": {"pos": "noun", "meaning": "a pebbly or sandy shore at the edge of the sea or a lake", "example": "Children built sandcastles on the beach."},
    "BEADS": {"pos": "noun", "meaning": "small pieces of glass, stone, or wood strung to make jewelry", "example": "She wore a string of amber beads around her neck."},
    "BEARD": {"pos": "noun", "meaning": "hair growing on a man's chin and lower cheeks", "example": "He stroked his beard thoughtfully."},
    "BEAST": {"pos": "noun", "meaning": "a large or ferocious animal; a brutal or unkind person", "example": "A beast howled somewhere in the dark forest."},
    "BEBOP": {"pos": "noun", "meaning": "a type of jazz with complex harmonies and rhythms, developed in the 1940s", "example": "They played bebop at the late-night jazz club."},
    "BEECH": {"pos": "noun", "meaning": "a large tree with smooth gray bark and glossy oval leaves", "example": "Beech trees turned copper and gold in autumn."},
    "BEFIT": {"pos": "verb", "meaning": "to be appropriate or suitable for", "example": "She dressed in a manner that befitted the occasion."},
    "BEIGE": {"pos": "adjective", "meaning": "a pale sandy yellowish-brown color", "example": "The walls were painted a neutral beige."},
    "BEING": {"pos": "noun", "meaning": "existence; a living creature, especially a conscious one", "example": "She believed in the importance of human being over human doing."},
    "BELAY": {"pos": "verb", "meaning": "to secure a climbing rope; to stop or cancel an order (nautical)", "example": "She belayed the rope as her partner climbed higher."},
    "BELCH": {"pos": "verb", "meaning": "to expel gas noisily from the stomach through the mouth", "example": "The volcano belched smoke and ash."},
    "BELIE": {"pos": "verb", "meaning": "to give a false impression of; to contradict or conceal", "example": "Her calm face belied her inner anxiety."},
    "BELLE": {"pos": "noun", "meaning": "a beautiful and admired girl or woman", "example": "She was the belle of the ball that evening."},
    "BELLY": {"pos": "noun", "meaning": "the front of the human trunk below the ribs; the stomach", "example": "He laughed until his belly ached."},
    "BELOW": {"pos": "preposition", "meaning": "at a lower level or layer; less than a specified amount", "example": "Temperatures fell below freezing overnight."},
    "BENCH": {"pos": "noun", "meaning": "a long seat; a judge's seat in court; a worktable", "example": "They sat on the park bench and fed the ducks."},
    "BENTO": {"pos": "noun", "meaning": "a Japanese-style packed meal in a divided box", "example": "She prepared a beautiful bento box for her lunch."},
    "BERET": {"pos": "noun", "meaning": "a round flat cap with no brim, often associated with French fashion", "example": "She wore a red beret tilted to one side."},
    "BERRY": {"pos": "noun", "meaning": "a small round juicy fruit; a soft fruit without a stone", "example": "She picked wild berries from the hedgerow."},
    "BERTH": {"pos": "noun", "meaning": "a sleeping bunk on a ship or train; a mooring place for a vessel", "example": "He settled into his upper berth as the train departed."},
    "BESET": {"pos": "verb", "meaning": "to trouble or threaten persistently; to hem in from all sides", "example": "The expedition was beset by bad weather."},
    "BEVEL": {"pos": "noun", "meaning": "a sloping surface or edge; a tool for marking angles", "example": "The carpenter cut a 45-degree bevel on the wood."},
    "BIBLE": {"pos": "noun", "meaning": "the sacred text of Christianity; an authoritative book on a subject", "example": "The chef's bible sat dog-eared on the kitchen shelf."},
    "BIDET": {"pos": "noun", "meaning": "a low basin for washing one's lower body, found in bathrooms", "example": "The luxury hotel room included a bidet."},
    "BIGHT": {"pos": "noun", "meaning": "a curve in a coastline or river; a loop of rope", "example": "The bay formed a gentle bight protected from the wind."},
    "BIGOT": {"pos": "noun", "meaning": "a person intolerant of differing opinions, beliefs, or races", "example": "He was known as a bigot who refused to listen to others."},
    "BIJOU": {"pos": "adjective", "meaning": "small and elegant; attractively compact", "example": "They rented a bijou apartment in the old quarter."},
    "BIKED": {"pos": "verb", "meaning": "past tense of bike; traveled by bicycle", "example": "She biked to work every day through the park."},
    "BIKER": {"pos": "noun", "meaning": "a person who rides a bicycle or motorcycle", "example": "A group of bikers roared past on the highway."},
    "BILGE": {"pos": "noun", "meaning": "the lowest part of a ship's interior; worthless talk (informal)", "example": "Water sloshed in the bilge of the small boat."},
    "BIMBO": {"pos": "noun", "meaning": "an attractive but unintelligent person (often offensive)", "example": "He dismissed her as a bimbo, which she proved wrong."},
    "BINGE": {"pos": "noun", "meaning": "a period of excessive indulgence in food, drink, or activity", "example": "She spent the weekend on a Netflix binge."},
    "BINGO": {"pos": "noun", "meaning": "a game of chance using numbered cards; an exclamation of success", "example": "'Bingo!' she shouted, completing the puzzle."},
    "BIOME": {"pos": "noun", "meaning": "a large naturally occurring ecological community of plants and animals", "example": "The rainforest is the world's most biodiverse biome."},
    "BIPED": {"pos": "noun", "meaning": "an animal that walks on two legs", "example": "Humans are the most widespread bipeds on Earth."},
    "BIRCH": {"pos": "noun", "meaning": "a slender tree with white peeling bark, common in northern forests", "example": "Silver birch trees lined the forest path."},
    "BIRTH": {"pos": "noun", "meaning": "the emergence of a baby from the womb; the beginning of something", "example": "The birth of their child changed everything."},
    "BISON": {"pos": "noun", "meaning": "a large shaggy-haired wild ox native to North America and Europe", "example": "A herd of bison grazed on the open prairie."},
    "BLACK": {"pos": "adjective", "meaning": "the very darkest color, the opposite of white; absorbing all light", "example": "She wore a black dress to the concert."},
    "BLADE": {"pos": "noun", "meaning": "the flat cutting edge of a knife or sword; a flat leaf of grass", "example": "He sharpened the blade on a whetstone."},
    "BLAME": {"pos": "verb", "meaning": "to hold responsible for a fault or wrong; to assign fault", "example": "Don't blame yourself—it was an accident."},
    "BLAND": {"pos": "adjective", "meaning": "lacking strong features or flavor; mild; not stimulating", "example": "The food was bland and unseasoned."},
    "BLANK": {"pos": "adjective", "meaning": "not written or printed on; showing no expression; empty", "example": "She stared at the blank page, unable to begin."},
    "BLARE": {"pos": "verb", "meaning": "to make a loud, harsh sound; to sound out noisily", "example": "Car horns blared in the traffic jam."},
    "BLASE": {"pos": "adjective", "meaning": "unimpressed by things because one has experienced them so often", "example": "After years of travel she had become blasé about luxury hotels."},
    "BLAST": {"pos": "noun", "meaning": "a destructive wave of pressure from an explosion; a strong gust", "example": "The blast shattered every window in the building."},
    "BLAZE": {"pos": "noun", "meaning": "a large and fiercely burning fire; a very bright display", "example": "Firefighters battled the blaze for hours."},
    "BLEAK": {"pos": "adjective", "meaning": "bare and exposed; offering little hope; cold and cheerless", "example": "The future looked bleak after the factory closed."},
    "BLEAT": {"pos": "verb", "meaning": "to make the cry of a sheep or goat; to speak in a weak whining voice", "example": "The lamb bleated for its mother."},
    "BLEED": {"pos": "verb", "meaning": "to lose blood from the body; to drain money or resources", "example": "He pressed a cloth to the wound to stop the bleeding."},
    "BLEEP": {"pos": "noun", "meaning": "a short high-pitched sound made by an electronic device", "example": "The monitor emitted a steady bleep."},
    "BLEND": {"pos": "verb", "meaning": "to mix different things together smoothly; to combine", "example": "Blend the ingredients until smooth."},
    "BLESS": {"pos": "verb", "meaning": "to make or pronounce holy; to grant divine favor or protection", "example": "The priest blessed the congregation."},
    "BLIMP": {"pos": "noun", "meaning": "a non-rigid airship; an obese person (informal)", "example": "A blimp floated over the stadium during the game."},
    "BLIND": {"pos": "adjective", "meaning": "unable to see; done without looking; unwilling to notice", "example": "He was blind in one eye since birth."},
    "BLING": {"pos": "noun", "meaning": "expensive and flashy jewelry or accessories (informal)", "example": "She was covered in gold bling from head to toe."},
    "BLINI": {"pos": "noun", "meaning": "small buckwheat pancakes from Russian cuisine, often served with sour cream", "example": "They served blini with smoked salmon and caviar."},
    "BLINK": {"pos": "verb", "meaning": "to open and close the eyes quickly; to flash on and off", "example": "He blinked in the sudden bright light."},
    "BLISS": {"pos": "noun", "meaning": "perfect happiness; serene joy", "example": "She described retirement as pure bliss."},
    "BLITZ": {"pos": "noun", "meaning": "a sudden, intensive attack; a period of rapid intense effort", "example": "They did a blitz on the backlog of paperwork."},
    "BLOAT": {"pos": "verb", "meaning": "to cause to swell with gas or liquid; to expand excessively", "example": "Eating too fast can bloat your stomach."},
    "BLOCK": {"pos": "noun", "meaning": "a solid rectangular piece; an obstacle; a city block", "example": "He ran around the block for exercise."},
    "BLOKE": {"pos": "noun", "meaning": "a man (British informal)", "example": "He seemed like a decent bloke."},
    "BLOND": {"pos": "adjective", "meaning": "having fair or golden hair; a pale golden-yellow color", "example": "She had long blond hair."},
    "BLOOD": {"pos": "noun", "meaning": "the red fluid circulated by the heart through the body", "example": "Blood is thicker than water, they say."},
    "BLOOM": {"pos": "noun", "meaning": "a flower; the state or period of flowering; a flush of health", "example": "Cherry blossoms were in full bloom."},
    "BLUFF": {"pos": "verb", "meaning": "to deceive by a show of confidence; to pretend", "example": "He was bluffing—he had no idea what to do."},
    "BLUNT": {"pos": "adjective", "meaning": "not sharp; speaking plainly without tact", "example": "She gave a blunt assessment of the problem."},
    "BLURB": {"pos": "noun", "meaning": "a short description of a book printed on its cover; promotional copy", "example": "The blurb made the novel sound thrilling."},
    "BLURT": {"pos": "verb", "meaning": "to say something suddenly and without thinking", "example": "He blurted out the secret before he could stop himself."},
    "BLUSH": {"pos": "verb", "meaning": "to become red in the face from embarrassment or shame", "example": "She blushed when he complimented her."},
    "BOARD": {"pos": "noun", "meaning": "a long flat piece of wood; a committee; to get onto a vehicle", "example": "The board of directors met quarterly."},
    "BOAST": {"pos": "verb", "meaning": "to talk with excessive pride about one's achievements", "example": "He liked to boast about his collection of vintage cars."},
    "BOGUS": {"pos": "adjective", "meaning": "not genuine; fake or fraudulent", "example": "The passport turned out to be bogus."},
    "BOLTS": {"pos": "noun", "meaning": "metal pins used to fasten things; rolls of fabric; sudden movements", "example": "She used bolts and nuts to assemble the shelves."},
    "BOLUS": {"pos": "noun", "meaning": "a small rounded mass of chewed food; a single dose of medicine", "example": "A bolus of medication was administered through the IV."},
    "BONUS": {"pos": "noun", "meaning": "an extra payment or benefit beyond what is normal", "example": "Staff received a Christmas bonus."},
    "BOOST": {"pos": "verb", "meaning": "to increase or improve; to push upward", "example": "Praise can boost a child's confidence."},
    "BOOTH": {"pos": "noun", "meaning": "a small enclosed area; a stall at a market or fair", "example": "She ducked into a phone booth to take the call."},
    "BORAX": {"pos": "noun", "meaning": "a white mineral salt used in cleaning products and glass-making", "example": "Borax can be used as a natural cleaning agent."},
    "BOSOM": {"pos": "noun", "meaning": "a person's chest; the center or heart of something", "example": "She held the child to her bosom."},
    "BOTCH": {"pos": "verb", "meaning": "to carry out a task badly; to bungle or mess up", "example": "He botched the repair and made things worse."},
    "BOUGH": {"pos": "noun", "meaning": "a main branch of a tree", "example": "Holly hung from every bough."},
    "BOUND": {"pos": "adjective", "meaning": "certain to do something; tied; heading in a direction", "example": "She was bound to succeed with that much talent."},
    "BOXER": {"pos": "noun", "meaning": "a person who boxes as a sport; a breed of dog", "example": "The boxer trained for months before the championship."},
    "BRACE": {"pos": "noun", "meaning": "a device that holds or supports; paired items; to prepare for impact", "example": "Brace yourself—this might hurt a little."},
    "BRAID": {"pos": "noun", "meaning": "a length of hair or threads woven together; a plait", "example": "She wore her hair in a long braid."},
    "BRAIN": {"pos": "noun", "meaning": "the organ inside the skull that controls mental and physical activity", "example": "Exercise is as good for the brain as it is for the body."},
    "BRAKE": {"pos": "noun", "meaning": "a device for slowing or stopping a vehicle", "example": "She pressed the brake hard and the car skidded."},
    "BRAND": {"pos": "noun", "meaning": "a trademark or distinctive name; a type of product; a mark burned in", "example": "The brand was instantly recognizable worldwide."},
    "BRAVE": {"pos": "adjective", "meaning": "ready to face and endure danger or pain; courageous", "example": "She was brave enough to speak up in front of everyone."},
    "BRAVO": {"pos": "interjection", "meaning": "an exclamation of praise used to applaud a performance", "example": "'Bravo!' the audience shouted as the curtain fell."},
    "BRAWL": {"pos": "noun", "meaning": "a rough and noisy fight or quarrel", "example": "A brawl broke out in the stands during the match."},
    "BRAWN": {"pos": "noun", "meaning": "physical strength; well-developed muscles", "example": "The job required brawn as much as brains."},
    "BREAD": {"pos": "noun", "meaning": "a staple food made from flour, water, and yeast that is baked", "example": "The smell of fresh bread filled the bakery."},
    "BREAK": {"pos": "verb", "meaning": "to separate into pieces; to interrupt; to fail to keep a rule", "example": "Be careful not to break the glass."},
    "BREED": {"pos": "noun", "meaning": "a particular variety of animal; a sort of person; to produce offspring", "example": "Golden retrievers are a popular breed of dog."},
    "BRIBE": {"pos": "noun", "meaning": "money or a favor given to influence someone's actions improperly", "example": "The official was caught accepting a bribe."},
    "BRICK": {"pos": "noun", "meaning": "a block of baked clay used in building; a reliable person (informal)", "example": "The house was built of solid red brick."},
    "BRIDE": {"pos": "noun", "meaning": "a woman on her wedding day or just before and after it", "example": "The bride wore a simple white gown."},
    "BRIEF": {"pos": "adjective", "meaning": "short in duration; concise; using few words", "example": "She gave a brief summary of the meeting."},
    "BRINE": {"pos": "noun", "meaning": "water strongly saturated with salt; the sea", "example": "Olives are preserved in brine."},
    "BRING": {"pos": "verb", "meaning": "to carry or lead something to a place; to cause to happen", "example": "Can you bring me a glass of water?"},
    "BRINK": {"pos": "noun", "meaning": "the extreme edge of something; the point just before something critical", "example": "The country was on the brink of economic collapse."},
    "BRISK": {"pos": "adjective", "meaning": "active and energetic; pleasantly cold and fresh", "example": "They set off at a brisk pace."},
    "BROAD": {"pos": "adjective", "meaning": "wide; covering a large area or range; general, not specific", "example": "She had a broad knowledge of history."},
    "BROIL": {"pos": "verb", "meaning": "to cook meat by direct exposure to heat; to be very hot", "example": "He broiled the salmon under the grill."},
    "BROOD": {"pos": "verb", "meaning": "to think deeply and sadly about something; to sit on eggs to hatch them", "example": "She brooded over the argument all day."},
    "BROOK": {"pos": "noun", "meaning": "a small stream; to tolerate or accept", "example": "A clear brook babbled through the meadow."},
    "BROOM": {"pos": "noun", "meaning": "a brush on a long handle for sweeping floors", "example": "She swept the porch with a broom."},
    "BROTH": {"pos": "noun", "meaning": "a thin soup made by simmering meat, vegetables, or bones", "example": "She sipped a warm mug of chicken broth."},
    "BROWN": {"pos": "adjective", "meaning": "a color like that of dark wood or rich soil", "example": "The autumn leaves turned brown and fell."},
    "BRUNT": {"pos": "noun", "meaning": "the worst part or main force of something", "example": "The coastal towns bore the brunt of the storm."},
    "BRUSH": {"pos": "noun", "meaning": "an implement with bristles for cleaning or painting; a brief contact", "example": "He gave the dog a quick brush."},
    "BRUTE": {"pos": "noun", "meaning": "a rough, violent, or brutal person; an animal as opposed to a human", "example": "Don't be such a brute—be gentle."},
    "BUDDY": {"pos": "noun", "meaning": "a close friend; a companion (informal)", "example": "He's been my buddy since we were kids."},
    "BUDGE": {"pos": "verb", "meaning": "to move slightly from a position; to cause to change one's mind", "example": "The stubborn mule refused to budge."},
    "BUGLE": {"pos": "noun", "meaning": "a brass wind instrument used for military calls and signals", "example": "The bugle sounded reveille at dawn."},
    "BUILD": {"pos": "verb", "meaning": "to construct by assembling materials; to develop gradually", "example": "They built the house from reclaimed wood."},
    "BULGE": {"pos": "noun", "meaning": "a rounded swelling or protrusion; to swell outward", "example": "His pockets had a suspicious bulge."},
    "BULLY": {"pos": "noun", "meaning": "a person who habitually intimidates or harasses weaker people", "example": "The bully was finally reported to the principal."},
    "BUMPY": {"pos": "adjective", "meaning": "uneven; having many bumps; causing jolts when traveled on", "example": "The dirt road was bumpy and rutted."},
    "BUNCH": {"pos": "noun", "meaning": "a number of things growing or held together", "example": "She carried a bunch of wildflowers."},
    "BUNNY": {"pos": "noun", "meaning": "a small rabbit; a young or pet rabbit (informal)", "example": "The children chased the bunny around the garden."},
    "BURLY": {"pos": "adjective", "meaning": "large and strong; heavily built", "example": "A burly security guard stood at the entrance."},
    "BURNS": {"pos": "verb", "meaning": "to be on fire; to be hot; to injure with heat or chemicals", "example": "The fire burns brightest in winter."},
    "BURST": {"pos": "verb", "meaning": "to break open suddenly; to rush somewhere suddenly", "example": "The pipe burst in the cold and flooded the basement."},
    "BUYER": {"pos": "noun", "meaning": "a person who purchases goods or services", "example": "A serious buyer made an offer on the house."},
    "BYLAW": {"pos": "noun", "meaning": "a rule made by a local authority or organization", "example": "The bylaw restricted parking near the school."},
    "BYTES": {"pos": "noun", "meaning": "units of digital information, typically equal to 8 bits", "example": "The file was just a few hundred bytes in size."},
    "BYWAY": {"pos": "noun", "meaning": "a minor road or path; a lesser-known aspect of a subject", "example": "They took a scenic byway through the countryside."},

    # ── C ──────────────────────────────────────────────────────────────────

    "CABAL": {"pos": "noun", "meaning": "a secret political faction plotting to seize power", "example": "A cabal of ministers conspired against the prime minister."},
    "CABIN": {"pos": "noun", "meaning": "a small wooden shelter or house; a compartment on a ship or aircraft", "example": "They spent the weekend in a log cabin by the lake."},
    "CABLE": {"pos": "noun", "meaning": "a thick rope or wire; a TV system; an overseas telegram", "example": "The cable car climbed slowly up the mountain."},
    "CACHE": {"pos": "noun", "meaning": "a hidden store of something; temporary computer storage", "example": "Hikers discovered a cache of supplies left by earlier explorers."},
    "CACTI": {"pos": "noun", "meaning": "plural of cactus; spiny succulent plants adapted to dry climates", "example": "The windowsill was lined with small potted cacti."},
    "CADET": {"pos": "noun", "meaning": "a young trainee in the armed forces or police", "example": "The cadet saluted his commanding officer."},
    "CADGE": {"pos": "verb", "meaning": "to beg or get something by imposing on others", "example": "He tried to cadge a cigarette from passers-by."},
    "CADRE": {"pos": "noun", "meaning": "a small group of trained people forming the core of a larger group", "example": "A cadre of experts was assembled to tackle the crisis."},
    "CAMEL": {"pos": "noun", "meaning": "a large desert mammal with one or two humps, used for transport", "example": "A camel can survive days without water."},
    "CAMEO": {"pos": "noun", "meaning": "a small carved gem; a brief notable appearance by a celebrity in a film", "example": "The director made a cameo in his own movie."},
    "CANAL": {"pos": "noun", "meaning": "an artificial waterway built for navigation or irrigation", "example": "Barges floated through the old canal."},
    "CANDY": {"pos": "noun", "meaning": "sweets; confectionery made primarily from sugar", "example": "The children picked candy from the jar."},
    "CANNY": {"pos": "adjective", "meaning": "having a sharp mind and good judgment; shrewd and careful", "example": "She made a canny investment that paid off years later."},
    "CANOE": {"pos": "noun", "meaning": "a narrow lightweight boat propelled by paddles", "example": "They paddled the canoe upstream against the current."},
    "CANON": {"pos": "noun", "meaning": "a general rule or principle; works considered authentic; a church official", "example": "Shakespeare is central to the literary canon."},
    "CAPER": {"pos": "noun", "meaning": "a playful jump or leap; a crime (informal); a pickled flower bud used in cooking", "example": "The children cut capers on the lawn."},
    "CARAT": {"pos": "noun", "meaning": "a unit of weight for gems; a measure of gold purity", "example": "The ring was set with a two-carat diamond."},
    "CARGO": {"pos": "noun", "meaning": "goods carried by a ship, aircraft, or vehicle", "example": "The cargo ship was loaded with steel and timber."},
    "CAROL": {"pos": "noun", "meaning": "a song of praise, especially a Christmas hymn", "example": "Children sang carols outside the church."},
    "CARRY": {"pos": "verb", "meaning": "to hold and transport something; to support the weight of", "example": "She carried the heavy bags up three flights of stairs."},
    "CARVE": {"pos": "verb", "meaning": "to cut into a hard material to form a shape; to slice meat", "example": "He carved a duck from a block of wood."},
    "CASTE": {"pos": "noun", "meaning": "a hereditary class in a social system; a social division", "example": "The caste system divided society into rigid groups."},
    "CATCH": {"pos": "verb", "meaning": "to seize and hold; to intercept; to contract an illness", "example": "She caught the ball with one hand."},
    "CAUSE": {"pos": "noun", "meaning": "a reason or motive; a movement or aim one supports", "example": "She devoted her life to the cause of equality."},
    "CEDAR": {"pos": "noun", "meaning": "an evergreen tree with fragrant reddish wood", "example": "The wardrobe was made of cedar to repel moths."},
    "CEASE": {"pos": "verb", "meaning": "to come to an end; to stop doing something", "example": "The rain ceased as quickly as it had started."},
    "CELLO": {"pos": "noun", "meaning": "a large stringed instrument played with a bow, held between the knees", "example": "She played the cello in the city orchestra."},
    "CHAIN": {"pos": "noun", "meaning": "a series of linked metal rings; a sequence of connected things", "example": "He wore a heavy gold chain around his neck."},
    "CHAIR": {"pos": "noun", "meaning": "a separate seat for one person; the chairperson of a meeting", "example": "Please take a chair and make yourself comfortable."},
    "CHALK": {"pos": "noun", "meaning": "a soft white limestone used for writing and drawing", "example": "The teacher wrote equations on the board in chalk."},
    "CHAMP": {"pos": "noun", "meaning": "a champion; to chew noisily and vigorously", "example": "The horse champed at the bit, eager to run."},
    "CHANT": {"pos": "noun", "meaning": "a rhythmic repetitive song; to sing or shout repetitively", "example": "The crowd began to chant the player's name."},
    "CHAOS": {"pos": "noun", "meaning": "complete disorder and confusion; a state of utter mayhem", "example": "The power cut threw the city into chaos."},
    "CHARM": {"pos": "noun", "meaning": "the power to attract and delight; a lucky trinket; a spell", "example": "He won everyone over with his natural charm."},
    "CHART": {"pos": "noun", "meaning": "a diagram or graph; a map; a list of popular music rankings", "example": "The album went straight to number one in the charts."},
    "CHASE": {"pos": "verb", "meaning": "to pursue rapidly in order to catch; to follow eagerly", "example": "The dog chased the ball across the field."},
    "CHASM": {"pos": "noun", "meaning": "a deep fissure in the earth; a wide difference between two things", "example": "A chasm separated the two factions."},
    "CHEAP": {"pos": "adjective", "meaning": "low in price; charging low prices; of poor quality", "example": "The meal was good and surprisingly cheap."},
    "CHEAT": {"pos": "verb", "meaning": "to act dishonestly to gain an advantage; to deceive", "example": "Cheating in an exam can lead to expulsion."},
    "CHECK": {"pos": "verb", "meaning": "to examine for accuracy; to stop; a bank payment order", "example": "Always check your work before submitting it."},
    "CHEEK": {"pos": "noun", "meaning": "the fleshy part of the face below the eye; impudent behavior", "example": "She had the cheek to ask for a raise after one week."},
    "CHEER": {"pos": "verb", "meaning": "to shout encouragement; to make happier", "example": "The crowd cheered as the runner crossed the finish line."},
    "CHESS": {"pos": "noun", "meaning": "a board game of strategy played by two players on a checkered board", "example": "He spent hours studying chess openings."},
    "CHEST": {"pos": "noun", "meaning": "the front part of the body enclosed by the ribs; a large strong box", "example": "He kept his valuables in an old wooden chest."},
    "CHIEF": {"pos": "noun", "meaning": "a leader or head of a group; the most important", "example": "The chief of police addressed the press."},
    "CHILD": {"pos": "noun", "meaning": "a young human being; a son or daughter of any age", "example": "Every child deserves access to education."},
    "CHILE": {"pos": "noun", "meaning": "a hot pepper; variant spelling of chili", "example": "She added dried chile to the sauce for extra heat."},
    "CHILL": {"pos": "noun", "meaning": "a coldness in the air; a moderate but unpleasant coldness", "example": "There was a chill in the evening air."},
    "CHIME": {"pos": "verb", "meaning": "to make a melodious ringing sound; to agree with", "example": "The clock chimed six times."},
    "CHIMP": {"pos": "noun", "meaning": "a chimpanzee; our closest living animal relative", "example": "The chimp used a stick to extract termites."},
    "CHINA": {"pos": "noun", "meaning": "fine white ceramic material; tableware made from it", "example": "She set the table with her best china."},
    "CHINK": {"pos": "noun", "meaning": "a small gap or crack that lets in light; a ringing sound", "example": "A chink of light showed under the door."},
    "CHIRP": {"pos": "verb", "meaning": "to make a short sharp sound like a small bird or insect", "example": "Crickets chirped in the warm evening grass."},
    "CHIVE": {"pos": "noun", "meaning": "a slender herb with a mild onion flavor, used as a garnish", "example": "Sprinkle chopped chive over the potato soup."},
    "CHOCK": {"pos": "noun", "meaning": "a wedge used to prevent a wheel or barrel from moving", "example": "He placed a chock under the tire to stop the car rolling."},
    "CHOIR": {"pos": "noun", "meaning": "a group of singers who perform together, often in church", "example": "The choir sang with remarkable precision."},
    "CHOKE": {"pos": "verb", "meaning": "to obstruct breathing; to fail under pressure", "example": "She choked on a fishbone."},
    "CHOMP": {"pos": "verb", "meaning": "to munch noisily and vigorously", "example": "He chomped on his sandwich without stopping to talk."},
    "CHORD": {"pos": "noun", "meaning": "a group of musical notes played simultaneously; a straight line in geometry", "example": "She struck a minor chord and the room fell quiet."},
    "CHORE": {"pos": "noun", "meaning": "a routine and often tedious task around the house", "example": "Washing up is a chore nobody enjoys."},
    "CHUCK": {"pos": "verb", "meaning": "to throw casually; to discard; to give up (informal)", "example": "He chucked the empty can into the bin."},
    "CHUNK": {"pos": "noun", "meaning": "a thick, solid piece of something; a substantial amount", "example": "She cut the bread into large chunks."},
    "CHURN": {"pos": "verb", "meaning": "to stir or agitate vigorously; to produce butter by agitation", "example": "The ship's propellers churned the water white."},
    "CHUTE": {"pos": "noun", "meaning": "a steep channel or slide for moving things to a lower level", "example": "Laundry was dropped down the chute to the basement."},
    "CIDER": {"pos": "noun", "meaning": "a drink made from fermented apple juice; apple juice (US)", "example": "They sat by the fire with mugs of warm cider."},
    "CIGAR": {"pos": "noun", "meaning": "a rolled cylinder of tobacco for smoking", "example": "He lit a cigar and leaned back in his chair."},
    "CINCH": {"pos": "noun", "meaning": "something very easy to do; a certainty (informal)", "example": "With her talent, winning will be a cinch."},
    "CIRCA": {"pos": "preposition", "meaning": "approximately; used to indicate an approximate date", "example": "The manuscript dates from circa 1350."},
    "CIVIC": {"pos": "adjective", "meaning": "relating to a city or citizenship; relating to civil life", "example": "Voting is a civic duty."},
    "CIVIL": {"pos": "adjective", "meaning": "relating to ordinary citizens; polite and courteous; not military", "example": "She kept the discussion civil despite strong disagreement."},
    "CLAIM": {"pos": "verb", "meaning": "to state as fact; to demand as one's due; to assert a right to", "example": "He claimed he had never seen the document."},
    "CLAMP": {"pos": "noun", "meaning": "a device for holding things firmly together; to hold tightly", "example": "Use a clamp to hold the wood while the glue dries."},
    "CLANG": {"pos": "verb", "meaning": "to make a loud resonant metallic sound", "example": "The iron gate clanged shut behind her."},
    "CLASH": {"pos": "verb", "meaning": "to conflict; to collide noisily; to be incompatible", "example": "The two personalities clashed from the beginning."},
    "CLASP": {"pos": "verb", "meaning": "to grasp something firmly with the hand; a fastening device", "example": "She clasped his hand as he slipped away."},
    "CLASS": {"pos": "noun", "meaning": "a group sharing characteristics; a lesson; social distinction; elegance", "example": "She had class and style that money couldn't buy."},
    "CLEAN": {"pos": "adjective", "meaning": "free from dirt or marks; morally pure; complete", "example": "A clean break is sometimes the kindest option."},
    "CLEAR": {"pos": "adjective", "meaning": "transparent; easy to understand; free of obstruction", "example": "The instructions were perfectly clear."},
    "CLEAT": {"pos": "noun", "meaning": "a T-shaped bar to which ropes are fastened; a metal plate on a shoe sole", "example": "He secured the rope around the cleat."},
    "CLEFT": {"pos": "noun", "meaning": "a split or narrow opening; divided or split apart", "example": "She had a small cleft in her chin."},
    "CLERK": {"pos": "noun", "meaning": "a person employed to keep records or accounts; a sales assistant", "example": "The clerk filed the documents alphabetically."},
    "CLICK": {"pos": "verb", "meaning": "to make a short sharp sound; to press a mouse button; to suddenly understand", "example": "The pieces finally clicked into place."},
    "CLIFF": {"pos": "noun", "meaning": "a steep rock face, especially at the sea's edge", "example": "They stood at the cliff's edge and watched the waves crash below."},
    "CLIMB": {"pos": "verb", "meaning": "to go up using one's hands and feet; to rise", "example": "She climbed the rope to the top without stopping."},
    "CLING": {"pos": "verb", "meaning": "to hold on tightly; to adhere to a surface; to be emotionally dependent", "example": "The child clung to his mother's hand."},
    "CLINK": {"pos": "verb", "meaning": "to make a light ringing sound, as glasses do when touched together", "example": "They clinked glasses and said cheers."},
    "CLOAK": {"pos": "noun", "meaning": "a sleeveless outer garment; something that conceals", "example": "Under the cloak of darkness, they made their escape."},
    "CLOCK": {"pos": "noun", "meaning": "a device for measuring and displaying time", "example": "The clock on the wall showed half past two."},
    "CLONE": {"pos": "noun", "meaning": "a genetically identical copy of an organism; an exact copy", "example": "The sheep was the world's first cloned mammal."},
    "CLOSE": {"pos": "adjective", "meaning": "near in space, time, or relationship; a narrow escape", "example": "That was a close call."},
    "CLOTH": {"pos": "noun", "meaning": "woven fabric material; a piece of fabric used for a purpose", "example": "She polished the silver with a soft cloth."},
    "CLOUD": {"pos": "noun", "meaning": "a mass of water vapor visible in the sky; something that obscures", "example": "Dark clouds gathered on the horizon."},
    "CLOUT": {"pos": "noun", "meaning": "influence or power; a heavy blow", "example": "He had enough clout to get things done quickly."},
    "CLOVE": {"pos": "noun", "meaning": "a dried flower bud used as a spice; one segment of a garlic bulb", "example": "Add two cloves of garlic to the pan."},
    "CLOWN": {"pos": "noun", "meaning": "a comic performer wearing a costume; a foolish person", "example": "A clown performed tricks for the children."},
    "CLUMP": {"pos": "noun", "meaning": "a compact mass of trees or plants; a dull heavy thud", "example": "A clump of oak trees stood at the field's edge."},
    "COACH": {"pos": "noun", "meaning": "a sports trainer; a railway car; a long-distance bus; to train", "example": "The coach pushed the team through grueling sessions."},
    "COAST": {"pos": "noun", "meaning": "the land bordering the sea; to move without using power", "example": "They drove along the rocky coast."},
    "COBRA": {"pos": "noun", "meaning": "a venomous snake that can spread its neck into a hood", "example": "A king cobra rose up before the snake charmer."},
    "COCOA": {"pos": "noun", "meaning": "a powder made from cacao beans; a warm drink made from it", "example": "She warmed her hands on a mug of cocoa."},
    "COMET": {"pos": "noun", "meaning": "a celestial body with a bright nucleus and a tail of gas and dust", "example": "Halley's Comet returns every 75 years."},
    "COMIC": {"pos": "adjective", "meaning": "causing laughter; relating to comedy", "example": "The actor had perfect comic timing."},
    "COMMA": {"pos": "noun", "meaning": "a punctuation mark used to indicate a pause or separate items", "example": "He placed a comma in the wrong position and changed the meaning entirely."},
    "CONCH": {"pos": "noun", "meaning": "a large spiral shell; the mollusc that lives in it", "example": "She held the conch to her ear and heard the sea."},
    "CONDO": {"pos": "noun", "meaning": "a privately owned apartment in a larger building (informal)", "example": "They bought a condo in the city centre."},
    "CORAL": {"pos": "noun", "meaning": "a hard marine organism that forms reefs; a pinkish-red color", "example": "Bleaching is destroying the world's coral reefs."},
    "COUCH": {"pos": "noun", "meaning": "a comfortable sofa; to express something in particular terms", "example": "She dozed off on the couch after dinner."},
    "COUGH": {"pos": "verb", "meaning": "to expel air from the lungs with a sudden sharp sound", "example": "He coughed throughout the entire film."},
    "COUNT": {"pos": "verb", "meaning": "to determine the total number of; to be important; a nobleman", "example": "Every vote counts."},
    "COURT": {"pos": "noun", "meaning": "a place where legal cases are heard; an enclosed area for sport; to woo", "example": "The case was heard in the High Court."},
    "COVER": {"pos": "verb", "meaning": "to place something over; to deal with a topic; to travel a distance", "example": "She covered the pot with a lid."},
    "COVET": {"pos": "verb", "meaning": "to eagerly desire something belonging to another person", "example": "He coveted his neighbor's gleaming new car."},
    "CRACK": {"pos": "noun", "meaning": "a narrow gap or break; a sharp explosive sound; first-rate (informal)", "example": "There was a crack in the wall after the earthquake."},
    "CRAFT": {"pos": "noun", "meaning": "a skill; an activity requiring skill; a vessel or aircraft", "example": "Pottery is a craft that takes years to master."},
    "CRANE": {"pos": "noun", "meaning": "a large machine for lifting heavy objects; a large wading bird", "example": "A crane lowered the steel beam into position."},
    "CRANK": {"pos": "noun", "meaning": "an eccentric person; a handle for starting an engine; to turn", "example": "She was considered a health food crank by her friends."},
    "CRASH": {"pos": "verb", "meaning": "to collide with great force; to break noisily; to fail suddenly", "example": "The stock market crashed in 1929."},
    "CRATE": {"pos": "noun", "meaning": "a slatted wooden or plastic box used for transporting goods", "example": "Oranges were packed in wooden crates."},
    "CRAVE": {"pos": "verb", "meaning": "to feel a powerful desire for something; to long for intensely", "example": "She craved adventure after years behind a desk."},
    "CRAWL": {"pos": "verb", "meaning": "to move on hands and knees; to move very slowly", "example": "Traffic crawled through the city center."},
    "CRAZY": {"pos": "adjective", "meaning": "mentally ill; extremely enthusiastic; very foolish", "example": "He was crazy about jazz from an early age."},
    "CREAK": {"pos": "verb", "meaning": "to make a prolonged squeaking sound under stress or strain", "example": "The old floorboards creaked under his weight."},
    "CREAM": {"pos": "noun", "meaning": "the rich fatty part of milk; a pale yellow color; the best", "example": "She poured thick cream over the strawberries."},
    "CREED": {"pos": "noun", "meaning": "a set of beliefs or principles, especially religious ones", "example": "He lived by a simple creed: honesty above all."},
    "CREEK": {"pos": "noun", "meaning": "a small narrow stream; an inlet of the sea", "example": "The children caught frogs in the creek."},
    "CREEP": {"pos": "verb", "meaning": "to move slowly and quietly to avoid being noticed", "example": "She crept downstairs so as not to wake anyone."},
    "CREPE": {"pos": "noun", "meaning": "a thin light pancake; a light crinkled fabric", "example": "She ordered a crepe with lemon and sugar."},
    "CREST": {"pos": "noun", "meaning": "the top of a hill or wave; a tuft on an animal's head; a family emblem", "example": "They reached the crest of the hill and paused to rest."},
    "CRIME": {"pos": "noun", "meaning": "an illegal act punishable by law; a harmful or shameful act", "example": "Theft is a crime with serious consequences."},
    "CRISP": {"pos": "adjective", "meaning": "firm and dry with a pleasing snap; brisk; neat and precise", "example": "She loved the crisp air of an autumn morning."},
    "CROAK": {"pos": "verb", "meaning": "to make a deep harsh sound like a frog; to speak hoarsely", "example": "Frogs croaked by the pond all evening."},
    "CRONE": {"pos": "noun", "meaning": "an old woman, especially one who is thin or withered", "example": "The old crone sat muttering by the fire."},
    "CROOK": {"pos": "noun", "meaning": "a criminal; a shepherd's hooked staff; something bent", "example": "The detective was determined to catch every crook in town."},
    "CROON": {"pos": "verb", "meaning": "to sing or hum softly in a low, soothing voice", "example": "She crooned a lullaby to the sleeping child."},
    "CROSS": {"pos": "adjective", "meaning": "angry or annoyed; a shape formed by two lines intersecting", "example": "She was cross with him for being late again."},
    "CROWD": {"pos": "noun", "meaning": "a large number of people gathered together", "example": "A crowd gathered to watch the street performer."},
    "CROWN": {"pos": "noun", "meaning": "a circular ornamental headpiece worn by royalty; the top of something", "example": "She was crowned queen in a grand ceremony."},
    "CRUDE": {"pos": "adjective", "meaning": "in a natural unrefined state; blunt or offensive; roughly made", "example": "The crude oil was shipped to the refinery."},
    "CRUEL": {"pos": "adjective", "meaning": "causing pain or suffering deliberately; merciless", "example": "It was cruel to leave the animal outside in the rain."},
    "CRUMB": {"pos": "noun", "meaning": "a small fragment broken from bread, cake, or a biscuit", "example": "Crumbs covered the cutting board."},
    "CRUSH": {"pos": "verb", "meaning": "to press with force until flattened; an infatuation; a dense crowd", "example": "She had a crush on the boy next door."},
    "CRUST": {"pos": "noun", "meaning": "the hard outer layer of bread; the outermost layer of the Earth", "example": "He preferred the crust of the bread to the soft inside."},
    "CRYPT": {"pos": "noun", "meaning": "an underground room in a church, used as a chapel or for burial", "example": "Ancient tombs lay in the cathedral crypt."},
    "CUBIT": {"pos": "noun", "meaning": "an ancient unit of measurement equal to the length of a forearm", "example": "The ark was measured in cubits, roughly 18 inches each."},
    "CUMIN": {"pos": "noun", "meaning": "a spice made from the seeds of a Mediterranean plant, widely used in cooking", "example": "Add a teaspoon of cumin to the lentil soup."},
    "CUPID": {"pos": "noun", "meaning": "the Roman god of love; a depiction of a chubby winged boy with a bow", "example": "Cupid's arrow struck both of them at the same party."},
    "CURLY": {"pos": "adjective", "meaning": "having curls; spiraling or winding in shape", "example": "She had naturally curly hair."},
    "CURRY": {"pos": "noun", "meaning": "a spiced sauce or dish, originating in South Asian cuisines", "example": "He ordered a mild chicken curry with rice."},
    "CURSE": {"pos": "noun", "meaning": "a solemn expression of a wish for harm to befall someone; profanity", "example": "She muttered a curse under her breath."},
    "CURVE": {"pos": "noun", "meaning": "a smoothly bending line or surface; a deviation from a straight path", "example": "The road disappeared around a sharp curve."},
    "CYCLE": {"pos": "noun", "meaning": "a series of events that repeats regularly; a bicycle; to ride a bicycle", "example": "The water cycle is essential to all life on Earth."},
    "CYNIC": {"pos": "noun", "meaning": "a person who distrusts human sincerity and sees selfish motives everywhere", "example": "Only a cynic would doubt that anyone acts from kindness."},
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

    # Filter to only words present in the word list
    to_insert = {w: DEFINITIONS[w] for w in words if w in DEFINITIONS}
    print(f"Definitions available: {len(to_insert)}")

    if csv_out:
        csv_path = _WORDS_FILE.parent / "definitions_ac.csv"
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
    parser = argparse.ArgumentParser(description="Seed word definitions for A–C words")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing definitions")
    parser.add_argument("--csv", action="store_true", help="Also write a CSV backup file")
    args = parser.parse_args()
    asyncio.run(main(overwrite=args.overwrite, csv_out=args.csv))
