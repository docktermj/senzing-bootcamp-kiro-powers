# Visual Guide: Senzing Bootcamp

This guide provides visual diagrams to help understand the bootcamp flow, data transformations, and architecture patterns.

## Bootcamp Flow Diagram

```mermaid
graph TD
    Start[Start Bootcamp] --> M0{Want Quick Demo?}
    M0 -->|Yes| Module0[Module 0: Quick Demo<br/>10-15 min]
    M0 -->|No| Module1
    Module0 --> Module1

    Module1[Module 1: Business Problem<br/>20-30 min] --> Module2[Module 2: Collect Data<br/>10-15 min per source]
    Module2 --> Module3[Module 3: Data Quality<br/>15-20 min per source]
    Module3 --> M4{Data SGES<br/>Compliant?}

    M4 -->|No| Module4[Module 4: Map Data<br/>1-2 hrs per source]
    M4 -->|Yes| Module5
    Module4 --> Module5

    Module5[Module 5: SDK Setup<br/>30 min - 1 hr] --> Module6[Module 6: Load Single Source<br/>30 min per source]

    Module6 --> M7{Multiple<br/>Sources?}
    M7 -->|Yes| Module7[Module 7: Multi-Source<br/>Orchestration<br/>1-2 hrs]
    M7 -->|No| Module8
    Module7 --> Module8

    Module8[Module 8: Query & Validate<br/>1-2 hrs] --> M9{Production<br/>Deployment?}

    M9 -->|No| Complete[Bootcamp Complete!]
    M9 -->|Yes| Module9[Module 9: Performance<br/>Testing<br/>1-2 hrs]

    Module9 --> Module10[Module 10: Security<br/>Hardening<br/>1-2 hrs]
    Module10 --> Module11[Module 11: Monitoring<br/>1-2 hrs]
    Module11 --> Module12[Module 12: Deploy<br/>2-3 hrs]
    Module12 --> Complete

    style Start fill:#e1f5e1
    style Complete fill:#e1f5e1
    style Module0 fill:#fff4e1
    style Module1 fill:#e1f0ff
    style Module2 fill:#e1f0ff
    style Module3 fill:#e1f0ff
    style Module4 fill:#e1f0ff
    style Module5 fill:#ffe1f0
    style Module6 fill:#ffe1f0
    style Module7 fill:#ffe1f0
    style Module8 fill:#f0e1ff
    style Module9 fill:#ffe1e1
    style Module10 fill:#ffe1e1
    style Module11 fill:#ffe1e1
    style Module12 fill:#ffe1e1
```

## Data Flow Diagram

```mermaid
graph LR
    subgraph "Source Systems"
        CRM[CRM System]
        ERP[ERP System]
        Web[Web Platform]
    end

    subgraph "Module 2: Collection"
        Raw[data/raw/]
    end

    subgraph "Module 3: Quality"
        QA[Quality Assessment]
    end

    subgraph "Module 4: Transformation"
        Transform[Transform Programs]
        Transformed[data/transformed/]
    end

    subgraph "Module 6-7: Loading"
        Loader[Load Programs]
        Senzing[(Senzing Engine)]
        DB[(Database)]
    end

    subgraph "Module 8: Querying"
        Query[Query Programs]
        Results[Results/Exports]
    end

    CRM --> Raw
    ERP --> Raw
    Web --> Raw

    Raw --> QA
    QA --> Transform
    Transform --> Transformed

    Transformed --> Loader
    Loader --> Senzing
    Senzing --> DB

    DB --> Query
    Query --> Results

    style CRM fill:#e1f0ff
    style ERP fill:#e1f0ff
    style Web fill:#e1f0ff
    style Raw fill:#fff4e1
    style QA fill:#f0e1ff
    style Transform fill:#ffe1f0
    style Transformed fill:#fff4e1
    style Loader fill:#ffe1f0
    style Senzing fill:#e1ffe1
    style DB fill:#e1ffe1
    style Query fill:#f0e1ff
    style Results fill:#fff4e1
```

## Transformation Process

