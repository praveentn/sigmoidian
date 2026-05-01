#!/usr/bin/env python3
"""
Seed word definitions for T–Z words using Claude-generated data.

Usage:
    python scripts/seed_definitions_tz.py                # insert missing only
    python scripts/seed_definitions_tz.py --overwrite    # replace existing
    python scripts/seed_definitions_tz.py --csv          # also dump CSV
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

    # ── T ──────────────────────────────────────────────────────────────────

    "TABBY": {"pos": "noun", "meaning": "a domestic cat with striped or brindled fur; a plain-woven silk fabric", "example": "A tabby cat curled up on the warm windowsill."},
    "TABLE": {"pos": "noun", "meaning": "a flat horizontal surface supported by legs, used for placing objects on", "example": "They set the table with candles and fine china for the dinner party."},
    "TABOO": {"pos": "noun", "meaning": "a social or cultural prohibition against a particular action or subject", "example": "Discussing salary openly was once considered a workplace taboo."},
    "TACIT": {"pos": "adjective", "meaning": "understood or implied without being directly stated", "example": "There was a tacit agreement between the rivals to avoid personal attacks."},
    "TAFFY": {"pos": "noun", "meaning": "a chewy candy made from boiled sugar or molasses, pulled until glossy", "example": "The boardwalk shop sold saltwater taffy in a dozen flavors."},
    "TAINT": {"pos": "verb", "meaning": "to contaminate or corrupt; to affect with a trace of something bad", "example": "The scandal tainted his reputation for years."},
    "TALLY": {"pos": "noun", "meaning": "a current score or count; a record kept by marks", "example": "The treasurer kept a running tally of every donation received."},
    "TALON": {"pos": "noun", "meaning": "the claw of a bird of prey", "example": "The eagle gripped the salmon with its powerful talons."},
    "TANGO": {"pos": "noun", "meaning": "a ballroom dance of Latin American origin characterized by gliding steps and dramatic pauses", "example": "They learned the tango together before their wedding."},
    "TANGY": {"pos": "adjective", "meaning": "having a strong, sharp, pleasantly acidic taste or smell", "example": "The salad dressing had a tangy lime and cilantro flavor."},
    "TAPAS": {"pos": "noun", "meaning": "small savory Spanish dishes served as snacks or appetizers", "example": "They ordered a spread of tapas to share before the main course."},
    "TAPER": {"pos": "verb", "meaning": "to gradually become narrower or thinner toward one end", "example": "The candle tapered to a slender point at the top."},
    "TAPIR": {"pos": "noun", "meaning": "a large herbivorous mammal with a short flexible snout, native to tropical forests", "example": "The tapir waded into the river to cool off in the afternoon heat."},
    "TARDY": {"pos": "adjective", "meaning": "late; delayed beyond the expected or proper time", "example": "Three tardy students slipped quietly into the back of the classroom."},
    "TAROT": {"pos": "noun", "meaning": "a deck of cards used for divination or fortune-telling", "example": "She shuffled the tarot deck and drew three cards for the reading."},
    "TASTE": {"pos": "verb", "meaning": "to perceive the flavor of something; to sample food or drink", "example": "He tasted the soup and added a pinch of salt."},
    "TASTY": {"pos": "adjective", "meaning": "having a pleasant, appealing flavor", "example": "The chef prepared a tasty three-course meal for the guests."},
    "TAUNT": {"pos": "verb", "meaning": "to provoke or challenge someone with insulting or mocking remarks", "example": "The crowd taunted the visiting team as they left the field."},
    "TAWNY": {"pos": "adjective", "meaning": "of a warm brownish-orange or yellowish-brown color", "example": "The lion's tawny coat blended perfectly with the dry savanna grass."},
    "TEACH": {"pos": "verb", "meaning": "to impart knowledge or skill to; to instruct", "example": "She spent thirty years teaching mathematics at the local high school."},
    "TEASE": {"pos": "verb", "meaning": "to make fun of or attempt to provoke in a playful or unkind way", "example": "His older siblings liked to tease him about his fear of spiders."},
    "TEETH": {"pos": "noun", "meaning": "hard calcified structures in the jaws used for biting and chewing", "example": "She brushed her teeth twice a day as advised by the dentist."},
    "TEMPO": {"pos": "noun", "meaning": "the speed at which a piece of music is played", "example": "The conductor slowed the tempo during the mournful second movement."},
    "TEMPT": {"pos": "verb", "meaning": "to entice someone to do something unwise or wrong; to attract", "example": "The smell of fresh bread tempted him to stop at the bakery."},
    "TENET": {"pos": "noun", "meaning": "a principle or belief held by a person, organization, or movement", "example": "Respect for individual liberty is a core tenet of the organization."},
    "TENOR": {"pos": "noun", "meaning": "the highest natural adult male singing voice; the general meaning of something", "example": "The tenor's voice soared above the orchestra in the final aria."},
    "TENSE": {"pos": "adjective", "meaning": "stretched tight; mentally strained; anxious", "example": "The tense silence in the courtroom broke when the verdict was read."},
    "TENTH": {"pos": "adjective", "meaning": "constituting number ten in a sequence; equal to one part in ten", "example": "He finished tenth in a field of fifty competitive runners."},
    "TEPID": {"pos": "adjective", "meaning": "lukewarm; showing little enthusiasm or interest", "example": "The audience gave only tepid applause after the unremarkable performance."},
    "TERSE": {"pos": "adjective", "meaning": "sparing in words; abrupt to the point of being rude", "example": "Her terse reply made it clear she was not in the mood for conversation."},
    "THANK": {"pos": "verb", "meaning": "to express gratitude to someone", "example": "She wrote a card to thank her mentor for years of guidance."},
    "THEFT": {"pos": "noun", "meaning": "the act of stealing; the unlawful taking of another's property", "example": "Security cameras helped police solve the theft from the jewelry store."},
    "THEME": {"pos": "noun", "meaning": "the main subject or idea of a work; a recurring melody in music", "example": "The novel's central theme is the conflict between duty and desire."},
    "THICK": {"pos": "adjective", "meaning": "having a large distance between opposite surfaces; dense", "example": "They hiked through a thick forest where sunlight barely reached the ground."},
    "THIEF": {"pos": "noun", "meaning": "a person who steals another's property", "example": "The thief was caught on camera leaving the store with unpaid merchandise."},
    "THIGH": {"pos": "noun", "meaning": "the part of the leg between the hip and the knee", "example": "He stretched his thighs before the long run."},
    "THING": {"pos": "noun", "meaning": "an object or entity that is difficult to name precisely; a matter or concern", "example": "She had a thing for collecting vintage postcards from around the world."},
    "THINK": {"pos": "verb", "meaning": "to have a particular opinion or belief; to use the mind to reason", "example": "Take a moment to think before you answer."},
    "THIRD": {"pos": "adjective", "meaning": "coming after the second in position or rank", "example": "She won third place in the regional spelling competition."},
    "THORN": {"pos": "noun", "meaning": "a sharp pointed outgrowth on a plant stem; a source of irritation", "example": "She pricked her finger on a thorn while cutting roses from the garden."},
    "THREE": {"pos": "noun", "meaning": "the number 3; a group or set of three", "example": "The triplets arrived one after another, all three within the same hour."},
    "THROB": {"pos": "verb", "meaning": "to beat or pulse with a strong regular rhythm", "example": "His head throbbed after staring at the screen for hours."},
    "THROW": {"pos": "verb", "meaning": "to propel something through the air with force from the hand", "example": "He threw the ball so hard it sailed clear over the outfield fence."},
    "THUMB": {"pos": "noun", "meaning": "the short thick first digit of the human hand", "example": "She gave a thumbs-up to signal that everything was going well."},
    "THUMP": {"pos": "verb", "meaning": "to hit with a heavy dull blow; to beat strongly", "example": "He thumped on the door until someone finally answered."},
    "THYME": {"pos": "noun", "meaning": "a small aromatic herb widely used in cooking", "example": "She added fresh thyme to the roasting pan with the chicken."},
    "TIARA": {"pos": "noun", "meaning": "a jeweled ornamental crown worn on the head, especially by women", "example": "The beauty queen wore a sparkling tiara during the final ceremony."},
    "TIBIA": {"pos": "noun", "meaning": "the larger of the two bones in the lower leg; the shinbone", "example": "The X-ray showed a hairline fracture along the tibia."},
    "TIGER": {"pos": "noun", "meaning": "a large wild cat native to Asia with a striped orange and black coat", "example": "The tiger paced silently along the edge of the enclosure."},
    "TIGHT": {"pos": "adjective", "meaning": "firmly fixed, fastened, or closed; leaving little slack", "example": "The jar lid was so tight she had to tap the edge to loosen it."},
    "TILDE": {"pos": "noun", "meaning": "the diacritic mark ~ used in spelling or as a mathematical symbol", "example": "In Spanish, the tilde over the n in 'mañana' changes its pronunciation."},
    "TIMER": {"pos": "noun", "meaning": "a device that measures elapsed time or triggers an event after a set period", "example": "She set a kitchen timer so the bread wouldn't overbake."},
    "TIMID": {"pos": "adjective", "meaning": "lacking self-confidence or boldness; easily frightened", "example": "The timid puppy hid behind the sofa when visitors arrived."},
    "TINGE": {"pos": "noun", "meaning": "a slight trace of color, feeling, or quality", "example": "The evening sky had a tinge of pink along the horizon."},
    "TIPSY": {"pos": "adjective", "meaning": "slightly drunk; unsteady from the effects of alcohol", "example": "After two glasses of wine she felt pleasantly tipsy."},
    "TIRED": {"pos": "adjective", "meaning": "in need of sleep or rest; worn out", "example": "After the long hike, they were too tired to cook and ordered pizza."},
    "TITAN": {"pos": "noun", "meaning": "a person of exceptional strength, importance, or achievement", "example": "He was widely regarded as a titan of the film industry."},
    "TITHE": {"pos": "noun", "meaning": "a tenth part of income given as a tax or contribution, especially to a church", "example": "Members of the congregation were encouraged to tithe a portion of their earnings."},
    "TITLE": {"pos": "noun", "meaning": "the name of a book, film, or other work; a name indicating rank or status", "example": "The title of her debut novel became a phrase everyone seemed to quote."},
    "TOAST": {"pos": "noun", "meaning": "sliced bread browned by heat; a call to drink in honor of someone", "example": "The best man raised his glass for the wedding toast."},
    "TODAY": {"pos": "noun", "meaning": "the present day; this current day", "example": "Today is the first day of the rest of your life, as the saying goes."},
    "TOKEN": {"pos": "noun", "meaning": "a thing that serves as a symbol or sign; a voucher or coin-like object", "example": "She kept the small coin as a token of their first trip abroad together."},
    "TONAL": {"pos": "adjective", "meaning": "relating to tone or musical pitch; having tonal qualities", "example": "The composer used tonal contrasts to build tension in the second act."},
    "TONER": {"pos": "noun", "meaning": "a powder used in laser printers; a cosmetic liquid applied to the skin", "example": "The office ran out of toner just before the big presentation."},
    "TONIC": {"pos": "noun", "meaning": "a drink with restorative or invigorating properties; a carbonated mixer", "example": "She ordered gin and tonic with a slice of lime."},
    "TOOTH": {"pos": "noun", "meaning": "each of the hard structures in the jaws used for biting and chewing food", "example": "He chipped a tooth biting into the hard candy."},
    "TOPAZ": {"pos": "noun", "meaning": "a precious gemstone typically yellow or pale blue in color", "example": "The ring featured a golden topaz set in antique silver."},
    "TOPIC": {"pos": "noun", "meaning": "a subject being discussed, written about, or studied", "example": "Climate change was the main topic at the international summit."},
    "TORCH": {"pos": "noun", "meaning": "a portable light source; a flaming stick or handheld electric light", "example": "Explorers carried torches as they descended into the cave."},
    "TORSO": {"pos": "noun", "meaning": "the trunk of the human body, excluding the head and limbs", "example": "The sculpture depicted only the torso, carved from pale marble."},
    "TOTAL": {"pos": "noun", "meaning": "the whole number or amount; the sum of all parts", "example": "The total cost came to more than they had budgeted for the renovation."},
    "TOUCH": {"pos": "verb", "meaning": "to make physical contact with; to affect emotionally", "example": "Her speech touched everyone in the audience."},
    "TOUGH": {"pos": "adjective", "meaning": "strong enough to withstand strain; difficult to do or deal with", "example": "It was a tough decision, but she chose to leave the company she had built."},
    "TOWEL": {"pos": "noun", "meaning": "a piece of absorbent cloth used for drying", "example": "He grabbed a towel and headed for the outdoor shower."},
    "TOWER": {"pos": "noun", "meaning": "a tall narrow building or structure", "example": "They climbed to the top of the clock tower to see the whole city."},
    "TOXIC": {"pos": "adjective", "meaning": "poisonous; causing harm to living things", "example": "Workers wore protective gear to handle the toxic chemicals safely."},
    "TOXIN": {"pos": "noun", "meaning": "a poisonous substance, especially one produced by a living organism", "example": "The lab identified a bacterial toxin as the cause of the outbreak."},
    "TRACE": {"pos": "verb", "meaning": "to follow the course or track of; to copy by following lines", "example": "Detectives traced the package back to a warehouse across town."},
    "TRACK": {"pos": "noun", "meaning": "a path or course; a prepared running surface; a recorded song", "example": "The third track on the album became an unexpected radio hit."},
    "TRADE": {"pos": "noun", "meaning": "the buying and selling of goods; a skilled occupation", "example": "He learned the trade of carpentry from his grandfather."},
    "TRAIL": {"pos": "noun", "meaning": "a path through wilderness; a mark left by something moving", "example": "They followed the nature trail to the waterfall lookout point."},
    "TRAIN": {"pos": "noun", "meaning": "a series of railway cars pulled by a locomotive; to teach or drill", "example": "The overnight train carried them through the mountains to the capital."},
    "TRAIT": {"pos": "noun", "meaning": "a distinguishing quality or characteristic of a person", "example": "Patience is her most admirable trait as a teacher."},
    "TRAMP": {"pos": "noun", "meaning": "a person who travels without a fixed home; a heavy tread", "example": "They heard the tramp of boots on the wooden floor above them."},
    "TRASH": {"pos": "noun", "meaning": "waste material; rubbish; something of low quality", "example": "He took the trash out before the collection truck arrived at dawn."},
    "TRAWL": {"pos": "verb", "meaning": "to fish using a wide-mouthed net dragged along the seabed", "example": "The fishing vessel trawled the waters for hours before filling its nets."},
    "TREAD": {"pos": "verb", "meaning": "to walk or step; to press underfoot", "example": "They tread carefully across the icy path to avoid slipping."},
    "TREAT": {"pos": "noun", "meaning": "something pleasant given as a reward; to deal with in a particular way", "example": "She took the children out for ice cream as a special treat."},
    "TREND": {"pos": "noun", "meaning": "a general direction in which something is developing or changing", "example": "The trend toward remote work accelerated dramatically that year."},
    "TRIAD": {"pos": "noun", "meaning": "a group or set of three related people or things", "example": "The triad of freedom, equality, and justice anchors the nation's constitution."},
    "TRIAL": {"pos": "noun", "meaning": "a formal examination of evidence in a court of law; a test of endurance", "example": "The trial lasted six weeks before the jury reached a verdict."},
    "TRIBE": {"pos": "noun", "meaning": "a social group with shared customs, language, and ancestry", "example": "The tribe held a ceremony to mark the passing of the winter solstice."},
    "TRICK": {"pos": "noun", "meaning": "a cunning or deceptive act; a clever technique or knack", "example": "The magician's best trick involved a locked box and a live dove."},
    "TRILL": {"pos": "noun", "meaning": "a rapid alternation between two adjacent musical notes; a quavering sound", "example": "The flute played a delicate trill at the opening of the concerto."},
    "TRIPE": {"pos": "noun", "meaning": "the stomach lining of an animal used as food; nonsense", "example": "The soup was a traditional recipe made with tripe and root vegetables."},
    "TRITE": {"pos": "adjective", "meaning": "overused and therefore lacking in originality or impact", "example": "The speech was full of trite phrases that left the audience unmoved."},
    "TROLL": {"pos": "noun", "meaning": "a mythological creature living under bridges; one who posts inflammatory online content", "example": "Internet trolls flooded the comment section with hostile replies."},
    "TROOP": {"pos": "noun", "meaning": "a group of soldiers; an organized group of people", "example": "A troop of scouts camped beside the river for the weekend."},
    "TROUT": {"pos": "noun", "meaning": "a freshwater fish of the salmon family, prized for sport and food", "example": "He spent the morning fly-fishing and caught three brown trout."},
    "TRUCE": {"pos": "noun", "meaning": "an agreement to stop fighting temporarily; a ceasefire", "example": "The warring factions declared a truce to allow aid workers through."},
    "TRUCK": {"pos": "noun", "meaning": "a large heavy motor vehicle for transporting goods", "example": "The delivery truck pulled up to the warehouse before dawn."},
    "TRULY": {"pos": "adverb", "meaning": "in a truthful or genuine way; to the fullest extent", "example": "She was truly grateful for the support she received during her illness."},
    "TRUMP": {"pos": "verb", "meaning": "to surpass or outdo; to play a trump card in a card game", "example": "Her practical experience trumped his theoretical knowledge in the interview."},
    "TRUNK": {"pos": "noun", "meaning": "the main woody stem of a tree; a large rigid luggage box; the torso", "example": "The ancient oak had a trunk so wide three people couldn't encircle it."},
    "TRUSS": {"pos": "noun", "meaning": "a framework of beams or rods supporting a roof or bridge", "example": "The steel truss held the bridge deck firmly above the river gorge."},
    "TRUST": {"pos": "noun", "meaning": "firm belief in the reliability, honesty, or ability of someone or something", "example": "Building trust with clients takes years but can be lost in an instant."},
    "TRUTH": {"pos": "noun", "meaning": "the quality of being in accordance with fact or reality", "example": "She demanded to hear the truth, no matter how uncomfortable it might be."},
    "TRYST": {"pos": "noun", "meaning": "a secret or private meeting between lovers", "example": "They arranged a midnight tryst at the old lighthouse by the shore."},
    "TULIP": {"pos": "noun", "meaning": "a spring-flowering bulb plant with cup-shaped blooms in bright colors", "example": "The park was carpeted with red and yellow tulips each April."},
    "TUMMY": {"pos": "noun", "meaning": "the stomach or abdomen, especially when used informally", "example": "The child complained of a tummy ache after eating too much cake."},
    "TUMOR": {"pos": "noun", "meaning": "an abnormal growth of tissue in the body", "example": "The scan revealed a small tumor that doctors said was benign."},
    "TUNER": {"pos": "noun", "meaning": "a device for tuning a radio or musical instrument to the correct pitch", "example": "He clipped the electronic tuner to the headstock of his guitar."},
    "TUNIC": {"pos": "noun", "meaning": "a loose sleeveless garment extending to the thighs or knees", "example": "The soldiers wore short tunics beneath their armor."},
    "TUPLE": {"pos": "noun", "meaning": "an ordered collection of elements; in computing, an immutable sequence", "example": "The function returned a tuple containing the latitude and longitude."},
    "TURBO": {"pos": "adjective", "meaning": "using a turbine driven by exhaust gases to boost engine power", "example": "The turbo engine gave the compact car surprising acceleration on the highway."},
    "TUTOR": {"pos": "noun", "meaning": "a private teacher who gives individual instruction", "example": "She hired a math tutor to help her son prepare for the entrance exam."},
    "TWANG": {"pos": "noun", "meaning": "a sharp ringing sound like a plucked string; a nasal tone of voice", "example": "The guitar string gave a bright twang as he strummed the opening chord."},
    "TWEAK": {"pos": "verb", "meaning": "to improve or adjust something by making small changes", "example": "She tweaked the recipe by adding a pinch of smoked paprika."},
    "TWEED": {"pos": "noun", "meaning": "a rough-surfaced woolen fabric woven with mixed colored yarns", "example": "He wore a tweed jacket with leather elbow patches to the faculty meeting."},
    "TWEET": {"pos": "noun", "meaning": "the chirping call of a small bird; a short social media post", "example": "The musician's tweet announcing the surprise album crashed the app."},
    "TWICE": {"pos": "adverb", "meaning": "two times; on two occasions", "example": "She read the letter twice before she fully understood its meaning."},
    "TWILL": {"pos": "noun", "meaning": "a fabric woven with a diagonal rib pattern", "example": "The trousers were cut from sturdy cotton twill that held its shape well."},
    "TWINE": {"pos": "noun", "meaning": "strong string made of twisted strands", "example": "He tied the parcel with brown paper and garden twine."},
    "TWINS": {"pos": "noun", "meaning": "two children or animals born at the same birth", "example": "The twins were so identical their parents had to label their clothing."},
    "TWIRL": {"pos": "verb", "meaning": "to spin or rotate quickly and lightly", "example": "She twirled across the dance floor in a flowing skirt."},
    "TWIST": {"pos": "verb", "meaning": "to wind or turn something round and round; to distort", "example": "He twisted the wire into the shape of a small bird."},
    "TYPED": {"pos": "verb", "meaning": "past tense of type; entered text using a keyboard", "example": "She typed the letter quickly and hit send before changing her mind."},
    "TYPOS": {"pos": "noun", "meaning": "typographical errors made when typing", "example": "He proofread the document twice but still missed a few typos."},

    # ── U ──────────────────────────────────────────────────────────────────

    "UDDER": {"pos": "noun", "meaning": "the mammary gland of a cow or other female mammal, containing the teats", "example": "The farmer gently cleaned the udder before beginning the milking."},
    "ULCER": {"pos": "noun", "meaning": "an open sore on the body's surface or lining, slow to heal", "example": "Stress and poor diet contributed to the stomach ulcer he developed."},
    "ULTRA": {"pos": "adjective", "meaning": "going beyond what is ordinary or moderate; extreme", "example": "The ultra-thin laptop was barely heavier than a notepad."},
    "UNCLE": {"pos": "noun", "meaning": "the brother of one's parent, or the husband of one's aunt", "example": "Her uncle taught her to fish every summer at the lake cabin."},
    "UNDER": {"pos": "preposition", "meaning": "extending below; lower than; subject to the authority of", "example": "The cat hid under the bed during the thunderstorm."},
    "UNFIT": {"pos": "adjective", "meaning": "not in good physical condition; not qualified or suitable", "example": "Years without exercise had left him unfit for the demanding hike."},
    "UNIFY": {"pos": "verb", "meaning": "to bring together into a single unit or whole; to make uniform", "example": "The new leader promised to unify the deeply divided country."},
    "UNION": {"pos": "noun", "meaning": "the action of joining or being joined together; an organized group of workers", "example": "The union negotiated a new contract that included better healthcare benefits."},
    "UNITE": {"pos": "verb", "meaning": "to come or bring together for a common purpose or action", "example": "The disaster united neighbors who had barely spoken to each other before."},
    "UNITY": {"pos": "noun", "meaning": "the state of being united or joined as a whole; harmony", "example": "The choir performed with remarkable unity of tone and timing."},
    "UPPER": {"pos": "adjective", "meaning": "situated above another part; higher in position or rank", "example": "The upper floors of the building offered views across the entire bay."},
    "UPSET": {"pos": "verb", "meaning": "to disturb the composure of; to knock over; to defeat unexpectedly", "example": "The young challenger upset the reigning champion in the second round."},
    "URBAN": {"pos": "adjective", "meaning": "relating to or characteristic of a city or town", "example": "Urban planners worked to create more green space in the dense neighborhood."},
    "URGED": {"pos": "verb", "meaning": "past tense of urge; strongly encouraged or pushed someone to act", "example": "Her doctor urged her to rest completely for at least two weeks."},
    "URINE": {"pos": "noun", "meaning": "the liquid waste product excreted by the kidneys", "example": "The lab tested a urine sample to check for signs of infection."},
    "USAGE": {"pos": "noun", "meaning": "the manner in which something is used; customary practice", "example": "The style guide explained the correct usage of commas in complex sentences."},
    "USHER": {"pos": "verb", "meaning": "to guide or escort someone to their seat or destination", "example": "An attendant ushered the guests to their reserved seats in the front row."},
    "USUAL": {"pos": "adjective", "meaning": "habitually or typically occurring; ordinary; customary", "example": "She ordered her usual coffee and sat by the window to read."},
    "USURP": {"pos": "verb", "meaning": "to seize and hold a position of power illegally or by force", "example": "The general attempted to usurp control of the government in a midnight coup."},
    "USURY": {"pos": "noun", "meaning": "the practice of lending money at excessively high rates of interest", "example": "Medieval laws condemned usury as a sin against the community."},
    "UTTER": {"pos": "verb", "meaning": "to make a sound or speak words; complete or absolute", "example": "She uttered not a single word throughout the entire interview."},

    # ── V ──────────────────────────────────────────────────────────────────

    "VAGUE": {"pos": "adjective", "meaning": "not clearly expressed or understood; lacking definite form", "example": "His answer was so vague that no one was sure what he actually meant."},
    "VALET": {"pos": "noun", "meaning": "a personal attendant who looks after clothing and other personal needs", "example": "The hotel offered valet parking so guests could leave their cars at the entrance."},
    "VALID": {"pos": "adjective", "meaning": "sound and well-grounded; legally or officially acceptable", "example": "You need a valid passport to board any international flight."},
    "VALOR": {"pos": "noun", "meaning": "great courage in the face of danger, especially in battle", "example": "The soldier received a medal for valor after pulling his comrades from enemy fire."},
    "VALUE": {"pos": "noun", "meaning": "the worth, importance, or usefulness of something", "example": "The antique dealer assessed the value of the painting at forty thousand dollars."},
    "VALVE": {"pos": "noun", "meaning": "a device that controls the flow of liquid or gas through a pipe", "example": "The plumber replaced the faulty valve that had been causing the leak."},
    "VAPOR": {"pos": "noun", "meaning": "a substance in a gaseous state; moisture visible as mist or steam", "example": "Water vapor rose from the hot spring and drifted across the cold morning air."},
    "VAULT": {"pos": "noun", "meaning": "an arched chamber, often underground; a secure room for valuables", "example": "The bank's vault was sealed with a foot-thick steel door."},
    "VEGAN": {"pos": "noun", "meaning": "a person who does not eat or use any animal products", "example": "The restaurant expanded its menu to include more options for vegan diners."},
    "VEINS": {"pos": "noun", "meaning": "blood vessels that carry blood toward the heart; lines in rock or leaves", "example": "The veins of quartz running through the granite caught the light beautifully."},
    "VENAL": {"pos": "adjective", "meaning": "willing to act dishonestly for money; open to bribery", "example": "The venal official accepted payments to ignore safety violations."},
    "VENOM": {"pos": "noun", "meaning": "a poison produced by an animal and transmitted by bite or sting", "example": "Antivenom must be administered quickly after a cobra bite."},
    "VERGE": {"pos": "noun", "meaning": "an edge or border; the point beyond which something begins", "example": "She was on the verge of tears when she heard the unexpected news."},
    "VERSE": {"pos": "noun", "meaning": "a line or group of lines forming part of a poem or song", "example": "He recited the opening verse of the poem from memory."},
    "VERVE": {"pos": "noun", "meaning": "enthusiasm, energy, and vigor, especially in artistic performance", "example": "The young conductor led the orchestra with extraordinary verve and passion."},
    "VICAR": {"pos": "noun", "meaning": "a Church of England priest in charge of a parish", "example": "The vicar opened the village fete with a short blessing."},
    "VIDEO": {"pos": "noun", "meaning": "a recording or broadcast of moving visual images", "example": "They watched the video of the ceremony again and again with tearful smiles."},
    "VIGIL": {"pos": "noun", "meaning": "a period of staying awake to watch over someone or something", "example": "Friends kept a candlelight vigil outside the hospital through the night."},
    "VIGOR": {"pos": "noun", "meaning": "physical or mental strength, energy, and enthusiasm", "example": "Despite her age, she tackled the project with the vigor of someone half her years."},
    "VILLA": {"pos": "noun", "meaning": "a large country house, especially one used as a holiday retreat", "example": "They rented a whitewashed villa overlooking the Aegean for two weeks."},
    "VINYL": {"pos": "noun", "meaning": "a tough flexible plastic; a gramophone record made from this material", "example": "He preferred the warmth of vinyl records over digital streaming."},
    "VIOLA": {"pos": "noun", "meaning": "a bowed string instrument slightly larger than a violin with a deeper tone", "example": "The viola section added rich, dark tones to the center of the orchestra."},
    "VIPER": {"pos": "noun", "meaning": "a venomous snake with long hinged fangs; a treacherous person", "example": "Hikers were warned to watch for vipers sunning on the rocky trail."},
    "VIRAL": {"pos": "adjective", "meaning": "spreading rapidly and widely online; relating to a virus", "example": "The heartwarming rescue video went viral within hours of being posted."},
    "VIRUS": {"pos": "noun", "meaning": "a submicroscopic infectious agent; a harmful program in computing", "example": "The computer virus corrupted every file on the shared network drive."},
    "VISIT": {"pos": "verb", "meaning": "to go to see a person or place, usually for a short time", "example": "She visited her grandmother every Sunday without fail."},
    "VISOR": {"pos": "noun", "meaning": "a projecting brim at the front of a cap; a shield for the face", "example": "He flipped down the car's visor to block the blinding afternoon sun."},
    "VISTA": {"pos": "noun", "meaning": "a pleasing view, especially a long narrow one between buildings or trees", "example": "The mountain pass opened onto a breathtaking vista of the valley below."},
    "VITAL": {"pos": "adjective", "meaning": "absolutely necessary; essential to life", "example": "Regular hydration is vital for maintaining concentration and energy."},
    "VIVID": {"pos": "adjective", "meaning": "producing powerful feelings or strong clear images; very bright", "example": "She had a vivid memory of the afternoon her father taught her to ride a bike."},
    "VIXEN": {"pos": "noun", "meaning": "a female fox; an attractive or quarrelsome woman", "example": "The vixen carried a rabbit back to her den in the hedgerow."},
    "VOCAL": {"pos": "adjective", "meaning": "relating to the voice; expressing opinions openly and forcefully", "example": "She was a vocal critic of the new policy at every community meeting."},
    "VODKA": {"pos": "noun", "meaning": "a clear distilled spirit, originally from Eastern Europe", "example": "He ordered a vodka tonic with two limes at the bar."},
    "VOGUE": {"pos": "noun", "meaning": "the prevailing fashion or style at a particular time", "example": "Minimalist interior design was very much in vogue that decade."},
    "VOICE": {"pos": "noun", "meaning": "the sound produced by a person speaking or singing; the right to express opinions", "example": "Her calm, measured voice reassured everyone in the room."},
    "VOMIT": {"pos": "verb", "meaning": "to eject the contents of the stomach through the mouth", "example": "The rough seas made half the passengers vomit over the side."},
    "VOTER": {"pos": "noun", "meaning": "a person who casts a vote in an election", "example": "First-time voters waited in long lines at the polling station."},
    "VOUCH": {"pos": "verb", "meaning": "to confirm or assert that something is true; to act as a guarantor", "example": "His former employer vouched for his honesty and reliability."},
    "VOWEL": {"pos": "noun", "meaning": "a speech sound produced with an open vocal tract; one of the letters a, e, i, o, u", "example": "Every syllable in English contains at least one vowel."},
    "VROOM": {"pos": "interjection", "meaning": "a sound imitating the noise of a vehicle engine accelerating", "example": "The sports car went vroom as it accelerated out of the tunnel."},

    # ── W ──────────────────────────────────────────────────────────────────

    "WACKY": {"pos": "adjective", "meaning": "amusingly eccentric or irrational; absurdly comical", "example": "The wacky game show required contestants to answer questions while spinning."},
    "WAFER": {"pos": "noun", "meaning": "a very thin light crisp biscuit; a thin disc of unleavened bread", "example": "She dipped the wafer into her hot chocolate and ate it in one bite."},
    "WAGER": {"pos": "noun", "meaning": "a bet or gamble on the outcome of an uncertain event", "example": "He placed a small wager on the underdog and won fifty dollars."},
    "WAGON": {"pos": "noun", "meaning": "a four-wheeled vehicle pulled by horses or other animals; a large trolley", "example": "The covered wagon carried their belongings across the prairie."},
    "WAIST": {"pos": "noun", "meaning": "the part of the human body below the ribs and above the hips", "example": "The tailor measured her waist before cutting the fabric for the dress."},
    "WAIVE": {"pos": "verb", "meaning": "to refrain from insisting on or using a right or requirement", "example": "The fee was waived for applicants who demonstrated financial hardship."},
    "WALTZ": {"pos": "noun", "meaning": "a ballroom dance in triple time with a turning, gliding motion", "example": "The couple danced a waltz to the old melody that played at their first meeting."},
    "WASTE": {"pos": "noun", "meaning": "unwanted or unusable material; the action of using something carelessly", "example": "She hated food waste and always found a way to use up leftovers."},
    "WATCH": {"pos": "verb", "meaning": "to look at attentively; to keep under careful observation", "example": "They watched the sunset from the hilltop without speaking a word."},
    "WATER": {"pos": "noun", "meaning": "the colorless liquid that forms rain, rivers, and oceans, essential to life", "example": "She drank two liters of water each day to stay properly hydrated."},
    "WEARY": {"pos": "adjective", "meaning": "feeling or showing extreme tiredness, especially from long exertion", "example": "Weary travelers slumped in their seats as the train pulled into the station."},
    "WEAVE": {"pos": "verb", "meaning": "to interlace threads to form fabric; to move in a winding path", "example": "She wove strips of willow into a tight, sturdy basket."},
    "WEDGE": {"pos": "noun", "meaning": "a piece of material thick at one end and thin at the other, used for splitting", "example": "He drove a steel wedge into the log with a single blow of the mallet."},
    "WEEDS": {"pos": "noun", "meaning": "wild plants growing where they are not wanted", "example": "She spent Saturday morning pulling weeds from the vegetable garden."},
    "WEIRD": {"pos": "adjective", "meaning": "suggesting something supernatural; strikingly odd or unusual", "example": "A weird humming noise came from the basement at night."},
    "WELCH": {"pos": "verb", "meaning": "to fail to honor a promise or obligation, especially to repay a debt", "example": "He welched on the bet and refused to pay what he owed."},
    "WHALE": {"pos": "noun", "meaning": "a very large marine mammal with a streamlined body and horizontal tail", "example": "The whale surfaced with a tremendous spray fifty meters from the boat."},
    "WHACK": {"pos": "verb", "meaning": "to strike something with a sharp blow", "example": "She whacked the piñata until candy showered across the grass."},
    "WHEAT": {"pos": "noun", "meaning": "a cereal grain widely grown for its seed, ground into flour", "example": "The golden wheat fields stretched to the horizon in every direction."},
    "WHEEL": {"pos": "noun", "meaning": "a circular frame that revolves on an axle; the circular steering control of a vehicle", "example": "The potter shaped the clay bowl on a spinning wheel."},
    "WHILE": {"pos": "conjunction", "meaning": "during the time that; at the same time as", "example": "She read a novel while waiting for her flight to be called."},
    "WHINE": {"pos": "verb", "meaning": "to make a long high-pitched complaining sound; to complain persistently", "example": "The dog sat by the door and whined until someone took him for a walk."},
    "WHIRL": {"pos": "verb", "meaning": "to move rapidly in circles or a curving course", "example": "Leaves whirled in the wind before the first autumn storm arrived."},
    "WHISK": {"pos": "verb", "meaning": "to move something quickly and lightly; to beat eggs or cream with a whisk", "example": "She whisked the eggs until they were pale and frothy."},
    "WHITE": {"pos": "adjective", "meaning": "of the color of milk or fresh snow; reflecting all visible light", "example": "The bride wore a simple white dress with tiny pearl buttons."},
    "WHOLE": {"pos": "adjective", "meaning": "complete or entire; not divided or in parts", "example": "She ate the whole pizza before realizing how hungry she had been."},
    "WHOOP": {"pos": "verb", "meaning": "to shout loudly in excitement or joy", "example": "The crowd whooped when the final buzzer sounded and their team had won."},
    "WHORL": {"pos": "noun", "meaning": "a spiral or circular arrangement of things; a fingerprint pattern", "example": "Each shell had a perfect whorl that tightened toward the tip."},
    "WIDOW": {"pos": "noun", "meaning": "a woman whose husband has died and who has not remarried", "example": "The widow quietly folded the flag handed to her at the graveside service."},
    "WIDTH": {"pos": "noun", "meaning": "the measurement or extent of something from side to side", "example": "Measure the width of the doorway before buying the new bookcase."},
    "WIELD": {"pos": "verb", "meaning": "to hold and use a weapon or tool; to have and exercise power", "example": "The knight wielded his sword with practiced ease."},
    "WITCH": {"pos": "noun", "meaning": "a person believed to practice magic, especially with evil intent", "example": "In the fairytale, the witch offered the princess a poisoned apple."},
    "WOMAN": {"pos": "noun", "meaning": "an adult female human being", "example": "The woman who founded the charity devoted decades to the cause."},
    "WOMEN": {"pos": "noun", "meaning": "the plural of woman; adult female human beings", "example": "Women made up the majority of the volunteers at the community center."},
    "WONKY": {"pos": "adjective", "meaning": "unsteady or crooked; not working correctly", "example": "The cafe had wonky chairs and mismatched tables that somehow added to its charm."},
    "WOODS": {"pos": "noun", "meaning": "a small area of trees denser than a copse but smaller than a forest", "example": "They walked through the woods at dusk, listening to owls overhead."},
    "WOOZY": {"pos": "adjective", "meaning": "unsteady, dizzy, or dazed, especially from illness or alcohol", "example": "She felt woozy after standing up too quickly in the heat."},
    "WORRY": {"pos": "verb", "meaning": "to feel or cause to feel anxious or uneasy about something", "example": "He tried not to worry about things that were outside his control."},
    "WORSE": {"pos": "adjective", "meaning": "of lower quality or a more serious degree than before", "example": "The weather grew worse as the afternoon turned into evening."},
    "WORST": {"pos": "adjective", "meaning": "of the lowest quality or the most serious degree", "example": "It was the worst storm the island had seen in living memory."},
    "WORTH": {"pos": "noun", "meaning": "the level of value or importance of something or someone", "example": "The renovations added considerable worth to the property."},
    "WOUND": {"pos": "noun", "meaning": "an injury to the body caused by a cut, blow, or other impact", "example": "She cleaned and bandaged the wound before driving him to the clinic."},
    "WOVEN": {"pos": "adjective", "meaning": "past participle of weave; made by interlacing threads or fibers", "example": "The rug was woven from brightly dyed wool in geometric patterns."},
    "WRATH": {"pos": "noun", "meaning": "extreme anger; fierce retribution for a wrong", "example": "He incurred the wrath of his editor by missing three deadlines in a row."},
    "WREAK": {"pos": "verb", "meaning": "to cause a large amount of harm or damage", "example": "The hurricane wreaked havoc on the coastal towns in its path."},
    "WRECK": {"pos": "noun", "meaning": "the destruction of a vehicle, vessel, or aircraft; something ruined", "example": "Salvage divers explored the wreck of a cargo ship that sank in 1943."},
    "WRING": {"pos": "verb", "meaning": "to squeeze and twist to remove liquid; to obtain by persistent effort", "example": "She wrung out the wet towel and hung it over the balcony railing."},
    "WRIST": {"pos": "noun", "meaning": "the joint connecting the hand and forearm", "example": "She wore a delicate silver bracelet on her left wrist."},
    "WRITE": {"pos": "verb", "meaning": "to mark letters, words, or symbols on a surface; to compose text", "example": "He sat down every morning to write before the rest of the house woke up."},
    "WRONG": {"pos": "adjective", "meaning": "not correct or true; unjust or immoral", "example": "She knew the answer was wrong but submitted it anyway under time pressure."},
    "WRYLY": {"pos": "adverb", "meaning": "with dry, ironic humor; in a wry manner", "example": "He smiled wryly and said he supposed losing was character-building."},

    # ── X ──────────────────────────────────────────────────────────────────

    "XEBEC": {"pos": "noun", "meaning": "a small three-masted Mediterranean sailing vessel formerly used by pirates", "example": "The museum displayed a model of an eighteenth-century xebec."},
    "XENON": {"pos": "noun", "meaning": "a heavy colorless odorless inert gaseous chemical element used in lamps", "example": "Xenon arc lamps produce a very bright, white light used in cinema projectors."},
    "XEROX": {"pos": "verb", "meaning": "to photocopy a document on a Xerox machine", "example": "She xeroxed the contract and kept a copy in her personal files."},
    "XYLEM": {"pos": "noun", "meaning": "the vascular tissue in plants that transports water and minerals upward from roots", "example": "The xylem in trees can carry water dozens of meters against gravity."},

    # ── Y ──────────────────────────────────────────────────────────────────

    "YAHOO": {"pos": "noun", "meaning": "an uncultured or boorish person; a shout of joy or excitement", "example": "He let out a yahoo and threw his hat in the air when his number was called."},
    "YARDS": {"pos": "noun", "meaning": "units of linear measurement equal to three feet; enclosed outdoor areas", "example": "The back yard stretched fifty yards from the house to the old stone wall."},
    "YARNS": {"pos": "noun", "meaning": "spun threads used for knitting or weaving; long rambling stories", "example": "The fisherman spun yarns about the one that got away."},
    "YEARN": {"pos": "verb", "meaning": "to have an intense longing for something", "example": "She yearned to return to the small coastal town where she grew up."},
    "YEARS": {"pos": "noun", "meaning": "periods of twelve months; a long time", "example": "It had been years since they last saw each other, yet nothing felt changed."},
    "YEAST": {"pos": "noun", "meaning": "a fungus used in baking and brewing to cause fermentation and rising", "example": "Without enough yeast, the bread will fail to rise in the oven."},
    "YELLS": {"pos": "verb", "meaning": "shouts loudly, especially in pain, anger, or excitement", "example": "He yells the scores across the field so everyone can hear."},
    "YELPS": {"pos": "verb", "meaning": "utters short sharp cries of pain or alarm", "example": "The puppy yelps whenever its tail gets accidentally stepped on."},
    "YIELD": {"pos": "verb", "meaning": "to produce or provide; to give way under pressure or authority", "example": "The orchard yields hundreds of kilograms of apples in a good year."},
    "YODEL": {"pos": "verb", "meaning": "to sing in a style that switches rapidly between chest voice and falsetto", "example": "The hiker yodeled across the valley and heard an echo return."},
    "YOKEL": {"pos": "noun", "meaning": "an unsophisticated person from a rural area", "example": "The city journalists condescendingly called every farmer a yokel."},
    "YOUNG": {"pos": "adjective", "meaning": "having lived or existed for only a short time; not yet old", "example": "Even at a young age she showed remarkable talent for mathematics."},
    "YOUTH": {"pos": "noun", "meaning": "the state or period of being young; young people collectively", "example": "She spent her youth traveling and rarely stayed in one place for long."},
    "YUCCA": {"pos": "noun", "meaning": "a desert plant with stiff spiky leaves and tall flower spikes, native to the Americas", "example": "A row of yuccas lined the dry garden path like silent sentinels."},
    "YUCKY": {"pos": "adjective", "meaning": "messy, dirty, or disgusting; unpleasant to look at or deal with", "example": "The children made a yucky face at the bowl of overcooked Brussels sprouts."},
    "YUMMY": {"pos": "adjective", "meaning": "highly attractive or pleasing, especially to taste; delicious", "example": "The freshly baked cinnamon rolls smelled yummy from the end of the street."},
    "YURTS": {"pos": "noun", "meaning": "circular portable tents traditionally used by nomads in Central Asia", "example": "The festival offered guests the option of sleeping in decorated yurts on the hillside."},

    # ── Z ──────────────────────────────────────────────────────────────────

    "ZEBRA": {"pos": "noun", "meaning": "an African wild horse with distinctive black and white stripes", "example": "A herd of zebras gathered at the watering hole at dusk."},
    "ZEROS": {"pos": "noun", "meaning": "the numerical digit 0; points at which a function equals zero", "example": "The forecast read zeros across the board — no chance of rain."},
    "ZESTY": {"pos": "adjective", "meaning": "having a strong, pleasantly sharp or spicy flavor; lively and energetic", "example": "The salsa was zesty enough to make his eyes water pleasantly."},
    "ZILCH": {"pos": "noun", "meaning": "nothing at all; zero", "example": "After searching every drawer, she found zilch — the key had simply vanished."},
    "ZINGY": {"pos": "adjective", "meaning": "pleasantly sharp or stimulating in taste, smell, or effect", "example": "The lemonade had a zingy freshness that cut through the summer heat."},
    "ZIPPY": {"pos": "adjective", "meaning": "bright and lively; able to move smartly and briskly", "example": "The little electric scooter was surprisingly zippy in city traffic."},
    "ZLOTY": {"pos": "noun", "meaning": "the basic monetary unit of Poland", "example": "He exchanged his euros for zloty at the airport before heading into the city."},
    "ZONES": {"pos": "noun", "meaning": "areas with particular characteristics or uses; defined geographic regions", "example": "The city was divided into residential and commercial zones by the new planning law."},
    "ZOOMS": {"pos": "verb", "meaning": "moves very quickly; adjusts a camera lens to change magnification", "example": "The photographer zooms in on the subject to fill the frame."},
    "ZOMBI": {"pos": "noun", "meaning": "variant spelling of zombie; a corpse said to be revived by supernatural means", "example": "The folklore of the region was full of tales of the zombi that walked at night."},
}


# ── helpers ────────────────────────────────────────────────────────────────────

async def load_words(path: pathlib.Path) -> list[str]:
    words = []
    with path.open() as f:
        for line in f:
            w = line.strip().upper()
            if len(w) == 5 and w.isalpha():
                words.append(w)
    return words


async def ensure_table(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS word_definitions (
            word    TEXT PRIMARY KEY,
            pos     TEXT NOT NULL DEFAULT '',
            meaning TEXT NOT NULL DEFAULT '',
            example TEXT NOT NULL DEFAULT ''
        )
    """)


