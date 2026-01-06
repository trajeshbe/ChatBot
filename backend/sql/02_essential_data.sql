pg_dump: warning: there are circular foreign-key constraints on this table:
pg_dump: detail: roles
pg_dump: hint: You might not be able to restore the dump without using --disable-triggers or temporarily dropping the constraints.
pg_dump: hint: Consider using a full dump instead of a --data-only dump to avoid this problem.
pg_dump: warning: there are circular foreign-key constraints on this table:
pg_dump: detail: departments
pg_dump: hint: You might not be able to restore the dump without using --disable-triggers or temporarily dropping the constraints.
pg_dump: hint: Consider using a full dump instead of a --data-only dump to avoid this problem.
--
-- PostgreSQL database dump
--

\restrict nWWgmy1aAgxbIGcHuAi2kVeEHgOC92JIABtfP7K7xh8dMbK52edwLd4hf6vCvww

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg12+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.departments (id, name, parent_department_id, description, is_active, created_at, updated_at, meta_info) FROM stdin;
0f4c1f28-a193-4075-907c-0a5916f2b62f	Data Operations	\N	Data research and operations teams	t	2025-11-30 14:13:46.911574+00	2025-11-30 14:13:46.911574+00	\N
9375d67f-3d0c-4e6f-8e84-ac99cb65641d	Technology	\N	Technology and IT teams	t	2025-11-30 14:13:46.911574+00	2025-11-30 14:13:46.911574+00	\N
11561e77-c20a-41da-8910-543b3d2f390b	Support Functions	\N	Support, marketing, sales, and HR	t	2025-11-30 14:13:46.911574+00	2025-11-30 14:13:46.911574+00	\N
\.