```mermaid
graph TD
    Input[Source Data<br/>CSV/JSON/Database] --> Parse[Parse Input]
    Parse --> Map[Map Fields]

    Map --> Name[Name Mapping<br/>first_name → PRIMARY_NAME_FIRST<br/>last_name → PRIMARY_NAME_LAST]
    Map --> Contact[Contact Mapping<br/>email → EMAIL_ADDRESS<br/>phone → PHONE_NUMBER]
    Map --> Address[Address Mapping<br/>address → ADDR_FULL<br/>city → ADDR_CITY]
    Map --> ID[Identifier Mapping<br/>ssn → SSN_NUMBER<br/>dob → DATE_OF_BIRTH]

    Name --> Validate[Validate Record]
    Contact --> Validate
    Address --> Validate
    ID --> Validate

    Validate --> Valid{Valid?}
    Valid -->|Yes| Output[Senzing JSON<br/>data/transformed/]
    Valid -->|No| Error[Error Log]

    style Input fill:#e1f0ff
    style Parse fill:#fff4e1
    style Map fill:#ffe1f0
    style Name fill:#f0e1ff
    style Contact fill:#f0e1ff
    style Address fill:#f0e1ff
    style ID fill:#f0e1ff
    style Validate fill:#ffe1e1
    style Output fill:#e1ffe1
    style Error fill:#ffe1e1
```

## Entity Resolution Process

```mermaid
graph TD
    subgraph "Input Records"
        R1[Record 1<br/>John Smith<br/>john@email.com<br/>555-0101]
        R2[Record 2<br/>J. Smith<br/>jsmith@email.com<br/>555-0101]
        R3[Record 3<br/>Jane Doe<br/>jane@email.com<br/>555-0102]
    end

    subgraph "Senzing Engine"
        Load[Load Records]
        Extract[Extract Features]
        Compare[Compare Features]
        Score[Score Matches]
        Resolve[Resolve Entities]
    end

    subgraph "Resolved Entities"
        E1[Entity 1<br/>John Smith<br/>Records: 1, 2]
        E2[Entity 2<br/>Jane Doe<br/>Records: 3]
    end

    R1 --> Load
    R2 --> Load
    R3 --> Load

    Load --> Extract
    Extract --> Compare
    Compare --> Score
    Score --> Resolve

    Resolve --> E1
    Resolve --> E2

    style R1 fill:#e1f0ff
    style R2 fill:#e1f0ff
    style R3 fill:#e1f0ff
    style Load fill:#fff4e1
    style Extract fill:#ffe1f0
    style Compare fill:#f0e1ff
    style Score fill:#ffe1e1
    style Resolve fill:#e1ffe1
    style E1 fill:#e1ffe1
    style E2 fill:#e1ffe1
```

## Multi-Source Orchestration

```mermaid
graph TD
    Start[Start Orchestration] --> Analyze[Analyze Dependencies]

    Analyze --> Group1[Group 1: Independent Sources]
    Analyze --> Group2[Group 2: Dependent Sources]

    Group1 --> P1[Load CRM<br/>Parallel]
    Group1 --> P2[Load ERP<br/>Parallel]
    Group1 --> P3[Load Web<br/>Parallel]

    P1 --> Wait1[Wait for Group 1]
    P2 --> Wait1
    P3 --> Wait1

    Wait1 --> Group2

    Group2 --> P4[Load Orders<br/>Parallel]
    Group2 --> P5[Load Support<br/>Parallel]

    P4 --> Wait2[Wait for Group 2]
    P5 --> Wait2

    Wait2 --> Validate[Validate All Sources]
    Validate --> Stats[Generate Statistics]
    Stats --> Complete[Orchestration Complete]

    style Start fill:#e1f5e1
    style Analyze fill:#fff4e1
    style Group1 fill:#e1f0ff
    style Group2 fill:#e1f0ff
    style P1 fill:#ffe1f0
    style P2 fill:#ffe1f0
    style P3 fill:#ffe1f0
    style P4 fill:#ffe1f0
    style P5 fill:#ffe1f0
    style Validate fill:#f0e1ff
    style Stats fill:#f0e1ff
    style Complete fill:#e1f5e1
```

