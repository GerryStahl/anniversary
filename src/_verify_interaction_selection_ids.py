import sys
sys.path.insert(0, ".")
import src.store as s

wanted_titles = [
    "A framework for conceptualizing, representing, and analyzing distributed interaction",
    "The joint organization of interaction within a multimodal CSCL medium",
    "Educational dialogues and computer supported collaborative learning: critical analysis and research perspectives",
    "When coding-and-counting is not enough: using epistemic network analysis (ENA) to analyze verbal data in CSCL research",
    "PolyCAFe—automatic support for the polyphonic analysis of CSCL chats",
    "Wiki-supported collaborative learning in primary education: How a dialogic space is created for thinking together",
    "Life history of a topic in an online discussion: a complex systems theory perspective on how one message attracts class members to create meaning collaboratively",
    "Dialogues across time and space in a video-based collaborative learning environment",
    "Contextual perspective in analysing collaborative knowledge construction of two small groups in web-based discussion",
    "Attending to others’ posts in asynchronous discussions: Learners’ online “listening” and its relationship to speaking",
    "Dialogic intervisualizing in multimodal inquiry",
    "An artificial intelligence-driven learning analytics method to examine the collaborative problem-solving process from the complex adaptive systems perspective",
    "Supporting classroom orchestration with real-time feedback: A role for teacher dashboards and real-time agents",
    "Deconstructing orchestration load: comparing teacher support through mirroring and guiding",
    "Implementing learning analytics in wiki-supported collaborative learning in secondary education: A framework- motivated empirical study",
    "Studying participation networks in collaboration using mixed methods",
    "Toward a classification of discourse patterns in asynchronous online discussions",
    "Distinguishing knowledge-sharing, knowledge- construction, and knowledge-creation discourses",
    "Leveraging mobile eye-trackers to capture joint visual attention in co-located collaborative learning groups",
    "Capturing the participation and social dimensions of",
    "iTalk–iSee: A participatory visual learning analytical tool for productive peer talk",
    "Studying teacher withitness in the wild: comparing a mirroring and an alerting & guiding dashboard for collaborative learning",
    "Accomplishing collaboration at scale: How professionals jointly frame problems on Stack Overflow",
    "“I guess my question is”: What is the co-occurrence of uncertainty and learning in computer-mediated discourse?",
]

store = s.load_store()
by_title = {((a.title or "").strip()): a.id for a in store.values()}
for title in wanted_titles:
    if title in by_title:
        print(f"FOUND\t{title}\t{by_title[title]}")
    else:
        matches = [(t, i) for t, i in by_title.items() if title.lower() in t.lower() or t.lower() in title.lower()]
        print(f"MISSING\t{title}")
        for t, i in matches[:5]:
            print(f"  CANDIDATE\t{t}\t{i}")