--
-- Data for Name: modules; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modules (id, module_key, module_name, description, icon, is_active, display_order, created_at, updated_at, meta_info, module_type, tier, category, tier_2_dependencies, is_enabled, is_beta, requires_special_permission, created_by, updated_by) FROM stdin;
e1759656-f97c-4001-a497-37d400a2754e	chat	Chat	RAG-powered chat interface	MessageSquare	t	1	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
c0995c51-cddc-42a6-9af3-d788019b2dab	history	Chat History	View and manage chat conversations	History	t	2	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
2834806e-937d-4a0d-8d7e-084454dc5b2f	upload	Upload Files	Upload documents for RAG	Upload	t	3	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
1c8f5816-c5a6-4de2-927c-d3a0899dea0d	scrape	Web Scraping	Extract data from websites	Globe	t	4	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
3ffa6ac1-b253-4aa3-a923-a641d32f966d	estimator	Project Estimator	Estimate project scope and effort	Calculator	t	5	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
2e7bf166-8c80-4e50-b97c-5522a8b85b12	evaluation	Evaluation	RAG evaluation metrics	BarChart3	t	6	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
dd78b891-a71c-4cea-88bb-b1501d9e596b	tools	Tool Usage	Tool usage analytics	Wrench	t	7	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
28d57d88-ccee-4356-979e-1b5e33adc2d2	weights	Weights Config	RAG system configuration	Sliders	t	8	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
f3549bcf-77ac-48e4-b71c-f088623ada8f	admin	Admin	System administration	Shield	t	9	2025-11-30 14:13:46.019785+00	2025-11-30 14:13:46.019785+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
ba04df74-e0ee-45e9-9634-331af0848c2a	model_finetuning	Fine-Tuning	Model fine-tuning and adaptation	Settings	t	10	2025-12-15 18:25:50.467964+00	2025-12-15 18:25:50.467964+00	\N	\N	\N	\N	\N	t	f	f	\N	\N
6ec2f00f-4028-4014-ab8f-b697fef5e295	cru	CRU POC	Construction resource utilization and project optimization	\N	t	0	2026-01-01 11:20:41.183612+00	2026-01-01 11:20:41.183612+00	\N	tier3	3	Construction	{construction-monitor,estimator-one-au,mine-scope}	t	f	f	\N	\N
3862781f-cec4-4253-aad4-6c7e00e0f9ca	grant-thornton	Grant Thornton POC	Financial audit and compliance automation	\N	t	0	2026-01-01 11:20:41.183612+00	2026-01-01 11:20:41.183612+00	\N	tier3	3	Finance	{financial-anomaly,legal-document,document-intelligence}	t	f	f	\N	\N
cc2a9403-8d84-40b9-a16d-86a7b6da14e2	gt-motive	GT Motive POC	Automotive damage assessment and repair estimation	\N	t	0	2026-01-01 11:20:41.183612+00	2026-01-01 11:20:41.183612+00	\N	tier3	3	Insurance	{insurance-risk,document-intelligence,predictive-analytics}	t	f	f	\N	\N
31e434bf-12b0-4973-b5c9-9baf894b7a76	solera	Solera POC	Insurance claims workflow automation and fraud detection	\N	t	0	2026-01-01 11:20:41.183612+00	2026-01-01 11:20:41.183612+00	\N	tier3	3	Insurance	{insurance-risk,document-intelligence,financial-anomaly}	t	f	f	\N	\N
06ea73eb-501b-48bb-9445-31fbed6335df	construction-monitor	Construction Monitor POC	Real-time project monitoring and progress tracking	\N	t	0	2026-01-01 11:20:41.183612+00	2026-01-01 11:20:41.183612+00	\N	tier3	3	Construction	{estimator-one-au,mine-scope,document-intelligence}	t	f	f	\N	\N
a46306c6-f0eb-4480-b2ce-d1821a6d2a95	document-intelligence	Document Intelligence	Advanced document processing and analysis	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Core	{}	t	f	f	\N	\N
40bd232f-8537-4bb2-abd8-02fbefec5062	generic-rag	Generic RAG	General-purpose retrieval-augmented generation	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Core	{}	t	f	f	\N	\N
f252b9b5-c489-41cb-9cff-c5ffe1ad439c	predictive-analytics	Predictive Analytics	Machine learning-based predictions and forecasting	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Analytics	{}	t	f	f	\N	\N
e0e85519-428c-4ed6-baaf-0c751b9bcda1	multilingual-translator	Multilingual Translator	Multi-language translation and localization	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Language	{}	t	f	f	\N	\N
9ba0538f-3c73-4744-8e15-516030435019	financial-anomaly	Financial Anomaly Detection	Fraud detection and financial anomaly identification	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Finance	{}	t	f	f	\N	\N
0b09e7dd-ce17-41ed-be06-10fdaf3dc25f	legal-document	Legal Document Processing	Contract analysis and legal document management	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Legal	{}	t	f	f	\N	\N
f8b5ff2b-f96f-4a1e-8615-3144c0ff604a	insurance-risk	Insurance Risk Assessment	Risk scoring and insurance claims analysis	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Insurance	{}	t	f	f	\N	\N
5fcd8033-c62c-4f96-8c7b-a3358ea242b9	estimator-one-au	EstimatorOne (AU)	Australian construction cost estimation	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Construction	{}	t	f	f	\N	\N
de230e50-243c-4207-b894-04c6f680bc03	mine-scope	Mine Scope Analysis	Mining project scope and resource planning	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 11:20:41.19204+00	\N	tier2	2	Mining	{}	t	f	f	\N	\N
7d6beb86-4c72-408b-a2e4-00a4ddb726d1	british-council	British Council POC	Educational content delivery and assessment platform	\N	t	0	2026-01-01 11:20:41.183612+00	2026-01-01 16:45:12.840033+00	\N	tier3	3	Education	{educational-content,generic-rag,multilingual-translator}	t	f	f	\N	\N
f0758459-9a0e-44fb-a249-e61ee697c5c6	educational-content	Educational Content Management	Course content delivery and assessment	\N	t	0	2026-01-01 11:20:41.19204+00	2026-01-01 12:43:56.727451+00	\N	tier2	2	Education	{}	t	f	f	\N	\N
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, name, parent_role_id, description, is_system_role, created_at, updated_at) FROM stdin;
654ae943-c059-4e40-990d-ae2ea35c4364	Admin	\N	Full system access - can manage all resources and users	t	2025-11-30 14:13:46.908707+00	2025-11-30 14:13:46.908707+00
b043de62-7fe7-4609-9b80-bee71a4f7271	CxO	\N	Executive level access - high-level analytics and reporting	t	2025-11-30 14:13:46.908707+00	2025-11-30 14:13:46.908707+00
7488d32c-e5e4-44f2-99bf-291c04f1ae9c	Manager	\N	Department manager - can manage team resources	t	2025-11-30 14:13:46.908707+00	2025-11-30 14:13:46.908707+00
dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	User	\N	Standard user - can use application features	t	2025-11-30 14:13:46.908707+00	2025-11-30 14:13:46.908707+00
87c95c22-46f3-44f4-80be-8e9750d77fdd	ReadOnly	\N	Read-only access - cannot modify data	t	2025-11-30 14:13:46.908707+00	2025-11-30 14:13:46.908707+00
\.


