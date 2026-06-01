Ma struktura ma zawierac i przekazywac caly kontekst dla dowolnego node
zarowno komendy jak i prompty zbudowane w dowolny sposob
Kontekst ma zawierac komplet informacji ktore agent potrzebuje by poprawnie realizowac zadanie
Jest podreczna biblioteka najwazniejszych niezbednych elementow ktore agent musi znac
Podzial bedzie

a)system context - to beda wszystkie reguly sterujace agenta, to by agent wiedzial co moze czego nie moze
  z kim moze sie komunikowac co ma w dyspozycji systemowej jakie narzedzia i technologie,
  tu jest okreslana rola agenta i powiazane z nia skille
b)domain contekst to jest zbior informacji o domenie w ktorej agent sie porusza wiedza z czym ogolnie ma doczynienia
c)session contekst to kontekst zwiazany z sessia calym zadaniem jakie jest realizowane dzieki temu agent dostac moze informacje o czyms co zostalo juz ustalone wczesniej
e)memory_contekst to zbior informacji ktore zostaly ustalone we wczesniejszych procesach sesjach czesto powtarzalnych regolach lub waznych informacjach, tu agent moze siegnac by sie czegos nauczonego o przedmiocie dowiedziec
f) execution_context - kontekst tego subzadania tego co tu i teraz jest do wykonania  




Dla architektury agentowej / graph-based (LangGraph, Semantic Kernel, własny orchestrator) taki podział jest sensowny, ale brakuje jeszcze kilku warstw, które w praktyce bardzo szybko okazują się potrzebne.

Ja rozdzieliłbym to tak:

Context
├── system_context
├── domain_context
├── session_context
├── memory_context
├── execution_context
├── communication_context
├── resource_context
├── state_context
└── audit_context
1. system_context

Stałe reguły działania agenta.

Przykłady:

agent_id: architect-agent

role:
  name: Enterprise Architect

skills:
  - java
  - spring
  - ddd
  - cqrs

constraints:
  - never_modify_production
  - no_external_calls

available_tools:
  - vector_search
  - sql_query
  - github_search

communication_rules:
  - can_call: [analyst-agent, coding-agent]

Odpowiada na pytanie:

Kim jestem i jakie są moje globalne zasady?

2. domain_context

Wiedza domenowa.

Przykład:

domain:
  name: Banking

entities:
  - Customer
  - Account
  - Transaction

business_rules:
  - account_must_have_owner
  - transaction_cannot_be_negative

Odpowiada na pytanie:

W jakim świecie biznesowym działam?

3. session_context

Kontekst całego procesu.

Przykład:

session_id: S-123

goal:
  migrate monolith to microservices

decisions:
  - use kafka
  - use postgres

completed_tasks:
  - identify bounded contexts

Odpowiada na pytanie:

Co już ustaliliśmy w tej konkretnej sesji?

4. memory_context

Długoterminowa pamięć.

Przykład:

lessons_learned:
  - customer_service_should_not_own_payments

organization_preferences:
  - use_java_21
  - use_maven

known_patterns:
  - event_sourcing
  - outbox_pattern

Odpowiada na pytanie:

Czego nauczyłem się wcześniej?

5. execution_context

Najważniejszy dla pojedynczego node.

Przykład:

task:
  generate_rest_api

input:
  aggregate: Customer

expected_output:
  openapi_spec

constraints:
  - use_rest
  - no_graphql

Odpowiada na pytanie:

Co mam zrobić dokładnie teraz?

Brakuje jeszcze:
6. communication_context

Przy multi-agentach jest krytyczny.

Przykład:

sender:
  analyst-agent

receiver:
  architect-agent

conversation:
  correlation_id: XYZ

previous_messages:
  - ...

Odpowiada na pytanie:

Kto mi to zlecił i z jakim kontekstem komunikacyjnym?

Bez tego ciężko śledzić delegacje między agentami.

7. resource_context

Źródła wiedzy dostępne dla agenta.

Przykład:

documents:
  - ADR-001
  - ADR-002

repositories:
  - customer-service

knowledge_sources:
  - vector_db
  - wiki

Odpowiada na pytanie:

Z jakich danych mogę korzystać?

To nie jest domain context.

Domain opisuje świat biznesowy.

Resource opisuje skąd agent ma pobierać wiedzę.

8. state_context

Stan workflow.

Przykład:

workflow:
  id: WF-22

current_node:
  architecture-review

previous_node:
  requirements-analysis

next_node:
  implementation

Odpowiada na pytanie:

Gdzie jestem w grafie procesu?

Przy LangGraphach i własnych orchestratorach to zwykle osobna sekcja.

9. audit_context

Enterprise'owo bardzo przydatne.

Przykład:

request_id: R-123

user:
  john.smith

timestamp:
  2026-05-31T10:00:00

trace_id:
  abc-xyz

Odpowiada na pytanie:

Jak odtworzyć wykonanie procesu?

Finalnie

Gdybym projektował uniwersalny AgentContext dla enterprise multi-agent system, zrobiłbym:

AgentContext
 ├─ SystemContext
 ├─ DomainContext
 ├─ SessionContext
 ├─ MemoryContext
 ├─ ExecutionContext
 ├─ CommunicationContext
 ├─ ResourceContext
 ├─ StateContext
 └─ AuditContext

Przy czym dla pojedynczego node najważniejsze są zwykle:

SystemContext
+
ExecutionContext
+
SessionContext
+
MemoryContext

a pozostałe pełnią rolę infrastrukturalną i orkiestracyjną. To daje praktycznie kompletny model kontekstu dla agentów enterprise działających w grafach, workflow i architekturach multi-agent.