async def upsert(conn: asyncpg.Connection, word: str, d: dict, overwrite: bool) -> None:
    if overwrite:
        await conn.execute(
            """INSERT INTO word_definitions (word, pos, meaning, example)
               VALUES ($1,$2,$3,$4)
               ON CONFLICT(word) DO UPDATE SET
                   pos=EXCLUDED.pos,
                   meaning=EXCLUDED.meaning,
                   example=EXCLUDED.example""",
            word, d["pos"], d["meaning"], d["example"],
        )
    else:
        await conn.execute(
            """INSERT INTO word_definitions (word, pos, meaning, example)
               VALUES ($1,$2,$3,$4)
               ON CONFLICT(word) DO NOTHING""",
            word, d["pos"], d["meaning"], d["example"],
        )


async def main(overwrite: bool, csv_out: bool) -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("ERROR: DATABASE_URL environment variable is not set.")
    if not _WORDS_FILE.exists():
        sys.exit(f"ERROR: Word list not found at {_WORDS_FILE}")

    words = await load_words(_WORDS_FILE)
    word_set = set(words)

    to_insert = {w: DEFINITIONS[w] for w in word_set if w in DEFINITIONS}
    print(f"Definitions in script : {len(DEFINITIONS)}")
    print(f"Matching game words   : {len(to_insert)}")

    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=3)
    async with pool.acquire() as conn:
        await ensure_table(conn)
        for word, defn in to_insert.items():
            await upsert(conn, word, defn, overwrite)
    await pool.close()

    mode = "overwrite" if overwrite else "insert-missing"
    print(f"Done ({mode}). {len(to_insert)} rows processed.")

    if csv_out:
        csv_path = pathlib.Path(__file__).parent.parent / "data" / "definitions_tz.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["word", "pos", "meaning", "example"])
            writer.writeheader()
            for word in sorted(to_insert):
                writer.writerow({"word": word, **to_insert[word]})
        print(f"CSV written to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed word definitions for T–Z")
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace existing definitions (default: skip)")
    parser.add_argument("--csv", action="store_true",
                        help="Also write a CSV backup to data/definitions_tz.csv")
    args = parser.parse_args()
    asyncio.run(main(overwrite=args.overwrite, csv_out=args.csv))