--
-- Data for Name: role_module_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_module_permissions (id, role_id, module_id, can_read, can_write, can_delete, can_share, created_at, updated_at) FROM stdin;
b0c90fc6-269f-4a41-9b7c-f90dce438509	654ae943-c059-4e40-990d-ae2ea35c4364	e1759656-f97c-4001-a497-37d400a2754e	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
b7dbf60d-0298-4302-bf16-cf0b70f85398	654ae943-c059-4e40-990d-ae2ea35c4364	c0995c51-cddc-42a6-9af3-d788019b2dab	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
e7c5e0b0-f50d-4fa6-8191-acfc0210b966	654ae943-c059-4e40-990d-ae2ea35c4364	2834806e-937d-4a0d-8d7e-084454dc5b2f	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
5b5a0d86-32f0-495c-a553-e64791ad20e6	654ae943-c059-4e40-990d-ae2ea35c4364	1c8f5816-c5a6-4de2-927c-d3a0899dea0d	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
a6afa11d-619d-4fd9-98a0-95e99628584c	654ae943-c059-4e40-990d-ae2ea35c4364	3ffa6ac1-b253-4aa3-a923-a641d32f966d	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
4e8e238f-f1e7-40bd-a633-b13cd210532c	654ae943-c059-4e40-990d-ae2ea35c4364	2e7bf166-8c80-4e50-b97c-5522a8b85b12	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
218ca871-75a7-4e9e-9f7f-1dd4a7dafdaf	654ae943-c059-4e40-990d-ae2ea35c4364	dd78b891-a71c-4cea-88bb-b1501d9e596b	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
4538a6aa-7f6d-440c-9ca7-2c5ae8d8f1f8	654ae943-c059-4e40-990d-ae2ea35c4364	28d57d88-ccee-4356-979e-1b5e33adc2d2	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
a64cc615-2cd0-4956-b252-193eb7d5bbbd	654ae943-c059-4e40-990d-ae2ea35c4364	f3549bcf-77ac-48e4-b71c-f088623ada8f	t	t	t	t	2025-11-30 14:13:46.920744+00	2025-11-30 14:13:46.920744+00
033ee9a8-699e-4f47-b214-8ffdfb76dbb1	b043de62-7fe7-4609-9b80-bee71a4f7271	e1759656-f97c-4001-a497-37d400a2754e	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
7c5185ff-7be0-41ff-834a-c77d84721f2c	b043de62-7fe7-4609-9b80-bee71a4f7271	c0995c51-cddc-42a6-9af3-d788019b2dab	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
5480d63b-fe8b-4a97-a883-d92dab5e5179	b043de62-7fe7-4609-9b80-bee71a4f7271	2834806e-937d-4a0d-8d7e-084454dc5b2f	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
c5b81e3c-dc28-44bd-a0e4-fd37cd0bc73f	b043de62-7fe7-4609-9b80-bee71a4f7271	1c8f5816-c5a6-4de2-927c-d3a0899dea0d	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
6f7d2e8b-cbce-4599-83e6-0d8feb5c0efa	b043de62-7fe7-4609-9b80-bee71a4f7271	3ffa6ac1-b253-4aa3-a923-a641d32f966d	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
6396b688-3173-4df2-9fe6-65257422b04f	b043de62-7fe7-4609-9b80-bee71a4f7271	2e7bf166-8c80-4e50-b97c-5522a8b85b12	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
6a6332e7-c0be-4967-aa41-41b79a46f67a	b043de62-7fe7-4609-9b80-bee71a4f7271	dd78b891-a71c-4cea-88bb-b1501d9e596b	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
725a2f00-23be-40dd-89c4-f0af1f8f4e05	b043de62-7fe7-4609-9b80-bee71a4f7271	28d57d88-ccee-4356-979e-1b5e33adc2d2	t	t	t	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
595b7ecf-3777-439f-b729-6eb8b3fdd400	b043de62-7fe7-4609-9b80-bee71a4f7271	f3549bcf-77ac-48e4-b71c-f088623ada8f	t	t	f	t	2025-12-01 09:40:11.488012+00	2025-12-01 09:40:11.488012+00
ecbcd1ea-4553-4113-9c4d-80449b7a06e1	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	e1759656-f97c-4001-a497-37d400a2754e	t	t	f	t	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
4b32da9e-25b7-4289-8993-b9f5b2a816c0	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	c0995c51-cddc-42a6-9af3-d788019b2dab	t	t	f	f	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
0a129c8a-b552-4dd1-9224-57455934d1c3	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	2834806e-937d-4a0d-8d7e-084454dc5b2f	t	t	f	f	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
d703f6d8-bc52-407a-8c00-d759d7466910	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	1c8f5816-c5a6-4de2-927c-d3a0899dea0d	t	t	f	t	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
acbccc51-c5be-4508-8ccc-e4c475d0d2cf	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	3ffa6ac1-b253-4aa3-a923-a641d32f966d	t	t	f	t	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
31171752-9895-494a-b852-8d67e517c4ee	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	2e7bf166-8c80-4e50-b97c-5522a8b85b12	t	t	f	t	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
b87c3912-27b7-49fe-8fe1-71b8e6481d06	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	dd78b891-a71c-4cea-88bb-b1501d9e596b	t	t	f	f	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
7d33be69-9819-4960-8494-5c68808eb64d	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	28d57d88-ccee-4356-979e-1b5e33adc2d2	t	t	f	f	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
682cb73b-aea5-4a83-a841-9a4cad0ae3e7	7488d32c-e5e4-44f2-99bf-291c04f1ae9c	f3549bcf-77ac-48e4-b71c-f088623ada8f	t	f	f	f	2025-12-01 09:40:11.493929+00	2025-12-01 09:40:11.493929+00
653ea150-8408-43f6-86a8-db520b67a566	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	e1759656-f97c-4001-a497-37d400a2754e	t	t	f	t	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
ddfb813d-4485-4c33-a6c5-7e95ed19b9d9	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	c0995c51-cddc-42a6-9af3-d788019b2dab	t	t	f	f	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
1a07d363-9673-40ca-b0d2-ed4726616791	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	2834806e-937d-4a0d-8d7e-084454dc5b2f	t	t	f	f	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
6b765dba-b9c3-4e26-982c-c10d9d7058b6	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	1c8f5816-c5a6-4de2-927c-d3a0899dea0d	t	t	f	t	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
106cf593-a268-46ec-847c-65eadeb5e792	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	3ffa6ac1-b253-4aa3-a923-a641d32f966d	t	f	f	t	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
e3ea1501-5dba-4fbd-9a16-04f354e12907	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	2e7bf166-8c80-4e50-b97c-5522a8b85b12	t	f	f	f	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
80dc7d76-0c24-491b-8c68-6a096acdfce4	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	dd78b891-a71c-4cea-88bb-b1501d9e596b	t	f	f	f	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
3f0401ed-5bb3-428b-8ca3-29d7a552b307	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	28d57d88-ccee-4356-979e-1b5e33adc2d2	t	f	f	f	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
f277abca-2c01-4fc5-9946-480f1703a051	dd9f8335-f0eb-4e4a-a6b8-cd80df673d40	f3549bcf-77ac-48e4-b71c-f088623ada8f	f	f	f	f	2025-12-01 09:40:11.496221+00	2025-12-01 09:40:11.496221+00
6bd173ba-4c00-4ebc-9d24-cc689c9e9cae	87c95c22-46f3-44f4-80be-8e9750d77fdd	e1759656-f97c-4001-a497-37d400a2754e	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
34cb3ebc-0388-470a-8d63-033d7b2b206e	87c95c22-46f3-44f4-80be-8e9750d77fdd	c0995c51-cddc-42a6-9af3-d788019b2dab	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
a633d37b-b093-47e8-a7f0-9814c61cec89	87c95c22-46f3-44f4-80be-8e9750d77fdd	2834806e-937d-4a0d-8d7e-084454dc5b2f	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
190a95a3-a0db-40aa-b582-11005e878e77	87c95c22-46f3-44f4-80be-8e9750d77fdd	1c8f5816-c5a6-4de2-927c-d3a0899dea0d	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
6eef8cbd-f9cc-4d9f-813c-3ffef109ee01	87c95c22-46f3-44f4-80be-8e9750d77fdd	3ffa6ac1-b253-4aa3-a923-a641d32f966d	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
793646c7-2af4-4b9a-b7ca-200c8e5ec855	87c95c22-46f3-44f4-80be-8e9750d77fdd	2e7bf166-8c80-4e50-b97c-5522a8b85b12	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
d60a9f98-c77d-464f-8f7c-bfef667e6e82	87c95c22-46f3-44f4-80be-8e9750d77fdd	dd78b891-a71c-4cea-88bb-b1501d9e596b	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
2b2217c7-e93e-4618-89c0-dc2b32d0988a	87c95c22-46f3-44f4-80be-8e9750d77fdd	28d57d88-ccee-4356-979e-1b5e33adc2d2	t	f	f	f	2025-12-01 09:40:11.497414+00	2025-12-01 09:40:11.497414+00
487a20ff-9103-4fa8-9e11-34c4dd04228b	654ae943-c059-4e40-990d-ae2ea35c4364	ba04df74-e0ee-45e9-9634-331af0848c2a	t	t	t	t	2025-12-15 18:26:14.867039+00	2025-12-15 18:26:14.867039+00
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.teams (id, name, code, department_id, team_lead_id, description, is_active, created_at, updated_at) FROM stdin;
7b62e55f-76eb-47a2-bc67-f414c5b9343b	Backend Development	BACKEND	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	API and server-side development	t	\N	\N
0d2b79fa-0afd-48f0-ad87-b710312603fa	Frontend Development	FRONTEND	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	UI/UX and client-side development	t	\N	\N
36b37d88-b274-4600-a6b5-98e13bcdc5ba	ITM1	ITM1	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
ccb8dedd-9ace-4256-8963-3574aa68af76	ITM2	ITM2	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
3fe96c39-8b26-441f-b579-54d58258a920	ITM6	ITM6	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
609c47c6-a6b9-4445-b9cb-f1a979f75606	ITM7	ITM7	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
88b06c41-0a82-4e83-9760-8b6fa787b80b	ITM9	ITM9	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
201051c9-c0a8-4dff-bb6f-c14ad81cba3e	ITM10	ITM10	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
56843886-e89f-48af-abce-cca95a80c006	ITM12	ITM12	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
9e1cafdc-8e86-4123-9366-535eaa67f099	ALF	ALF	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
96d818ff-595b-4c6a-87cf-fb3bc1f9d821	Air Business Distribution	AIR_BUSINESS_DISTRIBUTION	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
9b005ef7-73cc-4f56-911e-f19095e200ea	DMS Construction Data Research	DMS_CONSTRUCTION_DATA_RESEARCH	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
4370a923-b747-4ea8-824c-9bb724ee2465	DODs	DODS	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
4d905526-9b8a-4c36-a266-fd1921538d09	Glenigan FRO	GLENIGAN_FRO	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
8e549775-9bc7-49e0-a64e-8f638bc6a2fe	HSJ	HSJ	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
ef7682c9-a3d4-4524-9c5c-edbde323d2c1	HSJ On Medica	HSJ_ON_MEDICA	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
39c8f65b-f35a-484b-85b9-f7dad11229de	Haymarket	HAYMARKET	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
01944a9d-b610-4354-9c7f-daf3164a8054	Informa Connect - Data Research	INFORMA_CONNECT_DATA_RESEARCH	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
5f0c1374-0490-4b28-b4f2-0460962f8680	LLI Data	LLI_DATA	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
f6c8de17-1e42-475e-8933-c529b1e16828	Leadership	LEADERSHIP	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
12aa8ace-3659-4c3a-8808-1024cffb8737	Leadscale	LEADSCALE	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
69958e76-6ece-44cd-9f4b-22891eab7b3a	Political Engagement - Research Support	POLITICAL_ENGAGEMENT_RESEARCH_SUPPORT	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
ad56890c-e943-4198-92e7-8ddb51b38345	Quality	QUALITY	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
b059cf90-18db-408f-8f5a-ed6ed0f6f096	Tactical Data	TACTICAL_DATA	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
52d707c1-a4af-40e8-be60-ec662b2a4029	Tactical Data Research	TACTICAL_DATA_RESEARCH	0f4c1f28-a193-4075-907c-0a5916f2b62f	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
13dd829b-603e-4aff-b5ef-c26b8e2336e3	Marketing	MARKETING	11561e77-c20a-41da-8910-543b3d2f390b	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
a26d95fb-4c3d-48c7-976a-797261b27f9a	Sales	SALES	11561e77-c20a-41da-8910-543b3d2f390b	\N	\N	\N	2025-12-20 06:31:44.380844+00	\N
44ce93fd-5f86-4d40-bbc2-f52409973cd0	ITM11	ITM11	9375d67f-3d0c-4e6f-8e84-ac99cb65641d	\N	\N	t	2025-12-20 06:23:53.380965+00	\N
\.


--
-- PostgreSQL database dump complete
--

\unrestrict nWWgmy1aAgxbIGcHuAi2kVeEHgOC92JIABtfP7K7xh8dMbK52edwLd4hf6vCvww