## Production Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Application Load Balancer]
    end

    subgraph "Application Tier"
        API1[API Server 1<br/>Senzing Engine]
        API2[API Server 2<br/>Senzing Engine]
        API3[API Server 3<br/>Senzing Engine]
    end

    subgraph "Data Tier"
        DB[(PostgreSQL<br/>Multi-AZ)]
        Cache[(Redis Cache)]
    end

    subgraph "Monitoring"
        Prom[Prometheus]
        Graf[Grafana]
        Alert[Alerting]
    end

    subgraph "Security"
        Vault[Secrets Manager]
        Auth[Authentication]
    end

    Users[Users] --> LB
    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> DB
    API2 --> DB
    API3 --> DB

    API1 --> Cache
    API2 --> Cache
    API3 --> Cache

    API1 --> Prom
    API2 --> Prom
    API3 --> Prom

    Prom --> Graf
    Prom --> Alert

    API1 --> Vault
    API2 --> Vault
    API3 --> Vault

    API1 --> Auth
    API2 --> Auth
    API3 --> Auth

    style Users fill:#e1f0ff
    style LB fill:#fff4e1
    style API1 fill:#ffe1f0
    style API2 fill:#ffe1f0
    style API3 fill:#ffe1f0
    style DB fill:#e1ffe1
    style Cache fill:#e1ffe1
    style Prom fill:#f0e1ff
    style Graf fill:#f0e1ff
    style Alert fill:#ffe1e1
    style Vault fill:#ffe1e1
    style Auth fill:#ffe1e1
```

## Decision Tree: Which Path to Take?

```mermaid
graph TD
    Start{New to Senzing?} -->|Yes| Demo[Start with Module 0<br/>Quick Demo<br/>10 minutes]
    Start -->|No| Experience

    Demo --> Experience{Have data ready?}

    Experience -->|No| M1[Module 1: Define Problem<br/>Module 2: Collect Data]
    Experience -->|Yes| Quality{Data quality<br/>assessed?}

    M1 --> Quality

    Quality -->|No| M3[Module 3: Assess Quality]
    Quality -->|Yes| Format{Data in Senzing<br/>format?}

    M3 --> Format

    Format -->|No| M4[Module 4: Map Data]
    Format -->|Yes| SDK{Senzing<br/>installed?}

    M4 --> SDK

    SDK -->|No| M5[Module 5: Install SDK]
    SDK -->|Yes| Sources{Multiple<br/>sources?}

    M5 --> Sources

    Sources -->|No| M6[Module 6: Load Single Source]
    Sources -->|Yes| M7[Module 6 then 7:<br/>Multi-Source Orchestration]

    M6 --> Prod{Production<br/>deployment?}
    M7 --> Prod

    Prod -->|No| M8[Module 8: Query & Validate<br/>DONE!]
    Prod -->|Yes| M9[Modules 9-12:<br/>Performance, Security,<br/>Monitoring, Deploy]

    M9 --> Complete[Production Ready!]

    style Start fill:#e1f5e1
    style Demo fill:#fff4e1
    style M1 fill:#e1f0ff
    style M3 fill:#e1f0ff
    style M4 fill:#e1f0ff
    style M5 fill:#ffe1f0
    style M6 fill:#ffe1f0
    style M7 fill:#ffe1f0
    style M8 fill:#f0e1ff
    style M9 fill:#ffe1e1
    style Complete fill:#e1f5e1
