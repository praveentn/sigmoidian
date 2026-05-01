#!/usr/bin/env python3
"""
Seed word definitions for D–G words using Claude-generated data.

Usage:
    python scripts/seed_definitions_dg.py                # insert missing only
    python scripts/seed_definitions_dg.py --overwrite    # replace existing
    python scripts/seed_definitions_dg.py --csv          # also dump CSV
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

    # ── D ──────────────────────────────────────────────────────────────────

    "DACHA": {"pos": "noun", "meaning": "a Russian country house or cottage used as a summer retreat", "example": "They spent August at their dacha outside Moscow."},
    "DAILY": {"pos": "adjective", "meaning": "done, produced, or occurring every day", "example": "She read the daily newspaper with her morning coffee."},
    "DAIRY": {"pos": "noun", "meaning": "a place where milk and milk products are produced or sold", "example": "The dairy supplied fresh milk to the whole village."},
    "DAISY": {"pos": "noun", "meaning": "a small wild flower with white petals around a yellow centre", "example": "She wove a chain of daisies in the meadow."},
    "DALLY": {"pos": "verb", "meaning": "to waste time; to act or move slowly; to flirt", "example": "Stop dallying and get ready or we'll be late."},
    "DANCE": {"pos": "verb", "meaning": "to move rhythmically to music; to move lightly and quickly", "example": "They danced until midnight at the wedding."},
    "DANDY": {"pos": "noun", "meaning": "a man excessively concerned with elegant appearance; something excellent", "example": "He was a dandy who spent hours on his wardrobe."},
    "DAUNT": {"pos": "verb", "meaning": "to make someone feel intimidated or apprehensive", "example": "The scale of the task didn't daunt her at all."},
    "DATUM": {"pos": "noun", "meaning": "a single piece of information; a fixed point of reference", "example": "Each datum was carefully recorded in the log."},
    "DAUBS": {"pos": "noun", "meaning": "smears or blobs of a soft substance; crude paintings", "example": "The child's daubs of paint covered the page."},
    "DEATH": {"pos": "noun", "meaning": "the end of life; the permanent cessation of vital functions", "example": "The death of the old oak tree changed the landscape."},
    "DEBIT": {"pos": "noun", "meaning": "a payment taken from a bank account; an entry recording a sum owed", "example": "A direct debit pays the bill automatically each month."},
    "DEBUG": {"pos": "verb", "meaning": "to identify and remove errors from computer hardware or software", "example": "She spent the afternoon debugging the program."},
    "DEBUT": {"pos": "noun", "meaning": "a person's first appearance in a role or profession", "example": "His debut novel won three awards."},
    "DECAF": {"pos": "noun", "meaning": "decaffeinated coffee; coffee with most caffeine removed", "example": "She switched to decaf after midday."},
    "DECAL": {"pos": "noun", "meaning": "a picture or design on paper that can be transferred to another surface", "example": "He applied a dragon decal to his guitar case."},
    "DECAY": {"pos": "verb", "meaning": "to rot or decompose; to decline in quality or strength", "example": "Fallen leaves slowly decay into the soil."},
    "DECOR": {"pos": "noun", "meaning": "the furnishings and decoration of a room or building", "example": "The restaurant's decor was minimalist and elegant."},
    "DECOY": {"pos": "noun", "meaning": "a person or thing used to lure others into a trap", "example": "The detective used a decoy to draw out the suspect."},
    "DECRY": {"pos": "verb", "meaning": "to publicly condemn something as wrong or unworthy", "example": "Critics decried the new policy as a step backward."},
    "DEFER": {"pos": "verb", "meaning": "to put off to a later time; to show respectful submission to another", "example": "She deferred the decision until more data was available."},
    "DEIFY": {"pos": "verb", "meaning": "to worship or regard someone as a god; to idolize", "example": "Fans tended to deify the rock star."},
    "DEIGN": {"pos": "verb", "meaning": "to do something that one considers below one's dignity", "example": "He barely deigned to acknowledge the new employee."},
    "DEITY": {"pos": "noun", "meaning": "a god or goddess; divine status or nature", "example": "Each ancient city had its own patron deity."},
    "DELAY": {"pos": "noun", "meaning": "a period of time by which something is late; to make something late", "example": "A signal fault caused a delay of forty minutes."},
    "DELTA": {"pos": "noun", "meaning": "the fourth letter of the Greek alphabet; a triangular river mouth", "example": "The Nile Delta is one of the world's most fertile regions."},
    "DELVE": {"pos": "verb", "meaning": "to research or inquire deeply into something", "example": "She delved into the archives to find the truth."},
    "DEMON": {"pos": "noun", "meaning": "an evil spirit; a person of great energy or skill", "example": "She was a demon at chess, winning every match."},
    "DENIM": {"pos": "noun", "meaning": "a hard-wearing cotton twill fabric, typically blue, used for jeans", "example": "He wore denim from head to toe."},
    "DENSE": {"pos": "adjective", "meaning": "closely compacted; thick; stupid (informal)", "example": "The jungle was so dense that sunlight barely reached the ground."},
    "DEPOT": {"pos": "noun", "meaning": "a place for storing goods; a bus or rail station", "example": "The buses returned to the depot at night."},
    "DEPTH": {"pos": "noun", "meaning": "the distance from the top down or from front to back; intensity", "example": "The depth of the lake was impossible to measure by eye."},
    "DERBY": {"pos": "noun", "meaning": "an important horse race; a sporting contest between local rivals", "example": "The local derby always drew the biggest crowds of the season."},
    "DETER": {"pos": "verb", "meaning": "to discourage from doing something through fear or doubt", "example": "The alarm system deterred would-be burglars."},
    "DETOX": {"pos": "noun", "meaning": "a process of removing toxins from the body; withdrawal from alcohol or drugs", "example": "He checked into a clinic for a detox program."},
    "DEUCE": {"pos": "noun", "meaning": "a score of 40-40 in tennis; the number two in cards or dice", "example": "After deuce, the next point decides who takes the advantage."},
    "DEVIL": {"pos": "noun", "meaning": "the supreme spirit of evil; a wicked or mischievous person", "example": "The deal seemed too good and she feared a devil in the details."},
    "DIARY": {"pos": "noun", "meaning": "a personal daily record of events and thoughts; an appointment book", "example": "She kept a diary throughout her travels."},
    "DICEY": {"pos": "adjective", "meaning": "unpredictably dangerous or difficult; risky (informal)", "example": "The weather looked dicey for the outdoor event."},
    "DIGIT": {"pos": "noun", "meaning": "any of the numerals 0 to 9; a finger or toe", "example": "PIN numbers are usually four digits long."},
    "DINER": {"pos": "noun", "meaning": "a person who dines; a small roadside restaurant", "example": "They stopped at an all-night diner for coffee."},
    "DINGO": {"pos": "noun", "meaning": "a wild dog native to Australia", "example": "A dingo howled somewhere out in the dark."},
    "DINGY": {"pos": "adjective", "meaning": "gloomy and drab; dirty-looking", "example": "The hotel room was small and dingy."},
    "DIRTY": {"pos": "adjective", "meaning": "covered in dirt; morally wrong or dishonest", "example": "The children came home with dirty clothes after playing outside."},
    "DISCO": {"pos": "noun", "meaning": "a genre of dance music from the 1970s; a nightclub playing such music", "example": "They spent the evening dancing at a disco."},
    "DITCH": {"pos": "noun", "meaning": "a narrow channel dug in the ground for drainage; to abandon (informal)", "example": "They dug a ditch along the edge of the field."},
    "DITTY": {"pos": "noun", "meaning": "a short simple song", "example": "She hummed a cheery ditty as she worked."},
    "DIVAN": {"pos": "noun", "meaning": "a long low sofa without a back or arms; a bed base", "example": "He lounged on the divan with a book."},
    "DIVER": {"pos": "noun", "meaning": "a person who dives into water; one who works underwater", "example": "The diver explored the wreck at the bottom of the bay."},
    "DIZZY": {"pos": "adjective", "meaning": "having a sensation of spinning; making one feel unsteady", "example": "The height made her dizzy."},
    "DJINN": {"pos": "noun", "meaning": "a spirit in Islamic mythology able to take human or animal form", "example": "The djinn was said to grant three wishes."},
    "DODGE": {"pos": "verb", "meaning": "to move quickly to avoid something; to evade a question or duty", "example": "He dodged the question with a vague smile."},
    "DODGY": {"pos": "adjective", "meaning": "dishonest or unreliable; risky (British informal)", "example": "Something about his story seemed a bit dodgy."},
    "DOGMA": {"pos": "noun", "meaning": "a set of principles laid down by an authority as undeniably true", "example": "She questioned the dogma of the established church."},
    "DOILY": {"pos": "noun", "meaning": "a small decorative mat made of lace or paper", "example": "A doily sat under the vase of flowers."},
    "DOLCE": {"pos": "adjective", "meaning": "sweetly and softly (a musical direction); sweet (Italian)", "example": "The violins played the passage dolce."},
    "DOLLS": {"pos": "noun", "meaning": "small figures of a human being used as a toy or ornament", "example": "She lined her collection of dolls along the shelf."},
    "DOLOR": {"pos": "noun", "meaning": "a state of great sorrow or distress", "example": "He read the letter with growing dolor."},
    "DOLTS": {"pos": "noun", "meaning": "stupid people; dull-witted individuals", "example": "He called them dolts for not understanding the obvious."},
    "DONOR": {"pos": "noun", "meaning": "a person who donates something, especially blood or an organ", "example": "The hospital appealed for blood donors."},
    "DONUT": {"pos": "noun", "meaning": "a small fried dough cake, typically ring-shaped", "example": "She picked a glazed donut from the bakery display."},
    "DOUBT": {"pos": "noun", "meaning": "a feeling of uncertainty or lack of conviction", "example": "He had serious doubts about the plan."},
    "DOUGH": {"pos": "noun", "meaning": "a thick mixture of flour and liquid; money (informal)", "example": "She kneaded the dough until it was smooth."},
    "DOULA": {"pos": "noun", "meaning": "a trained helper who supports a woman during and after childbirth", "example": "The doula helped the mother stay calm throughout the labour."},
    "DOUSE": {"pos": "verb", "meaning": "to pour water over; to extinguish a fire", "example": "He doused the campfire before leaving."},
    "DOWEL": {"pos": "noun", "meaning": "a cylindrical peg used to fasten two pieces of wood together", "example": "She tapped each dowel into its hole."},
    "DOWRY": {"pos": "noun", "meaning": "property or money brought by a bride to her husband on marriage", "example": "The dowry included land and livestock."},
    "DOYEN": {"pos": "noun", "meaning": "the most respected or experienced person in a field", "example": "She was the doyen of British portrait painters."},
    "DOZEN": {"pos": "noun", "meaning": "a group of twelve; a large but indefinite number", "example": "She bought two dozen eggs at the market."},
    "DRAFT": {"pos": "noun", "meaning": "a preliminary version of a document; a current of air; conscription", "example": "He sent the first draft to his editor."},
    "DRAIN": {"pos": "verb", "meaning": "to cause liquid to run off; to exhaust one's energy or resources", "example": "The long day had drained her completely."},
    "DRAMA": {"pos": "noun", "meaning": "a play for stage or screen; exciting events causing tension", "example": "There was unexpected drama when the power went out."},
    "DRAPE": {"pos": "verb", "meaning": "to arrange cloth loosely over something; to hang in graceful folds", "example": "She draped a shawl over her shoulders."},
    "DRAWL": {"pos": "verb", "meaning": "to speak with slow vowel sounds; a slow manner of speaking", "example": "He answered in a lazy Southern drawl."},
    "DREAD": {"pos": "noun", "meaning": "great fear or apprehension about something", "example": "She faced Monday mornings with a sense of dread."},
    "DREAM": {"pos": "noun", "meaning": "images experienced during sleep; a cherished ambition", "example": "Her dream was to become a concert pianist."},
    "DRESS": {"pos": "noun", "meaning": "a woman's garment; clothing; to put on clothes", "example": "She wore a long blue dress to the gala."},
    "DRIFT": {"pos": "verb", "meaning": "to be carried slowly along by currents of water or air; to wander", "example": "The boat drifted downstream without a rudder."},
    "DRILL": {"pos": "noun", "meaning": "a tool for boring holes; repeated practice; a military exercise", "example": "They ran a fire drill every quarter."},
    "DRINK": {"pos": "verb", "meaning": "to take liquid into the mouth and swallow it", "example": "He drank two glasses of water after his run."},
    "DRIVE": {"pos": "verb", "meaning": "to operate a vehicle; to push or force; motivation", "example": "She drove two hours to reach the coast."},
    "DROID": {"pos": "noun", "meaning": "an android robot; a humanoid machine", "example": "The droid completed the task without complaint."},
    "DROLL": {"pos": "adjective", "meaning": "curious or unusual in a way that provokes amusement", "example": "He had a droll wit that caught people off guard."},
    "DRONE": {"pos": "noun", "meaning": "an unmanned aircraft; a male bee; a monotonous sound or speaker", "example": "A drone surveyed the flood damage from the air."},
    "DROOL": {"pos": "verb", "meaning": "to let saliva run from the mouth; to show great admiration", "example": "The dog drooled at the smell of the meat."},
    "DROOP": {"pos": "verb", "meaning": "to bend or hang downward through weakness or heaviness", "example": "The flowers drooped in the heat."},
    "DROVE": {"pos": "noun", "meaning": "a large number of people or animals moving together", "example": "Tourists arrived in droves for the festival."},
    "DROWN": {"pos": "verb", "meaning": "to die from suffocation underwater; to overwhelm completely", "example": "She was drowning in paperwork."},
    "DRUGS": {"pos": "noun", "meaning": "medicines or substances that affect the body's function", "example": "The doctor prescribed drugs to control the infection."},
    "DRUID": {"pos": "noun", "meaning": "a priest of an ancient Celtic religion; a modern follower of that religion", "example": "Druids gathered at Stonehenge for the solstice."},
    "DRUMS": {"pos": "noun", "meaning": "cylindrical percussion instruments played by beating with sticks", "example": "The drums set the pace for the whole band."},
    "DRUNK": {"pos": "adjective", "meaning": "having consumed enough alcohol to affect one's faculties", "example": "He was too drunk to drive safely."},
    "DRUPE": {"pos": "noun", "meaning": "a fleshy fruit with a stone inside, such as a plum or cherry", "example": "A cherry is a classic example of a drupe."},
    "DUCHY": {"pos": "noun", "meaning": "the territory of a duke or duchess", "example": "The duchy had been ruled by the same family for centuries."},
    "DUCKY": {"pos": "adjective", "meaning": "fine; satisfactory (informal); a term of endearment", "example": "Everything is just ducky, not a worry in the world."},
    "DUMMY": {"pos": "noun", "meaning": "a model of a human figure; a counterfeit object; a fool", "example": "The ventriloquist worked the dummy expertly."},
    "DUNCE": {"pos": "noun", "meaning": "a person who is slow at learning; a stupid person", "example": "He was no dunce—he just learned differently."},
    "DUNES": {"pos": "noun", "meaning": "mounds of sand formed by the wind, especially by the sea or in a desert", "example": "They climbed the dunes and gazed out at the ocean."},
    "DUPED": {"pos": "verb", "meaning": "deceived or tricked into believing something false", "example": "He felt embarrassed after being duped by the scam."},
    "DUSKY": {"pos": "adjective", "meaning": "darkish in color; shadowy; approaching darkness", "example": "The dusky light of evening settled over the valley."},
    "DUSTY": {"pos": "adjective", "meaning": "covered with or resembling dust; dull and outdated", "example": "The dusty attic hadn't been opened in years."},
    "DUTCH": {"pos": "adjective", "meaning": "relating to the Netherlands; going Dutch means splitting costs equally", "example": "They went Dutch on the restaurant bill."},
    "DUVET": {"pos": "noun", "meaning": "a soft thick bed cover filled with down or synthetic filling", "example": "She pulled the duvet over her head and ignored the alarm."},
    "DWARF": {"pos": "noun", "meaning": "a mythical small humanoid creature; a person of unusually small stature", "example": "The dwarf star was barely detectable through the telescope."},
    "DWEEB": {"pos": "noun", "meaning": "a studious or socially inept person (informal)", "example": "He embraced being called a dweeb once tech became cool."},
    "DWELL": {"pos": "verb", "meaning": "to live in a place; to think or speak at length about something", "example": "Don't dwell on past mistakes—look forward."},
    "DYING": {"pos": "adjective", "meaning": "in the process of dying; declining; done just before death", "example": "She granted him a dying wish."},

    # ── E ──────────────────────────────────────────────────────────────────

    "EAGER": {"pos": "adjective", "meaning": "wanting to do something very much; enthusiastic and keen", "example": "She was eager to start her new job."},
    "EAGLE": {"pos": "noun", "meaning": "a large powerful bird of prey with keen eyesight", "example": "An eagle soared above the mountain ridge."},
    "EARNS": {"pos": "verb", "meaning": "to receive money in return for work; to deserve by one's actions", "example": "She earns a good salary as an engineer."},
    "EARTH": {"pos": "noun", "meaning": "the planet we live on; soil; the ground", "example": "He pressed his hand into the dark, rich earth."},
    "EASEL": {"pos": "noun", "meaning": "a frame on legs to hold a canvas or display board", "example": "The painter set the canvas on her easel by the window."},
    "EAVES": {"pos": "noun", "meaning": "the lower edges of a roof that overhang the walls", "example": "Swallows built their nests under the eaves."},
    "EBONY": {"pos": "noun", "meaning": "a heavy black wood used for piano keys and decorative objects", "example": "The figurine was carved from polished ebony."},
    "EDICT": {"pos": "noun", "meaning": "an official order or decree issued by an authority", "example": "The emperor issued an edict banning all public gatherings."},
    "EDIFY": {"pos": "verb", "meaning": "to instruct or improve someone morally or intellectually", "example": "The lecture was meant to edify as well as entertain."},
    "EERIE": {"pos": "adjective", "meaning": "strange and frightening; mysteriously unsettling", "example": "An eerie silence fell over the abandoned building."},
    "EGRET": {"pos": "noun", "meaning": "a white wading bird related to the heron", "example": "An egret stood still at the edge of the pond."},
    "EIGHT": {"pos": "noun", "meaning": "the number 8; a group or unit of eight", "example": "She scored eight out of ten on the test."},
    "EJECT": {"pos": "verb", "meaning": "to force or throw out; to be ejected from an aircraft using an ejector seat", "example": "The disc was ejected automatically from the drive."},
    "ELBOW": {"pos": "noun", "meaning": "the joint between the forearm and upper arm; to push with the elbow", "example": "She elbowed her way to the front of the crowd."},
    "ELDER": {"pos": "noun", "meaning": "an older person; a person with authority in a community; a type of shrub", "example": "The village elders settled disputes through mediation."},
    "ELECT": {"pos": "verb", "meaning": "to choose by vote; to select or choose", "example": "She was elected chairwoman by a large majority."},
    "ELEGY": {"pos": "noun", "meaning": "a mournful poem or song, especially one for the dead", "example": "He composed an elegy for his fallen comrades."},
    "ELFIN": {"pos": "adjective", "meaning": "small and delicate; resembling an elf; light and impish", "example": "She had an elfin charm that captivated everyone she met."},
    "ELITE": {"pos": "noun", "meaning": "a select group seen as superior in ability or status", "example": "Only the elite were invited to the private summit."},
    "ELOPE": {"pos": "verb", "meaning": "to run away secretly to get married without parental approval", "example": "They eloped to Las Vegas rather than face a big wedding."},
    "ELUDE": {"pos": "verb", "meaning": "to escape from or avoid by cleverness; to fail to be understood", "example": "The answer continued to elude him."},
    "EMAIL": {"pos": "noun", "meaning": "messages sent electronically; the system for sending them", "example": "She received fifty emails before lunch."},
    "EMBED": {"pos": "verb", "meaning": "to fix firmly in a surrounding mass; to include in a larger structure", "example": "Journalists were embedded with the troops."},
    "EMBER": {"pos": "noun", "meaning": "a piece of glowing coal or wood in a dying fire", "example": "They sat by the embers long after the fire died down."},
    "EMCEE": {"pos": "noun", "meaning": "a master of ceremonies; a host of an event", "example": "The emcee kept the evening flowing with jokes and introductions."},
    "EMOTE": {"pos": "verb", "meaning": "to display exaggerated emotion; to portray emotion dramatically", "example": "The actor tended to emote rather than act naturally."},
    "EMPTY": {"pos": "adjective", "meaning": "containing nothing; without purpose or meaning", "example": "The room was empty when she arrived."},
    "ENACT": {"pos": "verb", "meaning": "to make a bill into law; to put a plan into action; to act out", "example": "Parliament enacted the new legislation within the month."},
    "ENDOW": {"pos": "verb", "meaning": "to give a quality or ability to someone; to provide an institution with income", "example": "She endowed the university with a generous scholarship fund."},
    "ENEMA": {"pos": "noun", "meaning": "a procedure in which liquid is injected into the rectum for medical purposes", "example": "The doctor recommended an enema to relieve the blockage."},
    "ENEMY": {"pos": "noun", "meaning": "a person or group that is hostile or opposed to another", "example": "He kept his enemies closer than his friends."},
    "ENJOY": {"pos": "verb", "meaning": "to take pleasure in; to possess and benefit from something", "example": "She enjoyed every moment of the holiday."},
    "ENNUI": {"pos": "noun", "meaning": "a feeling of listlessness and dissatisfaction arising from boredom", "example": "An overwhelming ennui settled over him by mid-afternoon."},
    "ENSUE": {"pos": "verb", "meaning": "to happen afterwards or as a result", "example": "A heated argument ensued after the announcement."},
    "ENTER": {"pos": "verb", "meaning": "to come into a place; to participate; to record data", "example": "Enter your password to unlock the account."},
    "ENTRY": {"pos": "noun", "meaning": "an act of entering; a piece submitted for a competition; a record in a diary", "example": "Her entry won first prize at the art show."},
    "ENVOY": {"pos": "noun", "meaning": "a messenger or representative, especially in diplomacy", "example": "A special envoy was sent to broker the peace deal."},
    "EPOCH": {"pos": "noun", "meaning": "a long and distinct period of history; a point that begins a new era", "example": "The invention of the internet marked a new epoch."},
    "EPOXY": {"pos": "noun", "meaning": "a strong adhesive made from synthetic resin; used for bonding materials", "example": "She glued the broken handle back with epoxy."},
    "EQUAL": {"pos": "adjective", "meaning": "the same in quantity, size, or value; having the same rights", "example": "All citizens are equal before the law."},
    "EQUIP": {"pos": "verb", "meaning": "to supply with tools or resources needed for a purpose", "example": "The expedition was fully equipped for the climb."},
    "ERASE": {"pos": "verb", "meaning": "to rub out or remove marks; to delete data", "example": "She erased the wrong answer and tried again."},
    "ERECT": {"pos": "verb", "meaning": "to build or put up a structure; to raise upright", "example": "A monument was erected in the town square."},
    "ERGOT": {"pos": "noun", "meaning": "a fungal disease of cereals; a grain-infecting fungus once linked to poisoning", "example": "Outbreaks of ergot poisoning plagued medieval Europe."},
    "ERODE": {"pos": "verb", "meaning": "to gradually wear away by the action of water, wind, or other forces", "example": "Sea cliffs erode faster than most people realize."},
    "ERROR": {"pos": "noun", "meaning": "a mistake; a state of being wrong; a deviation from accuracy", "example": "The final report contained several critical errors."},
    "ERUPT": {"pos": "verb", "meaning": "to burst out suddenly; to explode violently, as a volcano does", "example": "The volcano erupted without warning."},
    "ESSAY": {"pos": "noun", "meaning": "a short piece of writing on a particular subject", "example": "She wrote a compelling essay on climate justice."},
    "ETHER": {"pos": "noun", "meaning": "a highly flammable liquid once used as an anesthetic; the upper air", "example": "The idea seemed to dissolve into the ether."},
    "ETHIC": {"pos": "noun", "meaning": "a set of moral principles; a system of values guiding behavior", "example": "A strong work ethic was instilled in her from childhood."},
    "ETHOS": {"pos": "noun", "meaning": "the characteristic spirit and values of a community or culture", "example": "The company ethos centered on innovation and respect."},
    "ETUDE": {"pos": "noun", "meaning": "a short musical composition designed to develop a technique", "example": "She practiced Chopin's étude until her fingers ached."},
    "EVADE": {"pos": "verb", "meaning": "to escape or avoid by cleverness; to fail to address honestly", "example": "He evaded every direct question with skill."},
    "EVENT": {"pos": "noun", "meaning": "a thing that happens; a planned public occasion; a sports competition", "example": "The charity event raised over a million dollars."},
    "EVICT": {"pos": "verb", "meaning": "to expel a tenant from a property through legal process", "example": "The landlord moved to evict the tenant for non-payment."},
    "EVOKE": {"pos": "verb", "meaning": "to bring a feeling or memory to mind; to summon", "example": "The music evoked memories of her childhood."},
    "EXACT": {"pos": "adjective", "meaning": "perfectly accurate; precise; not approximate", "example": "Please give me the exact time the meeting starts."},
    "EXALT": {"pos": "verb", "meaning": "to praise highly; to raise in rank or status", "example": "The crowd exalted the returning champion."},
    "EXCEL": {"pos": "verb", "meaning": "to be exceptionally good at something; to surpass others", "example": "She excelled at mathematics from an early age."},
    "EXERT": {"pos": "verb", "meaning": "to apply or bring to bear; to make a strenuous effort", "example": "You'll need to exert pressure on the lever."},
    "EXILE": {"pos": "noun", "meaning": "the state of being barred from one's home country; a person so banished", "example": "The dissident lived in exile for twenty years."},
    "EXIST": {"pos": "verb", "meaning": "to have real being; to live or continue; to be present", "example": "Did dinosaurs and humans ever exist at the same time?"},
    "EXPEL": {"pos": "verb", "meaning": "to force someone to leave a school or organization officially", "example": "Three students were expelled for cheating."},
    "EXTOL": {"pos": "verb", "meaning": "to praise enthusiastically; to glorify", "example": "Every review extolled the restaurant's creative menu."},
    "EXTRA": {"pos": "adjective", "meaning": "added to an existing amount; beyond what is usual", "example": "She added extra cheese to her order."},
    "EXUDE": {"pos": "verb", "meaning": "to ooze or discharge; to display a quality strongly", "example": "He exuded confidence in every situation."},
    "EXULT": {"pos": "verb", "meaning": "to feel or show triumphant elation", "example": "The crowd exulted as the winner crossed the line."},

    # ── F ──────────────────────────────────────────────────────────────────

    "FABLE": {"pos": "noun", "meaning": "a short story with animals as characters that teaches a moral lesson", "example": "Aesop's fables have been read for thousands of years."},
    "FACET": {"pos": "noun", "meaning": "one side of a cut gemstone; a particular aspect of something", "example": "Every facet of the problem needed examination."},
    "FAGOT": {"pos": "noun", "meaning": "a bundle of sticks or twigs bound together as fuel", "example": "A fagot of birch wood was stacked beside the fireplace."},
    "FAINT": {"pos": "adjective", "meaning": "barely perceptible; lacking strength; to briefly lose consciousness", "example": "She fainted in the heat of the crowded stadium."},
    "FAIRY": {"pos": "noun", "meaning": "a small imaginary being with magical powers; a supernatural creature", "example": "The fairy tales she loved as a child still delighted her."},
    "FAITH": {"pos": "noun", "meaning": "complete trust or confidence; belief in a religion without proof", "example": "She kept the faith through years of hardship."},
    "FAKER": {"pos": "noun", "meaning": "a person who fakes things; one who pretends to be something they are not", "example": "Everyone could tell he was a faker within five minutes."},
    "FAKIR": {"pos": "noun", "meaning": "a Muslim or Hindu religious ascetic who lives on alms", "example": "A fakir sat motionless in meditation at the roadside."},
    "FALSE": {"pos": "adjective", "meaning": "not true or correct; fake or artificial; disloyal", "example": "The alarm turned out to be a false alert."},
    "FANCY": {"pos": "adjective", "meaning": "elaborate or decorative; to feel attracted to; a liking or desire", "example": "They booked a table at a fancy restaurant for the anniversary."},
    "FANGS": {"pos": "noun", "meaning": "long pointed teeth of an animal or snake; something resembling these", "example": "The cobra bared its fangs."},
    "FARCE": {"pos": "noun", "meaning": "a comic play with unlikely situations; an absurd event", "example": "The hearing descended into complete farce."},
    "FATAL": {"pos": "adjective", "meaning": "causing death; leading to disaster; decisively important", "example": "A fatal error in the code brought down the whole server."},
    "FATWA": {"pos": "noun", "meaning": "a ruling on Islamic law issued by a religious authority", "example": "A fatwa was issued against the publication."},
    "FAULT": {"pos": "noun", "meaning": "a defect or mistake; responsibility for an accident; a crack in rock", "example": "The earthquake occurred along a deep geological fault."},
    "FAUNA": {"pos": "noun", "meaning": "the animals of a particular region or period", "example": "The island's fauna includes species found nowhere else."},
    "FAVOR": {"pos": "noun", "meaning": "an act of kindness; approval or support; a small gift at a party", "example": "She asked a favor and he was happy to help."},
    "FEAST": {"pos": "noun", "meaning": "a large and elaborate meal; a religious festival; to eat heartily", "example": "The harvest feast lasted late into the night."},
    "FEIGN": {"pos": "verb", "meaning": "to pretend to feel or be affected by something", "example": "She feigned surprise when she already knew the result."},
    "FEINT": {"pos": "noun", "meaning": "a deceptive movement intended to distract; a mock attack", "example": "He made a feint to the left then went right."},
    "FELON": {"pos": "noun", "meaning": "a person who has committed a serious crime", "example": "As a convicted felon, he lost his right to vote."},
    "FEMUR": {"pos": "noun", "meaning": "the thigh bone; the longest bone in the human body", "example": "She fractured her femur in the fall."},
    "FENCE": {"pos": "noun", "meaning": "a barrier enclosing an area; to sell stolen goods; to spar with foils", "example": "The horses grazed inside the white fence."},
    "FERAL": {"pos": "adjective", "meaning": "in a wild state, especially after domestication; savage", "example": "A colony of feral cats lived behind the restaurant."},
    "FERRY": {"pos": "noun", "meaning": "a boat for transporting passengers and vehicles across water", "example": "They took the ferry across the sound."},
    "FEVER": {"pos": "noun", "meaning": "an abnormally high body temperature; intense excitement or agitation", "example": "The child ran a high fever throughout the night."},
    "FIBER": {"pos": "noun", "meaning": "a thread-like structure; dietary material from plants; moral strength", "example": "A diet rich in fiber is good for digestion."},
    "FIELD": {"pos": "noun", "meaning": "an open area of land; a subject of study; to deal with questions", "example": "She worked in the field of quantum computing."},
    "FIEND": {"pos": "noun", "meaning": "an evil spirit; a very wicked person; an enthusiast (informal)", "example": "He was a crossword fiend who never missed a puzzle."},
    "FIERY": {"pos": "adjective", "meaning": "consisting of fire; intensely passionate or hot-tempered", "example": "She had a fiery personality that commanded attention."},
    "FIFTH": {"pos": "noun", "meaning": "the ordinal form of five; one of five equal parts", "example": "He finished fifth in the race."},
    "FIFTY": {"pos": "noun", "meaning": "the number 50; a fifty-dollar or fifty-pound note", "example": "She paid with a crisp fifty."},
    "FIGHT": {"pos": "verb", "meaning": "to engage in combat; to struggle against; to argue", "example": "He was willing to fight for what he believed in."},
    "FILCH": {"pos": "verb", "meaning": "to steal something of small value in a sneaky way", "example": "He filched a cookie when no one was looking."},
    "FILET": {"pos": "noun", "meaning": "a boneless piece of meat or fish; a narrow ribbon or band", "example": "She ordered the salmon filet with vegetables."},
    "FILTH": {"pos": "noun", "meaning": "disgusting dirt; obscene language or content", "example": "The flat was in a state of absolute filth."},
    "FINAL": {"pos": "adjective", "meaning": "coming at the end; decisive; not subject to further change", "example": "The final decision rests with the committee."},
    "FINCH": {"pos": "noun", "meaning": "a small songbird with a short conical bill, such as a chaffinch or goldfinch", "example": "A goldfinch perched on the feeder."},
    "FIRED": {"pos": "verb", "meaning": "dismissed from employment; ignited; launched a projectile", "example": "She was fired for repeatedly missing deadlines."},
    "FIRST": {"pos": "adjective", "meaning": "coming before all others in order, time, or importance", "example": "He was the first to arrive at the meeting."},
    "FISHY": {"pos": "adjective", "meaning": "relating to fish; arousing doubt or suspicion (informal)", "example": "Something about his explanation seemed a bit fishy."},
    "FIXED": {"pos": "adjective", "meaning": "fastened securely; settled and not changing; predetermined dishonestly", "example": "The match was reportedly fixed before it even started."},
    "FIZZY": {"pos": "adjective", "meaning": "containing many bubbles of gas; effervescent", "example": "She ordered a fizzy water with her lunch."},
    "FJORD": {"pos": "noun", "meaning": "a long narrow inlet of the sea between steep cliffs, as in Norway", "example": "The cruise ship sailed slowly through the fjord."},
    "FLAIL": {"pos": "verb", "meaning": "to wave or swing erratically; to struggle without direction", "example": "He flailed about trying to find a solution."},
    "FLAIR": {"pos": "noun", "meaning": "a natural talent or aptitude; distinctive elegance of style", "example": "She had a flair for languages and spoke six fluently."},
    "FLAKE": {"pos": "noun", "meaning": "a small flat thin piece; to come off in flakes; an unreliable person", "example": "Snowflakes fell thick and fast."},
    "FLAKY": {"pos": "adjective", "meaning": "tending to crumble into flakes; unreliable (informal)", "example": "The pastry was deliciously flaky."},
    "FLAME": {"pos": "noun", "meaning": "a portion of burning gas; a passionate emotion; an old lover", "example": "An old flame appeared at the reunion."},
    "FLANK": {"pos": "noun", "meaning": "the side of a person or animal; the side of an army formation", "example": "The cavalry attacked the enemy's left flank."},
    "FLARE": {"pos": "noun", "meaning": "a sudden brief burst of flame; a signal light; to widen outward", "example": "She fired a flare to signal the rescue team."},
    "FLASH": {"pos": "noun", "meaning": "a sudden burst of light; a brief moment; to move very fast", "example": "The lightning flash lit up the whole sky."},
    "FLASK": {"pos": "noun", "meaning": "a container with a narrow neck for liquids; a pocket-sized container for spirits", "example": "He carried a silver flask of whisky in his coat pocket."},
    "FLEET": {"pos": "noun", "meaning": "a group of ships or vehicles; swift and agile", "example": "The fishing fleet set out before dawn."},
    "FLESH": {"pos": "noun", "meaning": "the soft substance of a body; the physical aspects of human nature", "example": "The wound was deep but hadn't reached flesh."},
    "FLICK": {"pos": "verb", "meaning": "to move with a quick light snap; to flip through pages", "example": "She flicked through the magazine impatiently."},
    "FLING": {"pos": "noun", "meaning": "a short period of wild behaviour; a brief romantic relationship", "example": "They had a summer fling before going their separate ways."},
    "FLINT": {"pos": "noun", "meaning": "a hard grey rock used to produce sparks; a piece of flint for a lighter", "example": "Early humans used flint to make tools and start fires."},
    "FLIRT": {"pos": "verb", "meaning": "to behave as though sexually attracted to someone; to trifle with", "example": "She flirted with the idea of moving abroad."},
    "FLOAT": {"pos": "verb", "meaning": "to rest on the surface of a liquid; to move gently through air", "example": "The raft floated lazily down the river."},
    "FLOCK": {"pos": "noun", "meaning": "a group of birds or sheep; a crowd of people; to gather in numbers", "example": "Tourists flocked to the beach in summer."},
    "FLOOD": {"pos": "noun", "meaning": "an overflow of water onto normally dry land; a large quantity", "example": "The flood left the village under three feet of water."},
    "FLOOR": {"pos": "noun", "meaning": "the lower surface of a room; a level of a building; to knock down", "example": "The question floored him completely."},
    "FLORA": {"pos": "noun", "meaning": "the plants of a particular region or period; gut bacteria", "example": "The island's flora included rare endemic orchids."},
    "FLOSS": {"pos": "noun", "meaning": "soft thread for cleaning between teeth; thin silk thread; to use dental floss", "example": "She flossed every evening without fail."},
    "FLOUR": {"pos": "noun", "meaning": "a fine powder made by grinding grain, used for baking", "example": "She sifted the flour before mixing it into the batter."},
    "FLOUT": {"pos": "verb", "meaning": "to openly disregard a rule or convention", "example": "He flouted the dress code by wearing jeans."},
    "FLUFF": {"pos": "noun", "meaning": "soft fibres or particles; light trivial material; to make an error (informal)", "example": "She fluffed her lines on opening night."},
    "FLUID": {"pos": "noun", "meaning": "a substance that flows; not fixed or stable", "example": "Drink plenty of fluid when you have a fever."},
    "FLUKE": {"pos": "noun", "meaning": "a lucky chance event; a stroke of good fortune", "example": "His first goal was a fluke—the second was pure skill."},
    "FLUME": {"pos": "noun", "meaning": "an artificial channel for water; a water slide at a theme park", "example": "They screamed all the way down the flume."},
    "FLUNK": {"pos": "verb", "meaning": "to fail an exam or course; to give a failing grade", "example": "He flunked chemistry and had to repeat the year."},
    "FLUSH": {"pos": "adjective", "meaning": "level with a surface; having plenty of money; to cleanse with water", "example": "Flush with excitement, she ran to share the news."},
    "FLUTE": {"pos": "noun", "meaning": "a woodwind instrument played by blowing across a hole; a tall wine glass", "example": "She raised her champagne flute for the toast."},
    "FLYER": {"pos": "noun", "meaning": "a printed advertisement; a person who flies; a bold and risky move", "example": "They distributed flyers around the neighbourhood."},
    "FOCAL": {"pos": "adjective", "meaning": "relating to the centre of interest; relating to a focus", "example": "The painting was the focal point of the room."},
    "FOCUS": {"pos": "noun", "meaning": "the centre of interest or activity; clarity of an image; to concentrate", "example": "She couldn't focus with so much noise around her."},
    "FOGGY": {"pos": "adjective", "meaning": "full of fog; vague or confused in the mind", "example": "I haven't the foggiest idea what you mean."},
    "FOLLY": {"pos": "noun", "meaning": "a lack of good judgment; a costly undertaking with little purpose", "example": "Building the bridge there was considered sheer folly."},
    "FORCE": {"pos": "noun", "meaning": "strength or energy; an influence causing change; to compel", "example": "The force of the wind knocked her off balance."},
    "FORGE": {"pos": "verb", "meaning": "to make a copy of something fraudulently; to create metal with heat; to advance", "example": "The team forged ahead despite the setbacks."},
    "FORGO": {"pos": "verb", "meaning": "to go without; to abstain from; to relinquish", "example": "She decided to forgo dessert and have coffee instead."},
    "FORTE": {"pos": "noun", "meaning": "a thing at which someone excels; loudly in music (Italian)", "example": "Public speaking was never his forte."},
    "FORTH": {"pos": "adverb", "meaning": "forward or onward in place or time; out into the open", "example": "He set forth on his journey at first light."},
    "FORTY": {"pos": "noun", "meaning": "the number 40; between thirty-nine and forty-one", "example": "She celebrated her fortieth birthday with a party."},
    "FORUM": {"pos": "noun", "meaning": "a place for public debate; an online discussion board", "example": "The town hall served as a forum for community issues."},
    "FOYER": {"pos": "noun", "meaning": "the entrance hall of a building; a lobby", "example": "They met in the hotel foyer before heading to dinner."},
    "FRAIL": {"pos": "adjective", "meaning": "physically weak; easily damaged or broken", "example": "He looked frail after months in hospital."},
    "FRAME": {"pos": "noun", "meaning": "a rigid structure surrounding a picture or window; the human body's structure", "example": "She chose a simple silver frame for the photograph."},
    "FRANK": {"pos": "adjective", "meaning": "direct and honest, even if offensive; to stamp a letter free of charge", "example": "She gave a frank assessment of his weaknesses."},
    "FRAUD": {"pos": "noun", "meaning": "criminal deception intended to result in financial gain; an impostor", "example": "He was convicted of bank fraud."},
    "FREAK": {"pos": "noun", "meaning": "a person or animal that is abnormal; a very unusual event; an enthusiast", "example": "She was a complete fitness freak."},
    "FRESH": {"pos": "adjective", "meaning": "recently made or obtained; not stale; new and different", "example": "The bread was baked fresh that morning."},
    "FRIAR": {"pos": "noun", "meaning": "a member of a male mendicant religious order", "example": "Friar Tuck was Robin Hood's portly companion."},
    "FRILL": {"pos": "noun", "meaning": "a strip of gathered fabric on a garment; an extra unnecessary feature", "example": "The basic room had no frills but was clean and comfortable."},
    "FRISK": {"pos": "verb", "meaning": "to pat someone down for concealed weapons; to move energetically", "example": "Security staff frisked all guests at the entrance."},
    "FROCK": {"pos": "noun", "meaning": "a woman's or girl's dress; a monk's habit", "example": "She wore a floral frock to the garden party."},
    "FROND": {"pos": "noun", "meaning": "a large divided leaf of a fern or palm", "example": "Palm fronds cast dappled shade on the path."},
    "FRONT": {"pos": "noun", "meaning": "the part facing forward; the foremost position; a line of battle; a facade", "example": "The shop's polished front hid a chaotic back room."},
    "FROST": {"pos": "noun", "meaning": "frozen water vapour covering surfaces; very cold weather", "example": "A hard frost had coated the grass white overnight."},
    "FROTH": {"pos": "noun", "meaning": "a mass of small bubbles; empty or trivial talk", "example": "The cappuccino was topped with thick froth."},
    "FROWN": {"pos": "verb", "meaning": "to knit the brows in displeasure or concentration; a scowl", "example": "She frowned at the unexpected bill."},
    "FROZE": {"pos": "verb", "meaning": "past tense of freeze; became solid through cold; stopped moving", "example": "The lake froze overnight in the bitter cold."},
    "FRUIT": {"pos": "noun", "meaning": "the edible produce of a plant; the result of effort", "example": "The garden produced fruit throughout summer."},
    "FUDGE": {"pos": "noun", "meaning": "a soft sweet made from sugar and butter; to present dishonestly", "example": "He fudged the figures in the report."},
    "FUGUE": {"pos": "noun", "meaning": "a polyphonic musical composition; a state of amnesia with wandering", "example": "Bach was a master of the fugue."},
    "FUNGI": {"pos": "noun", "meaning": "plural of fungus; organisms including mushrooms, moulds, and yeasts", "example": "Fungi play a vital role in decomposing organic matter."},
    "FUNKY": {"pos": "adjective", "meaning": "having a strong rhythmic quality; unconventionally stylish; musty", "example": "The venue had a funky vibe with mismatched furniture."},
    "FUNNY": {"pos": "adjective", "meaning": "causing laughter; strange or suspicious", "example": "The comedian told a very funny story about his dog."},
    "FUROR": {"pos": "noun", "meaning": "an outburst of public anger or excitement", "example": "The decision caused a furor among residents."},
    "FURRY": {"pos": "adjective", "meaning": "covered with fur; resembling or made of fur", "example": "She tucked the furry kitten under her chin."},
    "FUSSY": {"pos": "adjective", "meaning": "hard to please; excessively particular; overly detailed", "example": "He was fussy about how his coffee was prepared."},
    "FUSTY": {"pos": "adjective", "meaning": "smelling stale and musty; old-fashioned and outdated", "example": "The library had a fusty smell of old books."},
    "FUTON": {"pos": "noun", "meaning": "a low wooden bed frame with a thin mattress; a sofa that folds flat", "example": "Guests slept on the futon in the spare room."},
    "FUZZY": {"pos": "adjective", "meaning": "having a frizzy texture; unclear or indistinct; not sharp", "example": "The old photograph was fuzzy and hard to make out."},

    # ── G ──────────────────────────────────────────────────────────────────

    "GABLE": {"pos": "noun", "meaning": "the triangular upper portion of a wall at the end of a ridged roof", "example": "A weathervane sat atop the house's front gable."},
    "GAFFE": {"pos": "noun", "meaning": "an embarrassing blunder or social mistake", "example": "His gaffe at the dinner party was the talk of the office."},
    "GAILY": {"pos": "adverb", "meaning": "in a cheerful and lighthearted way; with bright colors", "example": "The village was gaily decorated for the festival."},
    "GAMUT": {"pos": "noun", "meaning": "the complete range or scope of something", "example": "Her performance ran the full gamut of emotions."},
    "GAUDY": {"pos": "adjective", "meaning": "extravagantly bright or showy; tastelessly ornate", "example": "The casino's gaudy neon signs glowed all night."},
    "GAUGE": {"pos": "noun", "meaning": "an instrument for measuring; a standard measure; to estimate", "example": "The fuel gauge showed the tank was nearly empty."},
    "GAUNT": {"pos": "adjective", "meaning": "lean and haggard, especially through illness; grim and desolate", "example": "He returned from the ordeal looking gaunt and pale."},
    "GAUZE": {"pos": "noun", "meaning": "a thin transparent fabric; light open-weave material used medically", "example": "The nurse wrapped the wound in clean gauze."},
    "GAVEL": {"pos": "noun", "meaning": "a small mallet used by a judge or auctioneer to call order", "example": "The judge brought down the gavel to end the session."},
    "GAWKY": {"pos": "adjective", "meaning": "nervously awkward and ungainly; lacking grace or ease", "example": "He was gawky as a teenager but grew into himself."},
    "GECKO": {"pos": "noun", "meaning": "a small tropical lizard with adhesive toe pads enabling it to climb walls", "example": "A gecko darted across the ceiling of the hotel room."},
    "GEEKS": {"pos": "noun", "meaning": "people intensely focused on a particular hobby or technology", "example": "A team of geeks built the app over one weekend."},
    "GEESE": {"pos": "noun", "meaning": "plural of goose; large waterbirds related to swans and ducks", "example": "A gaggle of geese waddled across the village green."},
    "GENES": {"pos": "noun", "meaning": "the basic units of heredity found in DNA; inherited characteristics", "example": "Scientists mapped the genes responsible for the trait."},
    "GENIE": {"pos": "noun", "meaning": "a spirit in folklore able to grant wishes when summoned", "example": "She rubbed the lamp hoping to release a genie."},
    "GENRE": {"pos": "noun", "meaning": "a style or category of art, music, or writing", "example": "She preferred crime fiction above any other genre."},
    "GEODE": {"pos": "noun", "meaning": "a rock with a hollow interior lined with crystals", "example": "The geode cracked open to reveal sparkling amethyst inside."},
    "GERMS": {"pos": "noun", "meaning": "microorganisms that can cause disease; bacteria or viruses", "example": "Wash your hands to stop the spread of germs."},
    "GHOST": {"pos": "noun", "meaning": "the spirit of a dead person; a faint trace; to write for another person", "example": "She claimed to have seen a ghost in the old corridor."},
    "GHOUL": {"pos": "noun", "meaning": "an evil spirit that robs graves; a person morbidly interested in death", "example": "Every horror film seemed to feature a ghoul or two."},
    "GIANT": {"pos": "noun", "meaning": "a huge imaginary being; a very large or important person or organization", "example": "The tech giant launched its new product to global fanfare."},
    "GIDDY": {"pos": "adjective", "meaning": "having a sensation of whirling; excitedly frivolous", "example": "She felt giddy with excitement before the trip."},
    "GIFTS": {"pos": "noun", "meaning": "things given freely; natural talents or abilities", "example": "He unwrapped his birthday gifts slowly."},
    "GIRTH": {"pos": "noun", "meaning": "the measurement around the middle; a band around a horse's belly", "example": "The tree's girth required four people to encircle it."},
    "GIVEN": {"pos": "adjective", "meaning": "specified; assumed as a basis; inclined to", "example": "Given the circumstances, she made the best possible choice."},
    "GIZMO": {"pos": "noun", "meaning": "a gadget or device, especially one whose name is not known", "example": "He pulled a curious gizmo from his toolkit."},
    "GLADE": {"pos": "noun", "meaning": "an open space in a forest; a clearing", "example": "Sunlight flooded the forest glade."},
    "GLAND": {"pos": "noun", "meaning": "an organ that secretes particular chemical substances in the body", "example": "An overactive thyroid gland can disrupt metabolism."},
    "GLARE": {"pos": "noun", "meaning": "a fierce or angry stare; a strong and dazzling light", "example": "The glare of the sun off the water was blinding."},
    "GLASS": {"pos": "noun", "meaning": "a hard transparent material; a drinking vessel made from it", "example": "She raised her glass in a toast."},
    "GLAZE": {"pos": "verb", "meaning": "to fit glass in a window; to cover food with a glassy coating; to lose brightness", "example": "His eyes glazed over during the long lecture."},
    "GLEAM": {"pos": "verb", "meaning": "to shine with a subdued light; to be apparent faintly", "example": "A gleam of hope appeared in the darkness."},
    "GLEAN": {"pos": "verb", "meaning": "to gather gradually bit by bit; to pick up leftover grain after harvesting", "example": "She gleaned useful information from the conversation."},
    "GLIDE": {"pos": "verb", "meaning": "to move smoothly and effortlessly; to fly without engine power", "example": "The swan glided silently across the lake."},
    "GLINT": {"pos": "noun", "meaning": "a small flash of light reflected from a surface", "example": "There was a mischievous glint in her eye."},
    "GLITZ": {"pos": "noun", "meaning": "extravagant but superficial glamour and showiness", "example": "Hollywood is built on glitz and illusion."},
    "GLOAT": {"pos": "verb", "meaning": "to contemplate one's own success with smug satisfaction", "example": "He couldn't help gloating after winning the bet."},
    "GLOBE": {"pos": "noun", "meaning": "a spherical model of the Earth; the Earth itself", "example": "She spun the globe and pointed to where she wanted to travel."},
    "GLOOM": {"pos": "noun", "meaning": "darkness or partial darkness; a feeling of depression or despondency", "example": "A mood of gloom settled over the office after the announcement."},
    "GLORY": {"pos": "noun", "meaning": "high renown or honor; magnificence; a state of extreme beauty", "example": "The team basked in the glory of their victory."},
    "GLOSS": {"pos": "noun", "meaning": "a shine on a smooth surface; superficial attractiveness; to gloss over", "example": "The report glossed over the more troubling findings."},
    "GLOVE": {"pos": "noun", "meaning": "a covering for the hand with separate divisions for fingers", "example": "She pulled on her leather gloves before heading outside."},
    "GLYPH": {"pos": "noun", "meaning": "a hieroglyphic symbol; a carved figure or character", "example": "Each glyph on the stone tablet had a distinct meaning."},
    "GNASH": {"pos": "verb", "meaning": "to grind the teeth together in anger or pain", "example": "He gnashed his teeth in frustration."},
    "GNOME": {"pos": "noun", "meaning": "a small mythical creature living underground; a garden ornament", "example": "A ceramic gnome sat beside the garden pond."},
    "GOLEM": {"pos": "noun", "meaning": "a clay figure magically given life in Jewish folklore; a mindless creature", "example": "In the legend, the rabbi created a golem to protect the community."},
    "GOOSE": {"pos": "noun", "meaning": "a large waterfowl; to poke someone from behind; to boost suddenly", "example": "The goose honked and chased the children away."},
    "GORGE": {"pos": "noun", "meaning": "a narrow valley with steep rocky walls; to eat greedily", "example": "They hiked through the gorge carved by the river."},
    "GOUGE": {"pos": "verb", "meaning": "to make a groove or hole; to scoop out; to charge an unfairly high price", "example": "The landlord was accused of gouging tenants on rent."},
    "GOURD": {"pos": "noun", "meaning": "a hard-skinned fruit of a climbing plant; a vessel made from its dried shell", "example": "They scooped water from the river using a dried gourd."},
    "GOWNS": {"pos": "noun", "meaning": "long dresses; loose robes worn by graduates, judges, or hospital patients", "example": "The graduates wore black gowns at the ceremony."},
    "GRACE": {"pos": "noun", "meaning": "elegance and beauty of movement; a prayer before a meal; divine favor", "example": "She moved with the grace of a trained dancer."},
    "GRADE": {"pos": "noun", "meaning": "a mark given for work; a level of quality; a slope", "example": "She got top grades in her final exams."},
    "GRAFT": {"pos": "noun", "meaning": "hard work (informal); a piece of transplanted tissue; corruption", "example": "Success came through years of honest graft."},
    "GRAIL": {"pos": "noun", "meaning": "something that is sought as the ultimate prize; the Holy Grail of legend", "example": "Fast fusion energy remains the grail of modern physics."},
    "GRAIN": {"pos": "noun", "meaning": "a seed of a cereal plant; a small hard particle; the texture of wood", "example": "The loaf was made from stone-ground whole grain."},
    "GRAND": {"pos": "adjective", "meaning": "magnificent; impressively large; a thousand pounds or dollars (informal)", "example": "The grand ballroom gleamed under the chandeliers."},
    "GRANT": {"pos": "verb", "meaning": "to give formally; to agree to fulfill; a sum of money given for a purpose", "example": "The university granted her a research scholarship."},
    "GRAPE": {"pos": "noun", "meaning": "a small round fruit growing in clusters, used for wine and eating", "example": "She plucked a grape from the bunch."},
    "GRAPH": {"pos": "noun", "meaning": "a diagram showing the relationship between values; to plot on a chart", "example": "The graph showed a steady rise in temperatures."},
    "GRASP": {"pos": "verb", "meaning": "to seize and hold firmly; to understand fully", "example": "It took a moment to grasp what she was saying."},
    "GRASS": {"pos": "noun", "meaning": "a low green plant covering lawns and fields; marijuana (informal)", "example": "They sat on the grass and watched the sunset."},
    "GRATE": {"pos": "verb", "meaning": "to shred food by rubbing against a grater; to make an irritating noise", "example": "His constant interruptions grated on her nerves."},
    "GRAVE": {"pos": "noun", "meaning": "a hole dug for burying a body; serious and concerning", "example": "The doctor's expression told her the news was grave."},
    "GRAVY": {"pos": "noun", "meaning": "a sauce made from meat juices; an unexpected bonus (informal)", "example": "She poured thick gravy over the roast potatoes."},
    "GRAZE": {"pos": "verb", "meaning": "to feed on grass; to touch or scrape lightly in passing", "example": "The bullet grazed his arm but didn't penetrate."},
    "GREAT": {"pos": "adjective", "meaning": "of an extent or intensity considerably above average; important; excellent", "example": "He had a great passion for classical music."},
    "GREBE": {"pos": "noun", "meaning": "a diving waterbird with a long neck and colourful markings", "example": "A great crested grebe fished in the centre of the lake."},
    "GREED": {"pos": "noun", "meaning": "intense and selfish desire for wealth, food, or power", "example": "Greed led him to ignore the risks of the scheme."},
    "GREEN": {"pos": "adjective", "meaning": "of the color between blue and yellow; relating to the environment; inexperienced", "example": "She was still green but showed enormous promise."},
    "GREET": {"pos": "verb", "meaning": "to give a word or sign of welcome; to react to in a specified way", "example": "She greeted every guest warmly at the door."},
    "GRIEF": {"pos": "noun", "meaning": "deep sorrow, especially following a death; trouble (informal)", "example": "She was still processing her grief months after the loss."},
    "GRIFT": {"pos": "noun", "meaning": "a petty swindle or fraud; money obtained by swindling", "example": "He ran small grifts until caught by the police."},
    "GRILL": {"pos": "noun", "meaning": "a device for cooking food over a direct heat; to interrogate closely", "example": "The detective grilled the suspect for two hours."},
    "GRIME": {"pos": "noun", "meaning": "dirt ingrained on a surface; filth accumulated over time", "example": "Years of grime coated the factory windows."},
    "GRIND": {"pos": "verb", "meaning": "to reduce to small particles by crushing; to work hard tediously", "example": "She ground the coffee beans fresh every morning."},
    "GROAN": {"pos": "verb", "meaning": "to make a deep sound of pain or despair; to creak under strain", "example": "He groaned when he saw the repair bill."},
    "GROIN": {"pos": "noun", "meaning": "the area at the junction of the thigh and the abdomen", "example": "He pulled a muscle in his groin during the sprint."},
    "GROOM": {"pos": "verb", "meaning": "to clean and maintain; to prepare someone for a role; a bridegroom", "example": "The stable hand groomed the horse carefully."},
    "GROPE": {"pos": "verb", "meaning": "to feel about with the hands; to search blindly; to touch inappropriately", "example": "She groped for the light switch in the dark."},
    "GROSS": {"pos": "adjective", "meaning": "disgustingly unpleasant; total before deductions; a dozen dozens (144)", "example": "The company's gross profit exceeded expectations."},
    "GROUP": {"pos": "noun", "meaning": "a number of people or things together; to classify together", "example": "A small group gathered in the corner to discuss the news."},
    "GROUT": {"pos": "noun", "meaning": "a mortar used to fill joints between tiles; to apply grout", "example": "He regrouted the bathroom tiles over the weekend."},
    "GROVE": {"pos": "noun", "meaning": "a small group of trees; an orchard", "example": "They picnicked in a shady grove of silver birches."},
    "GROWL": {"pos": "verb", "meaning": "to make a low guttural sound of hostility; to speak angrily", "example": "The dog growled at the stranger at the gate."},
    "GRUEL": {"pos": "noun", "meaning": "a thin liquid food of oatmeal boiled in water; meagre fare", "example": "The orphans were given nothing but thin gruel."},
    "GRUFF": {"pos": "adjective", "meaning": "abrupt or surly in manner; rough and low in voice", "example": "He had a gruff manner but a kind heart."},
    "GRUMP": {"pos": "noun", "meaning": "a grumpy person; a fit of sulking", "example": "Don't mind him—he's a grump before his coffee."},
    "GRUNT": {"pos": "verb", "meaning": "to make a low inarticulate sound; to say something with a grunt", "example": "He grunted a reply without looking up from his book."},
    "GUANO": {"pos": "noun", "meaning": "the excrement of seabirds or bats, used as fertilizer", "example": "Guano was once one of Peru's most valuable exports."},
    "GUARD": {"pos": "noun", "meaning": "a person who protects or keeps watch; a protective device", "example": "A guard was posted at the entrance around the clock."},
    "GUAVA": {"pos": "noun", "meaning": "a tropical fruit with pink flesh and a sweet aromatic flavor", "example": "She blended guava and lime for a fresh smoothie."},
    "GUESS": {"pos": "verb", "meaning": "to estimate without definite knowledge; to suppose correctly", "example": "Can you guess what's inside?"},
    "GUEST": {"pos": "noun", "meaning": "a person invited to visit or stay; someone staying at a hotel", "example": "The hotel welcomed its ten-thousandth guest with flowers."},
    "GUIDE": {"pos": "noun", "meaning": "a person who shows the way; a book of information; to lead or direct", "example": "The mountain guide knew every safe route."},
    "GUILD": {"pos": "noun", "meaning": "a medieval association of craftsmen or merchants; a professional association", "example": "The writers' guild negotiated better pay for its members."},
    "GUILE": {"pos": "noun", "meaning": "cunning intelligence; deceitful cleverness", "example": "He used guile rather than force to win the negotiation."},
    "GUILT": {"pos": "noun", "meaning": "the fact of having committed an offence; a feeling of responsibility for wrongdoing", "example": "The guilt ate at him for years."},
    "GUISE": {"pos": "noun", "meaning": "an outward form or appearance; a false appearance assumed to deceive", "example": "The spy operated under the guise of a journalist."},
    "GULAG": {"pos": "noun", "meaning": "a Soviet forced labor camp; any brutal prison system", "example": "Millions perished in the gulags of Siberia."},
    "GULCH": {"pos": "noun", "meaning": "a narrow and steep-sided ravine, especially one carved by water", "example": "The trail wound down into the gulch below."},
    "GULLY": {"pos": "noun", "meaning": "a channel or ravine cut by running water; a fielding position in cricket", "example": "Rainwater rushed through the gully."},
    "GUMBO": {"pos": "noun", "meaning": "a spicy stew from Louisiana made with meat or seafood and okra", "example": "She ladled shrimp gumbo over steamed rice."},
    "GUPPY": {"pos": "noun", "meaning": "a small tropical freshwater fish popular in home aquariums", "example": "She kept a tank of guppies on her windowsill."},
    "GURUS": {"pos": "noun", "meaning": "spiritual teachers; influential figures or experts in a field", "example": "Silicon Valley gurus predicted the company's rise."},
    "GUSTO": {"pos": "noun", "meaning": "enthusiasm and energy in doing something", "example": "She attacked the project with tremendous gusto."},
    "GUTSY": {"pos": "adjective", "meaning": "showing courage and determination; brave and spirited", "example": "It was a gutsy call to take on such a powerful opponent."},
    "GYPSY": {"pos": "noun", "meaning": "a member of a nomadic people; a person with an unconventional wandering lifestyle", "example": "She lived like a gypsy, moving from city to city."},
    "GYROS": {"pos": "noun", "meaning": "Greek sandwiches of meat cooked on a spit, wrapped in pita with toppings", "example": "They grabbed gyros from a street stall after the concert."},
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
        csv_path = _WORDS_FILE.parent / "definitions_dg.csv"
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
    parser = argparse.ArgumentParser(description="Seed word definitions for D–G words")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing definitions")
    parser.add_argument("--csv", action="store_true", help="Also write a CSV backup file")
    args = parser.parse_args()
    asyncio.run(main(overwrite=args.overwrite, csv_out=args.csv))
