# Initialization
Load and use the following project context:

- PROJECT_IDEA:       /op2u/README.md
- COMPETITORS:        /op2u/docs/competitors.md
- TARGET_AUDIENCE:    /op2u/docs/target_audience.md
- OUTPUT_DIR:         /op2u/docs/agent_analysis

Keep these paths available for later steps.

# Role
You are a senior startup strategist, market researcher, YC-style evaluator, product analyst, and venture memo writer.

Analyze the startup idea below and produce a rigorous competitor analysis report. Be skeptical, concise, quantitative where possible, and practical. Do not write generic startup fluff.

# Product concept
The product is a personal opportunity autopilot:
- builds and maintains a user profile;
- discovers relevant opportunities across jobs, education, grants, scholarships, conferences, fellowships, research visits, artist residencies, accelerators, NGO/policy programs, competitions, hackathons, and side opportunities;
- scores fit and expected value;
- prepares application materials;
- applies automatically or with user approval;
- tracks deadlines, submissions, statuses, replies, and outcomes;
- uses feedback to improve the user profile and future applications.

# Required research scope
Analyze competitors and substitutes across these categories:
1. Job auto-apply and career agents
2. Job trackers and resume optimization tools
3. Global opportunity directories
4. Scholarship and education funding platforms
5. Research grant databases
6. Nonprofit and grant management platforms
7. Creative residency and open-call platforms
8. Conference CFP and speaker opportunity platforms
9. NGO / UN / policy / impact opportunity platforms
10. Startup accelerators / hackathon / maker-opportunity platforms
11. General AI agents and search tools
12. Manual substitutes: Google, newsletters, Telegram/Discord groups, spreadsheets, Notion, Airtable, personal assistants

# Mandatory competitor examples
Include, but do not limit yourself to COMPETITORS

# Research rules
For every factual claim:
- prefer official websites, pricing pages, documentation, app stores, public reviews, user forums, Reddit/Hacker News/Product Hunt/G2/Capterra where relevant;
- cross-check important claims across at least 2 sources;
- include source URLs and access dates;
- distinguish confirmed facts from estimates and assumptions;
- flag outdated, uncertain, or low-confidence data.

# Report structure
Produce a polished PDF report in OUTPUT_DIR with the following sections:

## 1. Abstract
One-page executive summary:
- what the startup is;
- what market it enters;
- strongest competitors;
- biggest risks;
- strongest wedge;
- final verdict.

## 2. Startup interpretation
Explain the startup in one paragraph and one diagram.

Include:
- user persona;
- core job-to-be-done;
- main workflow;
- why now;
- what must be true for this to work.

## 3. Competitive landscape
Create a structured competitor taxonomy.

For each category include:
- category definition;
- user pain it solves;
- typical business model;
- typical weakness;
- relevance to the startup.

## 4. Competitor master table
Create a table with columns:

- Competitor
- Category
- Primary user
- Core job-to-be-done
- Main features
- Pricing / business model
- Geography / scope
- Automation level: 0–5
- Personalization level: 0–5
- Breadth of opportunity coverage: 0–5
- Application support: 0–5
- Tracking/status workflow: 0–5
- Data/source advantage: 0–5
- UX quality: 0–5
- Trust/compliance risk
- Strengths
- Weaknesses
- Why users choose it
- How op2u can beat it
- Source URLs
- Confidence: low/medium/high

## 5. Competitor matrix visualizations
Generate at least these visualizations:

### 5.1 Breadth vs autonomy matrix
X-axis:
- low autonomy → high autonomy

Y-axis:
- narrow vertical → broad life-opportunity scope

Place all competitors on the matrix.

### 5.2 Pain vs solution adequacy map
Rows:
- opportunity discovery
- fit scoring
- deadline tracking
- application writing
- auto-application
- status tracking
- profile improvement
- long-term life trajectory planning

Columns:
- manual search
- directories
- job auto-apply bots
- scholarship platforms
- grant platforms
- op2u target product

Use scores 0–5 and color coding.

### 5.3 Market wedge matrix
X-axis:
- ease of MVP launch

Y-axis:
- urgency / willingness to pay

Plot:
- jobs
- scholarships
- conferences/travel grants
- fellowships/research visits
- creative residencies
- NGO/UN programs
- startup accelerators
- hackathons
- nonprofit grants

### 5.4 Threat matrix
X-axis:
- ability to copy op2u

Y-axis:
- existing distribution/data advantage

Plot major competitors.

### 5.5 User workflow comparison
Compare:
- current manual workflow
- directory-based workflow
- job auto-apply workflow
- op2u workflow

Use flow diagrams.

### 5.6 Positioning map
Compare slogans and positioning:
- “job application automation”
- “scholarship matching”
- “grant discovery”
- “opportunity directory”
- “personal opportunity autopilot”
- “life trajectory engine”

## 6. Market assessment by direction
For each opportunity direction evaluate:

- market size estimate: TAM/SAM/SOM, with assumptions;
- user urgency;
- willingness to pay;
- supply fragmentation;
- regulatory/compliance complexity;
- application complexity;
- frequency of need;
- retention potential;
- data availability;
- automation feasibility;
- recommended priority.

Use a 1–5 score and explain.

Directions:
- jobs and internships;
- scholarships and funded education;
- conferences and travel grants;
- fellowships and research visits;
- creative residencies;
- NGO/UN/policy programs;
- startup accelerators;
- hackathons and competitions;
- grants for nonprofits/research;
- hobby/side opportunities.

## 7. User pain analysis
Identify user pains.

For each pain include:
- pain statement;
- current workaround;
- why current workaround is insufficient;
- frequency;
- intensity;
- willingness to pay;
- which competitor solves it best today;
- gap left open;
- op2u feature opportunity.

## 8. YC-style evaluation
Evaluate according to YC-style criteria:

- Is this a real hair-on-fire problem?
- Who has this problem most intensely?
- Is the initial market small but expandable?
- Is there a sharp wedge?
- Can the team get users manually first?
- Is there a path to a monopoly-like data/workflow advantage?
- What is the 10x better product promise?
- What is the dangerous assumption?
- What can be tested in 7 days?
- What can be tested in 30 days?
- What metric proves pull?

Give brutally honest scores 0–10.

## 9. Strategic recommendations
Include:

- best initial niche;
- first 3 user personas;
- MVP scope;
- features to avoid;
- data acquisition strategy;
- distribution strategy;
- monetization options;
- moat strategy;
- legal/compliance risks;
- 30/60/90-day roadmap.

## 10. Final verdict
End with:

- one-sentence verdict;
- strongest opportunity;
- biggest threat;
- best wedge;
- recommended MVP;
- kill criteria;
- next research tasks.

# Output requirements
Create the final answer as a PDF report in OUTPUT_DIR

Also provide:
1. Markdown source file.
2. CSV file with the competitor master table.
3. PNG/SVG visualizations:
   - breadth vs autonomy matrix;
   - pain vs solution adequacy heatmap;
   - market wedge matrix;
   - threat matrix;
   - workflow comparison.

# Style
- Use clear headings.
- Use dense tables.
- Use diagrams.
- No motivational fluff.
- No fake precision.
- Mark assumptions.
- Cite sources.
- Prefer practical conclusions over generic analysis.
