# Context Diagram

```mermaid
flowchart LR
    Student -->|question| Agent[Student Support Agent]
    Agent -->|retrieves approved information| Knowledge[(Knowledge Sources)]
    Agent -->|answer with boundaries| Student
    Agent -->|escalates| Staff[Relevant University Office]
    Staff -->|verified updates| Knowledge
```

The application sits between students and approved institutional information. It supports discovery and explanation; it does not replace authorized university staff or make binding decisions.
