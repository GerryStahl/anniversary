import sys
sys.path.insert(0, ".")
import src.store as s

wanted = [
    "Collaborative knowledge building using the Design Principles Database",
    "Specifying computer-supported collaboration scripts",
    "The mechanics of CSCL macro scripts",
    "Operationalizing macro-scripts in CSCL technological settings",
    "A systemic and cognitive view on collaborative knowledge building with wikis",
    "Rainbow: A framework for analysing computer-mediated pedagogical debates",
    "A framework for conceptualizing, representing, and analyzing distributed interaction",
    "Computer-supported argumentation: A review of the state of the art",
    "Connecting agents and artifacts in CSCL: Towards a rationale of mutual shaping",
    "Instrumental genesis in technology-mediated learning: From double stimulation to expansive knowledge practices",
    "The dialectical potential of Cultural Historical Activity Theory for researching sustainable CSCL practices",
    "A Habermasian perspective on joint meaning making online: What does it offer and what are the difficulties?",
]

arts = list(s.load_store().values())
for title in wanted:
    m = [a for a in arts if (a.title or "").strip() == title]
    if not m:
        print(f"MISSING\t{title}")
        continue
    a = m[0]
    print("---")
    print(a.id)
    print(f"{a.year}\t{a.title}")
    print(f"theory_primary={a.theory_primary}")
    print(f"summary={(a.summary_haiku or '').replace(chr(10), ' ')[:650]}")
