# Entity Taxonomy (BSI Graphs)

- Business
  - Domain
  - Actor (User)

- System
  - API (Gateway/REST/GraphQL)
  - Service / Module
  - Database (Managed_DB/Third_Party_DB)
  - Cache
  - Message_Bus
  - Queue / Task_Runner, Scheduler/Job
  - Storage, Search
  - External_API (HTTP/REST/GraphQL)
  - LLM_Service (OpenAI/Gemini/etc.)
  - Auth_Provider (OIDC/SAML/Custom)
  - Secrets_Config, Observability (optional placeholders)

- Implementation
  - File
  - Class
  - Function_Group

- Edges
  - contains
  - depends_on (may be weighted; rolled-up imports/calls)
  - calls (raw implementation calls)

Notes
- External_* are stubs (no local files) used when referenced but not defined in repo.
- Keep this list minimal; refine labels later. Do not add side features here.
