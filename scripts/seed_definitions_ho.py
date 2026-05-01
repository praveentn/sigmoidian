#!/usr/bin/env python3
"""
Seed word definitions for H–O words using Claude-generated data.

Usage:
    python scripts/seed_definitions_ho.py                # insert missing only
    python scripts/seed_definitions_ho.py --overwrite    # replace existing
    python scripts/seed_definitions_ho.py --csv          # also dump CSV
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

    # ── H ──────────────────────────────────────────────────────────────────

    "HABIT": {"pos": "noun", "meaning": "a settled or regular tendency that is hard to give up", "example": "She had a habit of tapping her pen when thinking."},
    "HAIKU": {"pos": "noun", "meaning": "a Japanese poem of three lines with five, seven, and five syllables", "example": "He wrote a haiku about the first snow of winter."},
    "HALED": {"pos": "verb", "meaning": "dragged or pulled forcibly to a place", "example": "The suspect was haled before the judge."},
    "HALVE": {"pos": "verb", "meaning": "to divide into two equal parts; to reduce by half", "example": "She halved the recipe since there were only two of them."},
    "HANDY": {"pos": "adjective", "meaning": "convenient and useful; skilled with one's hands", "example": "A Swiss Army knife is a handy tool to carry."},
    "HAPPY": {"pos": "adjective", "meaning": "feeling or showing contentment or pleasure", "example": "She was happy to hear the good news."},
    "HARDY": {"pos": "adjective", "meaning": "capable of enduring difficult conditions; robust and resilient", "example": "Hardy alpine plants survive even the harshest winters."},
    "HAREM": {"pos": "noun", "meaning": "the separate part of a household reserved for women in some Muslim cultures", "example": "The palace's harem was a world unto itself."},
    "HARPS": {"pos": "noun", "meaning": "large triangular musical instruments with strings plucked by hand", "example": "The harps gave the orchestra a celestial quality."},
    "HARPY": {"pos": "noun", "meaning": "a grasping, unpleasant woman; in myth, a fierce winged spirit", "example": "She was no harpy—just someone who knew her worth."},
    "HARSH": {"pos": "adjective", "meaning": "unpleasantly rough or jarring; cruel or severe", "example": "The judge handed down a harsh sentence."},
    "HASTE": {"pos": "noun", "meaning": "excessive speed or urgency; hurry", "example": "She left in such haste she forgot her keys."},
    "HASTY": {"pos": "adjective", "meaning": "done too quickly; acting with excessive speed", "example": "A hasty decision led to months of regret."},
    "HATCH": {"pos": "verb", "meaning": "to emerge from an egg; to devise a plan in secret", "example": "They hatched a scheme to surprise her on her birthday."},
    "HAUNT": {"pos": "verb", "meaning": "to appear as a ghost; to linger in the mind; to visit regularly", "example": "Regret haunted him for years."},
    "HAUTE": {"pos": "adjective", "meaning": "sophisticated and fashionable; of high quality (from French)", "example": "The gala was a celebration of haute couture."},
    "HAVEN": {"pos": "noun", "meaning": "a place of safety or refuge; a sheltered harbour", "example": "The cottage was a haven of peace."},
    "HAVOC": {"pos": "noun", "meaning": "widespread destruction or disorder", "example": "The storm wreaked havoc on the coastal towns."},
    "HAZEL": {"pos": "noun", "meaning": "a shrub with edible nuts; a light brown color", "example": "Her eyes were a warm shade of hazel."},
    "HEART": {"pos": "noun", "meaning": "the organ pumping blood around the body; the centre of emotion; courage", "example": "He put his whole heart into the performance."},
    "HEATH": {"pos": "noun", "meaning": "an area of open uncultivated land covered in heather and shrubs", "example": "They walked across the windswept heath in the morning mist."},
    "HEAVE": {"pos": "verb", "meaning": "to push, pull, or lift with great effort; to throw heavily", "example": "They heaved the sofa up the narrow staircase."},
    "HEAVY": {"pos": "adjective", "meaning": "of great weight; serious or important; oppressive", "example": "The heavy rain flooded the lower roads."},
    "HEDGE": {"pos": "noun", "meaning": "a row of shrubs forming a boundary; to avoid committing to a position", "example": "He hedged his bets by applying to six universities."},
    "HEFTY": {"pos": "adjective", "meaning": "large, heavy, and powerful; substantial in size or amount", "example": "The contractor charged a hefty fee for the work."},
    "HEIST": {"pos": "noun", "meaning": "a robbery or theft, especially a daring one", "example": "The heist was planned for months but fell apart in minutes."},
    "HELIX": {"pos": "noun", "meaning": "a three-dimensional spiral curve, like a corkscrew or DNA strand", "example": "DNA takes the form of a double helix."},
    "HELLO": {"pos": "interjection", "meaning": "a greeting used to begin a conversation", "example": "She picked up the phone and said hello."},
    "HENCE": {"pos": "adverb", "meaning": "as a consequence; for this reason; from this time", "example": "The deadline is three weeks hence."},
    "HENNA": {"pos": "noun", "meaning": "a reddish-brown dye from a plant, used for body decoration", "example": "Her hands were decorated with intricate henna patterns."},
    "HERBS": {"pos": "noun", "meaning": "plants used for flavoring food, making medicine, or in perfumery", "example": "Fresh herbs from the garden transformed the dish."},
    "HERON": {"pos": "noun", "meaning": "a large wading bird with long legs and a long neck", "example": "A heron stood motionless in the shallows."},
    "HINGE": {"pos": "noun", "meaning": "a moveable joint on which a door or lid turns; a central point", "example": "The whole argument hinges on one unproven assumption."},
    "HIPPO": {"pos": "noun", "meaning": "a hippopotamus; a large semi-aquatic African mammal", "example": "A hippo yawned, revealing enormous tusks."},
    "HITCH": {"pos": "noun", "meaning": "a temporary difficulty; a type of knot; to fasten or catch", "example": "The plan went off without a hitch."},
    "HOARD": {"pos": "noun", "meaning": "a stock of money or goods hidden away; to accumulate and store", "example": "Archaeologists discovered a hoard of Roman coins."},
    "HOARY": {"pos": "adjective", "meaning": "greyish-white with age; very old and overused", "example": "He told the same hoary jokes at every gathering."},
    "HOBBY": {"pos": "noun", "meaning": "an activity done regularly for pleasure in one's spare time", "example": "Birdwatching became his favourite hobby in retirement."},
    "HOIST": {"pos": "verb", "meaning": "to raise or lift using ropes or a mechanical device", "example": "They hoisted the flag at dawn."},
    "HOLLY": {"pos": "noun", "meaning": "an evergreen shrub with prickly dark leaves and red berries", "example": "Sprigs of holly decorated the mantelpiece at Christmas."},
    "HONEY": {"pos": "noun", "meaning": "a sweet sticky fluid made by bees; a term of endearment", "example": "She stirred a spoonful of honey into her tea."},
    "HONOR": {"pos": "noun", "meaning": "high respect or great esteem; a privilege; to fulfill an obligation", "example": "It was an honor to be included in the shortlist."},
    "HORDE": {"pos": "noun", "meaning": "a large group of people; a vast moving crowd", "example": "Hordes of tourists crowded the narrow streets."},
    "HORSE": {"pos": "noun", "meaning": "a large four-legged mammal used for riding and work", "example": "She rode the horse across the open field."},
    "HOTEL": {"pos": "noun", "meaning": "an establishment providing paid accommodation and meals", "example": "They checked into the hotel late in the evening."},
    "HOUND": {"pos": "noun", "meaning": "a dog used for hunting; to pursue relentlessly", "example": "The press hounded him wherever he went."},
    "HOUSE": {"pos": "noun", "meaning": "a building for human habitation; a household; to provide with shelter", "example": "The gallery houses one of the finest art collections in Europe."},
    "HOVEL": {"pos": "noun", "meaning": "a small, squalid, or poorly built dwelling", "example": "They had risen from a hovel to a mansion in one generation."},
    "HOVER": {"pos": "verb", "meaning": "to remain suspended in one place in the air; to wait close by", "example": "A hawk hovered above the field searching for prey."},
    "HUMAN": {"pos": "noun", "meaning": "a member of the species Homo sapiens; of or relating to people", "example": "To err is human, to forgive divine."},
    "HUMID": {"pos": "adjective", "meaning": "marked by a high level of moisture in the air", "example": "The jungle was unbearably hot and humid."},
    "HUMOR": {"pos": "noun", "meaning": "the quality of being funny; mood or temperament; to comply with", "example": "He had a dry sense of humor that people often missed."},
    "HUNCH": {"pos": "noun", "meaning": "a feeling or guess based on intuition rather than evidence", "example": "I had a hunch something was wrong before the call came."},
    "HUNKY": {"pos": "adjective", "meaning": "attractively large and muscular (informal)", "example": "The hunky lifeguard attracted a lot of attention."},
    "HURRY": {"pos": "verb", "meaning": "to move or do something with great speed; to rush", "example": "We'll have to hurry if we want to catch the train."},
    "HUSKY": {"pos": "adjective", "meaning": "large and strong; having a slightly hoarse voice; a sled dog breed", "example": "His husky voice was perfect for radio broadcasting."},
    "HUTCH": {"pos": "noun", "meaning": "a box or cage for keeping rabbits; a piece of furniture with shelves", "example": "She kept two rabbits in a hutch in the garden."},
    "HYDRA": {"pos": "noun", "meaning": "in Greek myth, a serpent with many heads; a persistent problem", "example": "The scandal proved a hydra—cutting one head just grew another."},
    "HYENA": {"pos": "noun", "meaning": "a dog-like carnivorous African mammal with a distinctive laughing cry", "example": "A hyena's laughter echoed across the savannah."},
    "HYMNS": {"pos": "noun", "meaning": "religious songs of praise sung in worship", "example": "The congregation sang traditional hymns at the service."},
    "HYPED": {"pos": "adjective", "meaning": "promoted or publicized intensively; excited or stimulated", "example": "The product was so hyped that disappointment was inevitable."},
    "HYPER": {"pos": "adjective", "meaning": "overly excited or energetic (informal)", "example": "The children were hyper after the birthday party."},

    # ── I ──────────────────────────────────────────────────────────────────

    "ICHOR": {"pos": "noun", "meaning": "the fluid said to flow in the veins of gods; a watery wound discharge", "example": "The myth described ichor rather than blood in divine veins."},
    "ICING": {"pos": "noun", "meaning": "a sweet coating on cakes; in sport, sending the puck down the rink illegally", "example": "She spread pink icing over the birthday cake."},
    "ICONS": {"pos": "noun", "meaning": "symbols representing something; people or things widely admired", "example": "The desktop icons made navigating the software easy."},
    "IDEAL": {"pos": "noun", "meaning": "a standard of perfection; a principle worth aspiring to", "example": "She held fast to her ideals even when it cost her."},
    "IDIOM": {"pos": "noun", "meaning": "a phrase whose meaning is not predictable from its words; a style", "example": "'Break a leg' is a theatrical idiom meaning good luck."},
    "IDIOT": {"pos": "noun", "meaning": "a stupid person; a person of low intelligence", "example": "He felt like an idiot for forgetting such an obvious thing."},
    "IDYLL": {"pos": "noun", "meaning": "a happy and peaceful time or situation; a short pastoral poem", "example": "Their summer in the countryside was a perfect idyll."},
    "IGLOO": {"pos": "noun", "meaning": "a dome-shaped shelter built from blocks of snow by Inuit people", "example": "The Inuit constructed an igloo in less than an hour."},
    "IMAGE": {"pos": "noun", "meaning": "a visual representation; the impression a person or brand projects", "example": "The company worked hard to improve its public image."},
    "IMBUE": {"pos": "verb", "meaning": "to inspire or permeate with a feeling or quality", "example": "Her writing is imbued with warmth and compassion."},
    "IMPEL": {"pos": "verb", "meaning": "to drive or urge forward; to force to do something", "example": "A sense of duty impelled him to speak up."},
    "IMPLY": {"pos": "verb", "meaning": "to suggest without stating directly; to indicate indirectly", "example": "His silence implied agreement."},
    "INANE": {"pos": "adjective", "meaning": "lacking sense or meaning; silly and pointless", "example": "The conversation was painfully inane."},
    "INBOX": {"pos": "noun", "meaning": "a tray for incoming documents; a folder for incoming emails", "example": "She returned from holiday to find four hundred unread emails in her inbox."},
    "INCUR": {"pos": "verb", "meaning": "to become subject to something unpleasant as a result of one's actions", "example": "He incurred a heavy fine for late filing."},
    "INDEX": {"pos": "noun", "meaning": "an alphabetical list; a pointer or indicator; a measure of change", "example": "Look up the topic in the index at the back of the book."},
    "INDIE": {"pos": "adjective", "meaning": "independent of a major company; relating to small-scale creative work", "example": "She preferred indie films over big studio productions."},
    "INEPT": {"pos": "adjective", "meaning": "lacking skill; performing badly; clumsy", "example": "The new recruit was inept but willing to learn."},
    "INERT": {"pos": "adjective", "meaning": "lacking the ability to move or act; chemically inactive", "example": "Argon is an inert gas that does not react with other elements."},
    "INFER": {"pos": "verb", "meaning": "to conclude from evidence rather than from explicit statements", "example": "From the clues, she inferred that he had left hours earlier."},
    "INGOT": {"pos": "noun", "meaning": "a rectangular block of metal, especially gold or silver", "example": "Gold ingots were stacked in the vault."},
    "INLAY": {"pos": "noun", "meaning": "a design set into a surface; to embed material decoratively", "example": "The desk had an intricate inlay of ivory and ebony."},
    "INLET": {"pos": "noun", "meaning": "a small arm of the sea or a lake; an opening or entry point", "example": "The boat sheltered in a quiet inlet overnight."},
    "INNER": {"pos": "adjective", "meaning": "situated inside or further in; relating to the mind or spirit", "example": "She needed time to find her inner calm."},
    "INPUT": {"pos": "noun", "meaning": "what is put in; contributions of ideas or resources; data fed into a computer", "example": "The team valued her creative input."},
    "INTER": {"pos": "verb", "meaning": "to bury a dead body in a grave or tomb", "example": "He was interred with full military honors."},
    "INTRO": {"pos": "noun", "meaning": "an introduction; an opening passage of music or speech (informal)", "example": "The guitarist played a long intro before the vocals came in."},
    "INURE": {"pos": "verb", "meaning": "to accustom someone to something unpleasant; to harden through practice", "example": "Years of criticism had inured her to harsh reviews."},
    "IRATE": {"pos": "adjective", "meaning": "feeling or characterized by great anger", "example": "An irate customer demanded to speak to the manager."},
    "IRONY": {"pos": "noun", "meaning": "the expression of meaning opposite to what is literally said; a twist of fate", "example": "The irony was that the fire station burned down first."},
    "ISLET": {"pos": "noun", "meaning": "a small island; clusters of cells in the pancreas", "example": "They moored beside a tiny wooded islet."},
    "ISSUE": {"pos": "noun", "meaning": "an important topic for discussion; an edition of a publication; to supply", "example": "The magazine's latest issue sold out within hours."},
    "ITCHY": {"pos": "adjective", "meaning": "having or causing an itch; restless and impatient", "example": "He had itchy feet and was always planning the next trip."},
    "IVORY": {"pos": "noun", "meaning": "a hard white material from elephant tusks; a creamy white color", "example": "Trade in ivory has been banned internationally."},

    # ── J ──────────────────────────────────────────────────────────────────

    "JADED": {"pos": "adjective", "meaning": "tired and bored, having had too much of something", "example": "Even the most jaded critic praised the performance."},
    "JAMMY": {"pos": "adjective", "meaning": "lucky, especially in an undeserved way (British informal)", "example": "That was a jammy shot—he didn't even aim."},
    "JAUNT": {"pos": "noun", "meaning": "a short journey taken for pleasure", "example": "They took a jaunt to the coast for the afternoon."},
    "JAZZY": {"pos": "adjective", "meaning": "bright and showy; having the quality of jazz music", "example": "She wore a jazzy patterned scarf to brighten her outfit."},
    "JEANS": {"pos": "noun", "meaning": "trousers made of denim, originally designed as work wear", "example": "She wore jeans and a white shirt to the casual dinner."},
    "JEERS": {"pos": "noun", "meaning": "mocking or scornful shouts of disapproval", "example": "The decision was met with jeers from the audience."},
    "JELLY": {"pos": "noun", "meaning": "a fruit-flavored spread; a gelatinous dessert; a translucent substance", "example": "She spread peanut butter and jelly on the toast."},
    "JERKY": {"pos": "adjective", "meaning": "moving with sudden jolts; dried cured strips of meat", "example": "The old bus ride was jerky and uncomfortable."},
    "JETTY": {"pos": "noun", "meaning": "a landing pier or dock extending into water", "example": "They sat on the jetty and dangled their feet in the sea."},
    "JEWEL": {"pos": "noun", "meaning": "a precious stone; a treasured person or thing", "example": "The museum's jewel was a flawless blue diamond."},
    "JIFFY": {"pos": "noun", "meaning": "a very short time (informal); an instant", "example": "I'll be back in a jiffy—just grabbing my coat."},
    "JIHAD": {"pos": "noun", "meaning": "a Muslim's spiritual struggle; a holy war declared in Islam", "example": "Scholars debate the inner spiritual meaning of jihad."},
    "JOINT": {"pos": "noun", "meaning": "a place where things are joined; a shared space; a cannabis cigarette (informal)", "example": "The knee joint is one of the most complex in the body."},
    "JOKER": {"pos": "noun", "meaning": "a person who makes jokes; a wild card in a deck of cards", "example": "He was the joker of the group, always lightening the mood."},
    "JOLLY": {"pos": "adjective", "meaning": "cheerful and full of good humor; to encourage in a friendly way", "example": "The host kept everyone in a jolly mood all evening."},
    "JOULE": {"pos": "noun", "meaning": "the SI unit of energy or work, equal to one newton-meter", "example": "The energy released was measured in joules."},
    "JOUST": {"pos": "verb", "meaning": "to compete in a medieval tournament on horseback; to compete for", "example": "Knights jousted for the queen's favor."},
    "JUDGE": {"pos": "noun", "meaning": "a person who decides the outcome of a competition or legal case", "example": "The judge sentenced him to two years in prison."},
    "JUICE": {"pos": "noun", "meaning": "the liquid extracted from fruit or vegetables; fuel or electricity (informal)", "example": "She squeezed fresh orange juice every morning."},
    "JUICY": {"pos": "adjective", "meaning": "full of juice; interestingly scandalous or entertaining", "example": "She leaned in to share the juicy gossip."},
    "JULEP": {"pos": "noun", "meaning": "a sweet drink made with bourbon, sugar, and mint; a sweet syrup", "example": "A mint julep is the signature drink of the Kentucky Derby."},
    "JUMBO": {"pos": "adjective", "meaning": "very large; much bigger than usual", "example": "She ordered a jumbo portion of fries."},
    "JUMPY": {"pos": "adjective", "meaning": "anxious and nervous; tending to startle easily", "example": "He had been jumpy since the incident last week."},
    "JUNTA": {"pos": "noun", "meaning": "a military or political group ruling after seizing power", "example": "The military junta suspended all civil liberties."},
    "JUROR": {"pos": "noun", "meaning": "a member of a jury in a court of law or competition", "example": "Each juror listened carefully to the closing arguments."},

    # ── K ──────────────────────────────────────────────────────────────────

    "KAPOK": {"pos": "noun", "meaning": "a silky fiber from the kapok tree used to stuff cushions and life jackets", "example": "Old life jackets were often filled with kapok."},
    "KAPUT": {"pos": "adjective", "meaning": "broken or no longer working (informal); ruined", "example": "The old washing machine is completely kaput."},
    "KARMA": {"pos": "noun", "meaning": "the sum of one's actions affecting future fate; destiny; cosmic justice", "example": "She believed that karma would eventually catch up with him."},
    "KAYAK": {"pos": "noun", "meaning": "a narrow covered canoe of a type traditionally used by Inuit people", "example": "They explored the sea caves by kayak."},
    "KAZOO": {"pos": "noun", "meaning": "a simple toy musical instrument you hum into to produce a buzzing sound", "example": "The children paraded down the street playing kazoos."},
    "KEBAB": {"pos": "noun", "meaning": "pieces of meat and vegetables cooked on a skewer or spit", "example": "They ordered lamb kebabs from the street vendor."},
    "KHAKI": {"pos": "adjective", "meaning": "a dull brownish-yellow color; a strong fabric of this color used for uniforms", "example": "The soldiers wore khaki uniforms in the desert."},
    "KIDDO": {"pos": "noun", "meaning": "an affectionate or informal term for a child or younger person", "example": "Listen up, kiddo—I'll only say this once."},
    "KILNS": {"pos": "noun", "meaning": "furnaces or ovens for baking clay, drying bricks, or burning lime", "example": "The pottery was fired in wood-burning kilns."},
    "KILOS": {"pos": "noun", "meaning": "kilograms; units of weight equal to one thousand grams", "example": "She lost five kilos after changing her diet."},
    "KILTS": {"pos": "noun", "meaning": "knee-length pleated tartan skirts worn as part of Scottish dress", "example": "The men wore kilts to the Highland games."},
    "KINGS": {"pos": "noun", "meaning": "male monarchs who rule a kingdom; playing cards of the highest rank", "example": "The tapestry depicted the kings of the ancient realm."},
    "KIOSK": {"pos": "noun", "meaning": "a small open-fronted structure selling newspapers, food, or tickets", "example": "She bought a coffee from the kiosk on the platform."},
    "KITTY": {"pos": "noun", "meaning": "a small cat; a fund of money from which players draw; a pool of money", "example": "Everyone threw ten pounds into the kitty for the party."},
    "KIWIS": {"pos": "noun", "meaning": "small flightless New Zealand birds; the tangy green-fleshed fruit", "example": "She sliced kiwis for the fruit salad."},
    "KLUTZ": {"pos": "noun", "meaning": "a clumsy or accident-prone person (informal)", "example": "He was a complete klutz who knocked something over daily."},
    "KNACK": {"pos": "noun", "meaning": "a special skill or talent; a clever way of doing something", "example": "She had a knack for making strangers feel at ease."},
    "KNAVE": {"pos": "noun", "meaning": "a dishonest or deceitful man; the Jack in a deck of cards", "example": "The knave tricked the merchant out of his savings."},
    "KNEAD": {"pos": "verb", "meaning": "to work dough or clay by pressing and folding; to massage", "example": "She kneaded the bread dough until it was smooth and elastic."},
    "KNEEL": {"pos": "verb", "meaning": "to go down or rest on one's knee or knees", "example": "He knelt down to help the child."},
    "KNELL": {"pos": "noun", "meaning": "the sound of a bell rung solemnly for a death or funeral", "example": "The church bell tolled a slow knell."},
    "KNIFE": {"pos": "noun", "meaning": "a cutting instrument with a sharp blade; to stab with a knife", "example": "She sharpened the knife before slicing the vegetables."},
    "KNOCK": {"pos": "verb", "meaning": "to strike a surface with a sharp blow; to collide; to criticize", "example": "He knocked on the door and waited."},
    "KNOLL": {"pos": "noun", "meaning": "a small hill or rounded mound", "example": "They climbed the grassy knoll for a view of the valley."},
    "KNOTS": {"pos": "noun", "meaning": "tight interlacings of rope; units of speed equal to one nautical mile per hour", "example": "The ship cruised at fifteen knots."},
    "KNOWN": {"pos": "adjective", "meaning": "recognized; familiar; acknowledged as a fact", "example": "He was a known expert in the field."},
    "KOALA": {"pos": "noun", "meaning": "an Australian tree-climbing marsupial with large ears and a stout body", "example": "The koala clung to the eucalyptus branch and dozed."},
    "KUDOS": {"pos": "noun", "meaning": "praise and honor for an achievement; prestige", "example": "Kudos to the team for finishing ahead of schedule."},

    # ── L ──────────────────────────────────────────────────────────────────

    "LABEL": {"pos": "noun", "meaning": "a piece of paper attached to an object giving information; to classify", "example": "Read the label carefully before taking any medication."},
    "LABOR": {"pos": "noun", "meaning": "work, especially physical; the workforce; the process of childbirth", "example": "The labor of rebuilding the town took years."},
    "LADLE": {"pos": "noun", "meaning": "a deep long-handled spoon for serving soup or stew", "example": "She ladled the soup into the bowls."},
    "LAGER": {"pos": "noun", "meaning": "a type of light effervescent beer, cold-fermented and stored", "example": "He ordered a cold lager at the bar."},
    "LANCE": {"pos": "noun", "meaning": "a long weapon with a wooden shaft and pointed metal head; to pierce", "example": "The knight lowered his lance and charged."},
    "LANKY": {"pos": "adjective", "meaning": "ungracefully tall and thin", "example": "The lanky teenager struggled to find clothes that fit."},
    "LAPEL": {"pos": "noun", "meaning": "the folded flap of a jacket or coat below the collar", "example": "She pinned a small brooch to her lapel."},
    "LAPSE": {"pos": "noun", "meaning": "a brief failure of concentration or memory; an interval of time", "example": "A momentary lapse of judgment cost him the match."},
    "LARCH": {"pos": "noun", "meaning": "a deciduous coniferous tree with needle leaves and small cones", "example": "Larches turned golden in October."},
    "LARGE": {"pos": "adjective", "meaning": "of considerable size or extent; above average", "example": "A large crowd gathered outside the courthouse."},
    "LARVA": {"pos": "noun", "meaning": "the active immature form of an insect after hatching from an egg", "example": "The caterpillar is the larva of a butterfly."},
    "LASER": {"pos": "noun", "meaning": "a device emitting an intense narrow beam of coherent light", "example": "Surgeons used a laser to correct her vision."},
    "LASSO": {"pos": "noun", "meaning": "a loop of rope used to catch cattle or horses", "example": "The cowboy threw the lasso in a wide arc."},
    "LATCH": {"pos": "noun", "meaning": "a bar that falls into a catch to fasten a door; to attach or cling to", "example": "She latched onto the idea immediately."},
    "LAUGH": {"pos": "verb", "meaning": "to make sounds expressing amusement; to find something funny", "example": "He laughed until his sides hurt."},
    "LAYER": {"pos": "noun", "meaning": "a sheet or thickness of material, typically one of several; to arrange in layers", "example": "She applied a second layer of paint to the wall."},
    "LEACH": {"pos": "verb", "meaning": "to drain from soil by the action of water; to drain away gradually", "example": "Chemicals leached from the dump into the groundwater."},
    "LEAKY": {"pos": "adjective", "meaning": "having holes through which liquid or gas can pass", "example": "The leaky tap kept her awake all night."},
    "LEARN": {"pos": "verb", "meaning": "to gain knowledge or skill through study or experience", "example": "It's never too late to learn something new."},
    "LEASE": {"pos": "noun", "meaning": "a contract granting use of property for a specified time", "example": "They signed a two-year lease on the apartment."},
    "LEASH": {"pos": "noun", "meaning": "a strap attached to an animal's collar to control it", "example": "She kept the dog on a short leash near the traffic."},
    "LEDGE": {"pos": "noun", "meaning": "a narrow horizontal surface projecting from a wall or cliff", "example": "A pigeon perched on the window ledge."},
    "LEECH": {"pos": "noun", "meaning": "a blood-sucking worm; a person who exploits others without giving back", "example": "He was a leech, always borrowing money he never repaid."},
    "LEGAL": {"pos": "adjective", "meaning": "permitted by law; relating to the law", "example": "She sought legal advice before signing."},
    "LEGIT": {"pos": "adjective", "meaning": "legitimate; conforming to the rules; genuine (informal)", "example": "Is this deal legit or should I be worried?"},
    "LEMON": {"pos": "noun", "meaning": "a yellow citrus fruit with sour juice; a defective product (informal)", "example": "She squeezed a lemon over the grilled fish."},
    "LEMUR": {"pos": "noun", "meaning": "a tree-climbing primate with a long tail, native to Madagascar", "example": "Ring-tailed lemurs sunbathed in the morning sun."},
    "LEVEE": {"pos": "noun", "meaning": "an embankment built to prevent river flooding; a landing place", "example": "The levee held through the worst of the flood season."},
    "LEVEL": {"pos": "adjective", "meaning": "flat and horizontal; equal; calm and steady", "example": "She needed a level surface to lay the tiles."},
    "LEVER": {"pos": "noun", "meaning": "a rigid bar pivoted on a fulcrum to move a load; to move with a lever", "example": "He used a crowbar as a lever to shift the rock."},
    "LIBEL": {"pos": "noun", "meaning": "a published false statement damaging to a person's reputation", "example": "She sued the newspaper for libel."},
    "LIGHT": {"pos": "noun", "meaning": "electromagnetic radiation visible to the eye; illumination; not heavy", "example": "She preferred light reading on holiday."},
    "LILAC": {"pos": "noun", "meaning": "a shrub with fragrant purple or white flowers; a pale mauve color", "example": "The garden was filled with the scent of lilac in spring."},
    "LIMBO": {"pos": "noun", "meaning": "an uncertain state of waiting; a dance in which dancers pass under a bar", "example": "The project was stuck in limbo awaiting approval."},
    "LINEN": {"pos": "noun", "meaning": "a cloth woven from flax; household items made from it", "example": "The table was set with crisp white linen."},
    "LINER": {"pos": "noun", "meaning": "a large passenger ship; something used to line the inside of something", "example": "The ocean liner departed at midnight."},
    "LINGO": {"pos": "noun", "meaning": "a foreign language; the vocabulary of a particular field (informal)", "example": "She picked up the local lingo within a week."},
    "LIPID": {"pos": "noun", "meaning": "a group of biological molecules including fats, waxes, and oils", "example": "Lipids are essential components of cell membranes."},
    "LITHE": {"pos": "adjective", "meaning": "thin and supple; moving with graceful ease", "example": "The gymnast was lithe and incredibly flexible."},
    "LIVER": {"pos": "noun", "meaning": "the large organ that processes nutrients and detoxifies the blood", "example": "Alcohol puts significant strain on the liver."},
    "LIVID": {"pos": "adjective", "meaning": "furiously angry; having a bluish discoloration from a bruise", "example": "She was absolutely livid when she heard what had happened."},
    "LLAMA": {"pos": "noun", "meaning": "a domesticated South American animal related to the camel, used for wool and transport", "example": "The llama spat at the tourist who got too close."},
    "LOBBY": {"pos": "noun", "meaning": "an entrance hall; to seek to influence politicians; a group doing so", "example": "The pharmaceutical lobby spent millions on the campaign."},
    "LOCAL": {"pos": "adjective", "meaning": "belonging to or relating to a particular area", "example": "They always shopped at the local market."},
    "LODGE": {"pos": "noun", "meaning": "a small house in the grounds of an estate; a beaver's lair; to formally register", "example": "She lodged a complaint with the council."},
    "LOFTY": {"pos": "adjective", "meaning": "of great height; noble and ambitious; arrogantly superior", "example": "He had lofty ambitions that he mostly achieved."},
    "LOGIC": {"pos": "noun", "meaning": "reasoning conducted according to strict principles of validity", "example": "Her argument was flawless in its logic."},
    "LONER": {"pos": "noun", "meaning": "a person who prefers to be alone; one who avoids company", "example": "He was a loner who preferred books to parties."},
    "LOOSE": {"pos": "adjective", "meaning": "not firmly fixed; free; not tight; not precise", "example": "The bolt had worked itself loose over time."},
    "LORRY": {"pos": "noun", "meaning": "a large heavy goods vehicle; a truck (British English)", "example": "The lorry blocked the narrow lane for twenty minutes."},
    "LOSER": {"pos": "noun", "meaning": "a person who loses; someone seen as a failure (informal)", "example": "He called himself a loser after the defeat, but the team disagreed."},
    "LOTUS": {"pos": "noun", "meaning": "a water lily with large floating leaves; a symbol of enlightenment", "example": "The lotus bloomed on the still surface of the pond."},
    "LOUSE": {"pos": "noun", "meaning": "a small parasitic insect; a contemptible person", "example": "A louse of a manager who took all the credit."},
    "LOUSY": {"pos": "adjective", "meaning": "very poor or bad; infested with lice (informal)", "example": "The weather was lousy for the entire holiday."},
    "LOYAL": {"pos": "adjective", "meaning": "giving firm and constant support to a person, cause, or institution", "example": "She was a loyal friend through every crisis."},
    "LUCID": {"pos": "adjective", "meaning": "expressed clearly; easy to understand; thinking clearly", "example": "She gave a lucid explanation of a complex topic."},
    "LUCKY": {"pos": "adjective", "meaning": "having or bringing good luck; fortunate", "example": "He was lucky to escape without injury."},
    "LUCRE": {"pos": "noun", "meaning": "money, especially when obtained by dishonest means", "example": "He was not motivated by filthy lucre but by principle."},
    "LUMPY": {"pos": "adjective", "meaning": "full of lumps; not smooth", "example": "She stirred the sauce until it was no longer lumpy."},
    "LUNAR": {"pos": "adjective", "meaning": "relating to the moon", "example": "The lunar landing was watched by millions around the world."},
    "LUNCH": {"pos": "noun", "meaning": "a meal eaten in the middle of the day", "example": "They met for lunch at the Italian place on the corner."},
    "LUNGE": {"pos": "verb", "meaning": "to make a sudden forward thrust; to move suddenly towards", "example": "He lunged for the ball but couldn't reach it."},
    "LUPUS": {"pos": "noun", "meaning": "an autoimmune disease causing inflammation in various parts of the body", "example": "She was diagnosed with lupus after months of unexplained symptoms."},
    "LURCH": {"pos": "verb", "meaning": "to make an abrupt unsteady movement; to stagger", "example": "The bus lurched forward as the driver braked sharply."},
    "LURID": {"pos": "adjective", "meaning": "unpleasantly vivid; presented in a sensationalized way", "example": "The tabloid ran lurid details of the scandal."},
    "LUSTY": {"pos": "adjective", "meaning": "healthy and strong; full of vigor; enthusiastic", "example": "The baby let out a lusty cry."},
    "LYMPH": {"pos": "noun", "meaning": "a colorless fluid containing white blood cells that bathes tissues", "example": "Swollen lymph nodes can indicate infection."},
    "LYNCH": {"pos": "verb", "meaning": "to kill illegally by mob action, typically by hanging", "example": "History records many victims of lynch mobs in the American South."},
    "LYRIC": {"pos": "noun", "meaning": "the words of a song; a short poem expressing personal emotion", "example": "She knew every lyric of the song by heart."},

    # ── M ──────────────────────────────────────────────────────────────────

    "MACAW": {"pos": "noun", "meaning": "a large, long-tailed parrot with bright plumage from Central and South America", "example": "A scarlet macaw perched in the jungle canopy."},
    "MACHO": {"pos": "adjective", "meaning": "aggressively asserting one's masculinity; showing off toughness", "example": "He played up the macho image but was gentle at home."},
    "MACRO": {"pos": "noun", "meaning": "a single instruction that expands into a set of actions; large-scale", "example": "The programmer set up a macro to automate the repetitive task."},
    "MADAM": {"pos": "noun", "meaning": "a polite title for a woman; the owner of a brothel", "example": "May I help you, madam?"},
    "MAFIA": {"pos": "noun", "meaning": "an organized crime syndicate; any close-knit group using underhanded methods", "example": "The corruption trial exposed links to the local mafia."},
    "MAGIC": {"pos": "noun", "meaning": "the use of supernatural forces; conjuring tricks; a wonderful quality", "example": "There was real magic in the way she told the story."},
    "MAGMA": {"pos": "noun", "meaning": "molten rock material under the earth's crust", "example": "Magma erupted from the volcano and cooled into new land."},
    "MAJOR": {"pos": "adjective", "meaning": "important, serious, or significant; greater in rank", "example": "This is a major development in the investigation."},
    "MANGA": {"pos": "noun", "meaning": "Japanese comic books and graphic novels", "example": "She collected manga and read every volume of the series."},
    "MANIA": {"pos": "noun", "meaning": "mental illness with periods of excitement; an obsessive enthusiasm", "example": "Disco mania swept through the 1970s."},
    "MANIC": {"pos": "adjective", "meaning": "showing wild excitement or energy; relating to mania", "example": "The pace at the trading floor was completely manic."},
    "MANOR": {"pos": "noun", "meaning": "a large country house with land; a feudal lord's estate", "example": "The manor house had stood for four centuries."},
    "MAPLE": {"pos": "noun", "meaning": "a tree with distinctive lobed leaves; its sweet sap used to make syrup", "example": "Maple syrup dripped over the warm pancakes."},
    "MARCH": {"pos": "verb", "meaning": "to walk with a regular measured tread; to proceed steadily", "example": "The protesters marched through the city centre."},
    "MARSH": {"pos": "noun", "meaning": "low-lying land that is flooded in wet seasons; a swamp", "example": "Rare wading birds nested in the coastal marsh."},
    "MASON": {"pos": "noun", "meaning": "a person who builds with stone or brick; a Freemason", "example": "A skilled mason can lay a thousand bricks a day."},
    "MATCH": {"pos": "noun", "meaning": "a contest between two sides; something equal to another; a stick for lighting fire", "example": "The final match of the season drew a record crowd."},
    "MAUVE": {"pos": "noun", "meaning": "a pale purple color", "example": "She chose a mauve blouse for the spring wedding."},
    "MAXIM": {"pos": "noun", "meaning": "a short statement expressing a general truth or rule of conduct", "example": "'Prepare for the worst' was her guiding maxim."},
    "MAYBE": {"pos": "adverb", "meaning": "perhaps; possibly", "example": "Maybe we should leave early to avoid the traffic."},
    "MAYOR": {"pos": "noun", "meaning": "the elected head of a city or town council", "example": "The mayor opened the new library with a ribbon-cutting ceremony."},
    "MEDAL": {"pos": "noun", "meaning": "a metal disc given as an award for achievement or bravery", "example": "She trained four years to win that gold medal."},
    "MEDIA": {"pos": "noun", "meaning": "the main means of mass communication; the press and broadcasters", "example": "The media covered the trial extensively."},
    "MELEE": {"pos": "noun", "meaning": "a confused mixture of people; a noisy and chaotic fight or crowd", "example": "A melee broke out near the stadium after the match."},
    "MELON": {"pos": "noun", "meaning": "a large round fruit with sweet juicy flesh", "example": "She served chilled melon as a starter on the hot day."},
    "MERCY": {"pos": "noun", "meaning": "compassionate treatment of someone in one's power; leniency", "example": "She begged for mercy and was granted a lighter sentence."},
    "MERGE": {"pos": "verb", "meaning": "to combine or join to form a single entity", "example": "The two companies merged to create one of the biggest in the sector."},
    "MERIT": {"pos": "noun", "meaning": "the quality of being good and deserving praise; a point in favor", "example": "Promotion was based entirely on merit."},
    "MERRY": {"pos": "adjective", "meaning": "cheerful and lively; slightly drunk (informal)", "example": "Everyone was merry by the end of the Christmas dinner."},
    "MESSY": {"pos": "adjective", "meaning": "untidy or dirty; causing difficulty or distress", "example": "The kitchen was in a messy state after cooking."},
    "METAL": {"pos": "noun", "meaning": "a hard shiny material such as iron, gold, or silver; heavy rock music", "example": "The sculpture was cast in polished metal."},
    "METRO": {"pos": "noun", "meaning": "an underground railway system in a city", "example": "She took the metro across town to avoid the traffic."},
    "MIGHT": {"pos": "noun", "meaning": "great strength or power; past tense of may", "example": "They fought with all their might."},
    "MIMIC": {"pos": "verb", "meaning": "to imitate someone's voice, actions, or appearance", "example": "The comedian could mimic any accent perfectly."},
    "MINCE": {"pos": "verb", "meaning": "to chop food into very small pieces; to walk with tiny delicate steps", "example": "She minced the garlic finely before frying it."},
    "MINER": {"pos": "noun", "meaning": "a person who works in a mine extracting coal or minerals", "example": "Generations of miners had worked the same seam."},
    "MINOR": {"pos": "adjective", "meaning": "lesser in importance or seriousness; a person under the legal age", "example": "These are minor issues that can be fixed quickly."},
    "MIRTH": {"pos": "noun", "meaning": "amusement expressed in laughter; great merriment", "example": "The joke provoked much mirth around the table."},
    "MISER": {"pos": "noun", "meaning": "a person who hoards wealth and hates spending it", "example": "The old miser refused to heat his house in winter."},
    "MISTY": {"pos": "adjective", "meaning": "full of mist; indistinct; sentimental", "example": "A misty morning softened the view of the hills."},
    "MODEL": {"pos": "noun", "meaning": "a thing used as an example; a person who poses for art; to display clothes", "example": "She worked as a model while studying architecture."},
    "MODEM": {"pos": "noun", "meaning": "a device connecting a computer to the internet via a phone line", "example": "The old modem took minutes to connect."},
    "MOGUL": {"pos": "noun", "meaning": "an important or powerful person; a mound on a ski slope", "example": "A media mogul controlled half the country's newspapers."},
    "MOIST": {"pos": "adjective", "meaning": "slightly wet; damp", "example": "The soil should be kept moist but not waterlogged."},
    "MOLAR": {"pos": "noun", "meaning": "a large grinding tooth at the back of the mouth", "example": "She had her lower molar extracted."},
    "MONEY": {"pos": "noun", "meaning": "a medium of exchange in the form of coins and banknotes", "example": "Money doesn't buy happiness, but it helps."},
    "MONKS": {"pos": "noun", "meaning": "members of a religious community living under vows of poverty and obedience", "example": "Monks rose before dawn for morning prayer."},
    "MONTH": {"pos": "noun", "meaning": "any of the twelve periods into which the year is divided", "example": "The project took six months longer than planned."},
    "MOODY": {"pos": "adjective", "meaning": "having changeable moods; gloomy and sullen", "example": "She was moody for days after the argument."},
    "MOOSE": {"pos": "noun", "meaning": "the largest member of the deer family, native to North America and Eurasia", "example": "A moose stood knee-deep in the lake at dusk."},
    "MORAL": {"pos": "adjective", "meaning": "concerned with right and wrong behavior; virtuous", "example": "He faced a genuine moral dilemma."},
    "MORON": {"pos": "noun", "meaning": "a stupid person (informal, offensive)", "example": "He felt like a complete moron after the mistake."},
    "MORPH": {"pos": "verb", "meaning": "to gradually change from one form to another", "example": "The protest movement morphed into a political party."},
    "MOTEL": {"pos": "noun", "meaning": "a roadside hotel designed for motorists with direct room access", "example": "They pulled off the highway and checked into a motel."},
    "MOTIF": {"pos": "noun", "meaning": "a recurring element in a design or work of art; a theme", "example": "The floral motif ran through the whole collection."},
    "MOTOR": {"pos": "noun", "meaning": "a machine that produces motion, especially an electric engine", "example": "The motor hummed quietly in the background."},
    "MOTTO": {"pos": "noun", "meaning": "a short sentence or phrase expressing a guiding principle", "example": "The school motto was 'Learn and Serve'."},
    "MOUND": {"pos": "noun", "meaning": "a rounded mass of earth or stones; a pitcher's raised platform in baseball", "example": "She found arrowheads on the ancient burial mound."},
    "MOUNT": {"pos": "verb", "meaning": "to climb; to get onto a horse; to fix in position; a mountain", "example": "Tension mounted as the deadline approached."},
    "MOURN": {"pos": "verb", "meaning": "to feel or express deep sorrow for a death or loss", "example": "The whole nation mourned the loss of the beloved leader."},
    "MOUSE": {"pos": "noun", "meaning": "a small rodent; a computer pointing device", "example": "She clicked the mouse and the file opened."},
    "MOUTH": {"pos": "noun", "meaning": "the opening in the face used for eating and speaking; the outlet of a river", "example": "The river's mouth spread wide across the delta."},
    "MOVIE": {"pos": "noun", "meaning": "a film; a motion picture shown in a cinema or on a screen", "example": "They watched a movie and ate popcorn on the sofa."},
    "MUCUS": {"pos": "noun", "meaning": "a slippery secretion produced by mucous membranes to lubricate and protect", "example": "Excess mucus is a common symptom of a cold."},
    "MUDDY": {"pos": "adjective", "meaning": "covered in or resembling mud; not clear or bright", "example": "The children came home with muddy boots."},
    "MULCH": {"pos": "noun", "meaning": "a covering of organic matter spread over soil to retain moisture", "example": "She spread mulch around the rose bushes in autumn."},
    "MURAL": {"pos": "noun", "meaning": "a large painting applied directly to a wall or ceiling", "example": "A vivid mural covered the entire side of the building."},
    "MURKY": {"pos": "adjective", "meaning": "dark and gloomy; not clear; suspicious or morally doubtful", "example": "The murky water made it impossible to see the bottom."},
    "MUSIC": {"pos": "noun", "meaning": "vocal or instrumental sounds combined to produce beauty and expression", "example": "Music filled every room of the house."},
    "MUSTY": {"pos": "adjective", "meaning": "having a stale, mouldy smell; outdated", "example": "The old house had a musty smell of damp books."},
    "MUTED": {"pos": "adjective", "meaning": "quietened; softened in color or sound; restrained", "example": "The room was decorated in muted earth tones."},
    "MYRRH": {"pos": "noun", "meaning": "a fragrant resin obtained from certain trees, used in perfumes and incense", "example": "Myrrh was one of the gifts brought by the Magi."},

    # ── N ──────────────────────────────────────────────────────────────────

    "NACHO": {"pos": "noun", "meaning": "a tortilla chip topped with cheese and other toppings", "example": "They shared a plate of nachos at the cinema."},
    "NADIR": {"pos": "noun", "meaning": "the lowest point in a situation; the point directly below the observer", "example": "The team's nadir came with five consecutive losses."},
    "NAIVE": {"pos": "adjective", "meaning": "showing a lack of experience or judgment; innocent and unsuspecting", "example": "It was naive to think the deal would be without strings."},
    "NANNY": {"pos": "noun", "meaning": "a person employed to look after children; a female goat", "example": "The nanny took the children to the park each afternoon."},
    "NASAL": {"pos": "adjective", "meaning": "relating to the nose; having a tone produced through the nose", "example": "Her nasal voice carried across the quiet room."},
    "NASTY": {"pos": "adjective", "meaning": "highly unpleasant; unkind or spiteful", "example": "He left a nasty comment online."},
    "NAVAL": {"pos": "adjective", "meaning": "relating to a navy or warships", "example": "A naval battle decided the outcome of the war."},
    "NAVEL": {"pos": "noun", "meaning": "the small hollow in the abdomen; the belly button; a type of orange", "example": "She wore a crop top that showed her navel."},
    "NEEDY": {"pos": "adjective", "meaning": "lacking necessities; emotionally demanding and insecure", "example": "Funds were directed toward needy families."},
    "NERVE": {"pos": "noun", "meaning": "a fiber transmitting impulses; courage or boldness; cheek", "example": "He had the nerve to ask for a pay rise on his first week."},
    "NEVER": {"pos": "adverb", "meaning": "not ever; at no time; absolutely not", "example": "She never missed a single meeting in five years."},
    "NEXUS": {"pos": "noun", "meaning": "a connection or link; the central point of a network", "example": "The city was the nexus of the country's financial system."},
    "NICHE": {"pos": "noun", "meaning": "a position suited to a person's abilities; a hollow in a wall; a specialized market", "example": "She carved out a niche in handmade leather goods."},
    "NIECE": {"pos": "noun", "meaning": "a daughter of one's brother or sister", "example": "She bought her niece a book for her birthday."},
    "NIFTY": {"pos": "adjective", "meaning": "particularly good, clever, or effective (informal)", "example": "That's a nifty little gadget for opening jars."},
    "NIGHT": {"pos": "noun", "meaning": "the period of darkness between sunset and sunrise", "example": "She stayed up reading long into the night."},
    "NINJA": {"pos": "noun", "meaning": "a person trained in Japanese martial arts and stealth; an expert", "example": "He moved like a ninja, undetected by the guards."},
    "NINNY": {"pos": "noun", "meaning": "a foolish and weak person", "example": "Don't be a ninny—just say what you think."},
    "NOBLE": {"pos": "adjective", "meaning": "having high moral qualities; belonging to the aristocracy; impressive", "example": "It was a noble effort, even if it fell short."},
    "NOISE": {"pos": "noun", "meaning": "a loud or unpleasant sound; unwanted signals in data", "example": "The noise from the building site was constant."},
    "NOMAD": {"pos": "noun", "meaning": "a person who moves from place to place rather than settling", "example": "He was a digital nomad, working from a different country each month."},
    "NOOSE": {"pos": "noun", "meaning": "a loop in a rope that tightens when pulled; a trap", "example": "The tightening regulations were a noose around the industry."},
    "NORTH": {"pos": "noun", "meaning": "the direction toward the North Pole; the northern part of a place", "example": "They traveled north for three days."},
    "NOTCH": {"pos": "noun", "meaning": "a V-shaped cut; a level or degree; to achieve", "example": "She notched up another win in the tournament."},
    "NOVEL": {"pos": "noun", "meaning": "a long fictional narrative in prose; new and original", "example": "Her debut novel was shortlisted for a major prize."},
    "NUDGE": {"pos": "verb", "meaning": "to push gently; to encourage gradually toward a goal", "example": "She nudged him and pointed to the sign."},
    "NURSE": {"pos": "noun", "meaning": "a person trained to care for the sick; to tend or look after", "example": "The nurse checked the patient's temperature every hour."},
    "NUTTY": {"pos": "adjective", "meaning": "containing nuts; crazy or eccentric (informal)", "example": "He had some nutty ideas that occasionally turned out to be brilliant."},
    "NYLON": {"pos": "noun", "meaning": "a strong lightweight synthetic fiber used in fabrics and rope", "example": "Her stockings were made of fine nylon."},
    "NYMPH": {"pos": "noun", "meaning": "a mythological spirit of nature; an immature form of an insect", "example": "In Greek myth, nymphs inhabited rivers, trees, and mountains."},

    # ── O ──────────────────────────────────────────────────────────────────

    "OAKEN": {"pos": "adjective", "meaning": "made of or resembling oak wood", "example": "The oaken beams of the old barn still held firm."},
    "OASIS": {"pos": "noun", "meaning": "a fertile spot in a desert with a water source; a welcome relief", "example": "The café was an oasis of calm in the busy city."},
    "OBESE": {"pos": "adjective", "meaning": "grossly overweight; having excess body fat to a degree harmful to health", "example": "The doctor warned that he was clinically obese."},
    "OCCUR": {"pos": "verb", "meaning": "to take place; to come to mind; to be found", "example": "It didn't occur to her that he might be lying."},
    "OCEAN": {"pos": "noun", "meaning": "the vast body of salt water covering most of the earth's surface", "example": "The ocean stretched endlessly beyond the horizon."},
    "OFFER": {"pos": "verb", "meaning": "to present for acceptance or rejection; to put forward for consideration", "example": "She offered to help carry the bags."},
    "OFTEN": {"pos": "adverb", "meaning": "frequently; many times; in many cases", "example": "He often stayed late at the office."},
    "OGRES": {"pos": "noun", "meaning": "frightening giants in folklore; cruel or threatening people", "example": "The characters battled ogres through the enchanted forest."},
    "OLIVE": {"pos": "noun", "meaning": "a small fruit yielding oil; a grey-green color; a branch symbolizing peace", "example": "She extended an olive branch to end the dispute."},
    "OMEGA": {"pos": "noun", "meaning": "the last letter of the Greek alphabet; an ending or final stage", "example": "From alpha to omega, the journey was extraordinary."},
    "OMENS": {"pos": "noun", "meaning": "events seen as signs of future good or bad fortune", "example": "Dark clouds on the wedding day were considered ill omens."},
    "ONION": {"pos": "noun", "meaning": "a rounded bulb with a pungent smell and flavor, used widely in cooking", "example": "She chopped the onion and her eyes immediately watered."},
    "ONSET": {"pos": "noun", "meaning": "the beginning of something, especially something unpleasant", "example": "At the onset of winter, they stocked the larder."},
    "OOMPH": {"pos": "noun", "meaning": "the quality of being exciting or having energy; sex appeal (informal)", "example": "The redesign gave the brand some much-needed oomph."},
    "OPERA": {"pos": "noun", "meaning": "a dramatic work set to music and performed with singing and orchestra", "example": "She wept at the final aria of the opera."},
    "OPIUM": {"pos": "noun", "meaning": "an addictive narcotic drug made from the poppy plant", "example": "Opium addiction devastated entire communities."},
    "OPTIC": {"pos": "adjective", "meaning": "relating to the eye or vision; relating to light", "example": "An optic fibre can transmit data at the speed of light."},
    "ORBIT": {"pos": "noun", "meaning": "the curved path of a celestial body around another; a sphere of activity", "example": "The satellite completed one orbit every ninety minutes."},
    "ORDER": {"pos": "noun", "meaning": "an authoritative command; a sequence; a request for goods", "example": "She placed an order for three copies of the book."},
    "ORGAN": {"pos": "noun", "meaning": "a distinct part of the body with a specific function; a pipe instrument", "example": "The cathedral organ could be heard throughout the building."},
    "OTTER": {"pos": "noun", "meaning": "a semiaquatic mammal with dense fur that swims and eats fish", "example": "An otter slid into the river without a splash."},
    "OUNCE": {"pos": "noun", "meaning": "a unit of weight equal to one-sixteenth of a pound; a small amount", "example": "She weighed out two ounces of dark chocolate."},
    "OUTER": {"pos": "adjective", "meaning": "situated on the outside; further from the centre", "example": "The outer walls of the castle were ten feet thick."},
    "OVARY": {"pos": "noun", "meaning": "a female reproductive organ producing eggs; the seed-bearing part of a flower", "example": "The ovary is central to the female reproductive system."},
    "OVERT": {"pos": "adjective", "meaning": "done openly and not secretly; not hidden", "example": "There was no overt hostility, just a quiet coldness."},
    "OXIDE": {"pos": "noun", "meaning": "a compound of oxygen with another element", "example": "Iron oxide is the reddish compound commonly known as rust."},
    "OWNER": {"pos": "noun", "meaning": "a person who owns something; one who has legal possession", "example": "The owner of the dog apologized for its behaviour."},
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
        csv_path = _WORDS_FILE.parent / "definitions_ho.csv"
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
    parser = argparse.ArgumentParser(description="Seed word definitions for H–O words")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing definitions")
    parser.add_argument("--csv", action="store_true", help="Also write a CSV backup file")
    args = parser.parse_args()
    asyncio.run(main(overwrite=args.overwrite, csv_out=args.csv))