```

## Module Dependencies

```mermaid
graph LR
    M0[Module 0<br/>Quick Demo<br/>Optional] -.-> M1

    M1[Module 1<br/>Business Problem<br/>Required] --> M2[Module 2<br/>Collect Data<br/>Required]

    M2 --> M3[Module 3<br/>Data Quality<br/>Required]

    M3 --> M4[Module 4<br/>Map Data<br/>Conditional]
    M3 -.->|SGES Data| M5

    M4 --> M5[Module 5<br/>SDK Setup<br/>Required]

    M5 --> M6[Module 6<br/>Load Single<br/>Required]

    M6 --> M7[Module 7<br/>Multi-Source<br/>Conditional]
    M6 -.->|Single Source| M8

    M7 --> M8[Module 8<br/>Query/Validate<br/>Required]

    M8 -.->|Dev Only| End[Complete]
    M8 --> M9[Module 9<br/>Performance<br/>Production Only]

    M9 --> M10[Module 10<br/>Security<br/>Production Only]

    M10 --> M11[Module 11<br/>Monitoring<br/>Production Only]

    M11 --> M12[Module 12<br/>Deploy<br/>Production Only]

    M12 --> End

    style M0 fill:#fff4e1
    style M1 fill:#e1f0ff
    style M2 fill:#e1f0ff
    style M3 fill:#e1f0ff
    style M4 fill:#e1f0ff
    style M5 fill:#ffe1f0
    style M6 fill:#ffe1f0
    style M7 fill:#ffe1f0
    style M8 fill:#f0e1ff
    style M9 fill:#ffe1e1
    style M10 fill:#ffe1e1
    style M11 fill:#ffe1e1
    style M12 fill:#ffe1e1
    style End fill:#e1f5e1
```

## Time Estimates by Path

```mermaid
gantt
    title Bootcamp Time Estimates
    dateFormat X
    axisFormat %H:%M

    section Quick Demo
    Module 0 :0, 15m

    section Fast Track
    Module 5 SDK Setup :0, 60m
    Module 6 Load Data :60m, 30m
    Module 8 Query :90m, 60m

    section Complete Path
    Module 1 Problem :0, 30m
    Module 2 Collect :30m, 45m
    Module 3 Quality :75m, 60m
    Module 4 Mapping :135m, 120m
    Module 5 SDK :255m, 60m
    Module 6 Load :315m, 30m
    Module 8 Query :345m, 120m

    section Production Path
    Modules 1-8 :0, 465m
    Module 9 Performance :465m, 120m
    Module 10 Security :585m, 120m
    Module 11 Monitoring :705m, 120m
    Module 12 Deploy :825m, 180m
```

## Data Quality Scoring

```mermaid
graph LR
    Input[Source Data] --> C1[Completeness<br/>Check]
    Input --> C2[Consistency<br/>Check]
    Input --> C3[Accuracy<br/>Check]
    Input --> C4[Uniqueness<br/>Check]

    C1 --> S1[Score: 0-100]
    C2 --> S2[Score: 0-100]
    C3 --> S3[Score: 0-100]
    C4 --> S4[Score: 0-100]

    S1 --> Avg[Average Score]
    S2 --> Avg
    S3 --> Avg
    S4 --> Avg

    Avg --> Grade{Overall Grade}

    Grade -->|90-100| A[Grade A<br/>Excellent<br/>Ready to Load]
    Grade -->|75-89| B[Grade B<br/>Good<br/>Minor Issues]
    Grade -->|60-74| C[Grade C<br/>Fair<br/>Needs Improvement]
    Grade -->|<60| D[Grade D<br/>Poor<br/>Fix Before Loading]

    style Input fill:#e1f0ff
    style C1 fill:#fff4e1
    style C2 fill:#fff4e1
    style C3 fill:#fff4e1
    style C4 fill:#fff4e1
    style Avg fill:#ffe1f0
    style A fill:#e1ffe1
    style B fill:#e1ffe1
    style C fill:#ffe1e1
    style D fill:#ffe1e1
```

## Using These Diagrams

### In Documentation

These diagrams are embedded in markdown files and render automatically in:

- GitHub
- GitLab
- VS Code (with Mermaid extension)
- Most modern markdown viewers

### Exporting

To export as images:

1. Use online tools like [Mermaid Live Editor](https://mermaid.live/)
2. Use VS Code with Mermaid extension
3. Use command-line tools like `mmdc`

### Customizing

To customize diagrams:

1. Copy the mermaid code block
2. Modify node names, connections, or styles
3. Test in Mermaid Live Editor
4. Update documentation

## Related Documentation

- [POWER.md](../../POWER.md) - Bootcamp overview
- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [PROGRESS_TRACKER.md](PROGRESS_TRACKER.md) - Track your progress

## Version History

- **v1.0.0** (2026-03-17): Visual guide created with Mermaid diagrams
