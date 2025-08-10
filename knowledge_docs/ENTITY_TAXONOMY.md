# Entity Taxonomy (BSI Graphs)

- Business
  - Domain
  - Actor (User)

- System
  - Service
  - Module
  - Database (Managed_DB/Third_Party_DB)
  - Message_Bus
  - External_API (HTTP/REST/GraphQL)
  - LLM_Service (OpenAI/Gemini/etc.)
  - Auth_Provider (OIDC/SAML/Custom)
  - API (Gateway/REST/GraphQL)
  - Web_App, Mobile_App
  - Queue/Task_Runner, Scheduler/Job
  - Cache, Storage, Search
  - Secrets_Config, Observability (optional placeholders)

- Implementation
  - File
  - Class
  - Function_Group

- Edges
  - contains
  - depends_on
  - calls

Notes
- External_* are stubs (no local files) used when referenced but not defined in repo.
- Keep this list minimal; refine labels later. Do not add side features here.
