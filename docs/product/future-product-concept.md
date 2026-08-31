# Future product concept

This is an exploratory interface and workflow sketch for capabilities outside the Discovery MVP. It is not an implementation specification. In particular, its `Autonomy` and `APPLY` sketches do not authorize unattended execution: any future external write must follow the [future execution approval boundary](future-execution-approval-boundary.md).

```md
┌──────────────────────────────────────────────────────────┐
│                      usr CONTROL ROOM                    │
│                      _for each agent_                    │
└──────────────────────────────────────────────────────────┘

### Togglers:
- Focus     [ Career | Education | Grants | Side | All ] |
- Autonomy  [ Suggest | Ask me | Auto ]                  |
- Horizon   near ◄───────────────●───────────────► far   |
                 now             1y           life       |┐
                                                         |│
- Loaction  [ + Add location ]                           |│
                                                          │
                                                          │
     ┌──────────────┐            ┌──────────────┐         │ 
     │   PROFILE    │            │    GOALS     │         │ 
     │ CV, publicity│            │ long / short │         │ 
     └──────┬───────┘            └──────┬───────┘         │ 
            └─────────────┬─────────────┘                 │
                          ▼                               │
                ┌────────────────────┐                    │
 DB 🗄️  ◄-----► │ OPPORTUNITY RADAR  │                    │
                │     searching      │◄─┬─────────────────┘
                └─────────┬──────────┘  │
                          ▼             │
                ┌────────────────────┐  │
              ┌►│       FILTER       │◄─┘
              │ └─────────┬──────────┘
              │           ▼              
              │ ┌────────────────────┐
              └─│      FEEDBACK      │
                │  usr sellects x%   │
                └─────────┬──────────┘
                          ▼              
                ┌────────────────────┐
                │       APPLY        │
                │   our usr email    │
                └────────────────────┘
```

```md
┌──────────────────────────────────────────────────────────┐
│                   usr PROGRESS DASHBOARD                 │
└──────────────────────────────────────────────────────────┘
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  THE EMAIL  │◄───►│  any NEWS ? │────►│ NOTIFICATION │
└─────────────┘     └─────────────┘     └──────────────┘
            ┌───────────────────┐       ┌──────────────┐
            │ PROFILE IMPROVING │ ◄───► │  STATISTIC   │
            └───────────────────┘       └──────────────┘
                                        ┌──────────────┐
                                        │   STATUSES   │
                                        │  aplication  │
                                        └──────────────┘
                                   ┌───────────────────┐
                                   │FEEDBACK AGREGATION│
                                   └───────────────────┘
```

