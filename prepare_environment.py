"""
Prepare the Azure AI Foundry environment for the Contoso Field Services workshop.

This is intentionally a single, rerunnable Python file: it creates the Azure
resource/project and model deployments, then prepares Foundry project assets
(prompt agents, toolbox, evaluation dataset/evaluation, and optional RAG
knowledge assets) for use in the Foundry portal playgrounds.

Authentication:
    az login --tenant 1b9b5045-f788-4fc4-8a5b-b04bf80ecd9a
    python prepare_environment.py

The defaults below reflect the active Azure CLI context when this file was
created. Override them with environment variables or command-line arguments.
No client secrets or API keys are stored in this file.

Install:
    pip install azure-identity azure-mgmt-resource azure-mgmt-cognitiveservices
    pip install azure-ai-projects azure-search-documents openai python-dotenv
    pip install pypdf

Optional:
    - Set AZURE_SEARCH_ENDPOINT and DEMO_DATA_DIR to build the Foundry IQ
      index/knowledge source/knowledge base from local workshop documents.
    - Set FOUNDRY_RAI_POLICY_NAME to create the guarded agent version.
    - Set CREATE_EVALUATION=true after the evaluation dataset is available.

The script does not deploy a hosted-agent container. A hosted agent is an
application artifact with its own source, image/zip, identity and release
configuration; the companion code in the blog can be deployed after this
script has prepared the shared project assets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import (
    Deployment,
    DeploymentModel,
    DeploymentProperties,
    Sku,
)
from azure.mgmt.resource import ResourceManagementClient


DEFAULTS = {
    "tenant_id": "1b9b5045-f788-4fc4-8a5b-b04bf80ecd9a",
    "subscription_id": "c396918f-565f-458c-87b5-4dfe9b6959a8",
    "location": "eastus",
    "resource_group": "rg-training-foundry",
    "foundry_resource": "foundry-training-contoso",
    "foundry_project": "contoso-field-service",
    "fast_model": "gpt-5.1-mini",
    "fast_version": "2025-04-14",
    "quality_model": "gpt-5.1",
    "quality_version": "2025-04-14",
    "embedding_model": "text-embedding-3-small",
    "embedding_version": "1",
    "sku_name": "GlobalStandard",
    "capacity": "10",
    "project_api_version": "2025-04-01-preview",
}


def value(name: str, default_key: str | None = None) -> str:
    env_name = name.upper()
    if env_name in os.environ and os.environ[env_name].strip():
        return os.environ[env_name].strip()
    if default_key is not None:
        return DEFAULTS[default_key]
    raise RuntimeError(f"Missing required setting: {env_name}")


def optional(name: str, default: str = "") -> str:
    return os.environ.get(name.upper(), default).strip()


def resource_id(subscription_id: str, resource_group: str, provider: str, name: str) -> str:
    return (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/{provider}/{name}"
    )


def ensure_resource_group(credential: DefaultAzureCredential, subscription_id: str) -> None:
    client = ResourceManagementClient(credential, subscription_id)
    rg_name = value("AZURE_RESOURCE_GROUP", "resource_group")
    location = value("AZURE_LOCATION", "location")
    client.resource_groups.create_or_update(rg_name, {"location": location})
    print(f"[ok] resource group: {rg_name}")


def ensure_foundry_resource(
    credential: DefaultAzureCredential,
    subscription_id: str,
) -> None:
    client = CognitiveServicesManagementClient(
        credential=credential,
        subscription_id=subscription_id,
        api_version=value("COGNITIVE_SERVICES_API_VERSION", "project_api_version"),
    )
    rg_name = value("AZURE_RESOURCE_GROUP", "resource_group")
    resource_name = value("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource")
    location = value("AZURE_LOCATION", "location")
    result = client.accounts.begin_create(
        resource_group_name=rg_name,
        account_name=resource_name,
        account={
            "location": location,
            "kind": "AIServices",
            "sku": {"name": "S0"},
            "identity": {"type": "SystemAssigned"},
            "properties": {
                "allowProjectManagement": True,
                "customSubDomainName": resource_name,
                "publicNetworkAccess": "Enabled",
            },
        },
    ).result()
    print(f"[ok] Foundry resource: {result.name} ({result.location})")


def ensure_project(credential: DefaultAzureCredential, subscription_id: str) -> None:
    client = CognitiveServicesManagementClient(
        credential=credential,
        subscription_id=subscription_id,
        api_version=value("COGNITIVE_SERVICES_API_VERSION", "project_api_version"),
    )
    result = client.projects.begin_create(
        resource_group_name=value("AZURE_RESOURCE_GROUP", "resource_group"),
        account_name=value("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource"),
        project_name=value("AZURE_FOUNDRY_PROJECT_NAME", "foundry_project"),
        project={
            "location": value("AZURE_LOCATION", "location"),
            "identity": {"type": "SystemAssigned"},
            "properties": {},
        },
    ).result()
    print(f"[ok] Foundry project: {result.name}")


def ensure_deployment(
    credential: DefaultAzureCredential,
    subscription_id: str,
    deployment_name: str,
    model_name: str,
    model_version: str,
    capacity: int,
) -> None:
    client = CognitiveServicesManagementClient(
        credential=credential,
        subscription_id=subscription_id,
        api_version=value("COGNITIVE_SERVICES_API_VERSION", "project_api_version"),
    )
    deployment = client.deployments.begin_create_or_update(
        resource_group_name=value("AZURE_RESOURCE_GROUP", "resource_group"),
        account_name=value("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource"),
        deployment_name=deployment_name,
        deployment=Deployment(
            sku=Sku(name=value("MODEL_SKU_NAME", "sku_name"), capacity=capacity),
            properties=DeploymentProperties(
                model=DeploymentModel(
                    format="OpenAI",
                    name=model_name,
                    version=model_version,
                )
            ),
        ),
    ).result()
    print(f"[ok] deployment: {deployment.name} ({deployment.properties.provisioning_state})")


def project_endpoint(subscription_id: str) -> str:
    configured = optional("AZURE_AI_PROJECT_ENDPOINT")
    if configured:
        return configured.rstrip("/")
    resource_name = value("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource")
    project_name = value("AZURE_FOUNDRY_PROJECT_NAME", "foundry_project")
    return (
        f"https://{resource_name}.services.ai.azure.com/api/projects/"
        f"{project_name}"
    )


def make_project_client(credential: DefaultAzureCredential) -> Any:
    try:
        from azure.ai.projects import AIProjectClient
    except ImportError as exc:
        raise RuntimeError(
            "Install azure-ai-projects before creating Foundry project assets."
        ) from exc
    return AIProjectClient(
        endpoint=project_endpoint(value("AZURE_SUBSCRIPTION_ID", "subscription_id")),
        credential=credential,
        allow_preview=True,
    )


def create_agents(project: Any, fast_deployment: str, quality_deployment: str) -> dict[str, str]:
    from azure.ai.projects.models import PromptAgentDefinition

    instructions = """You are the Contoso Field Services Assistant.

Help field engineers and support managers answer support policy, warranty,
troubleshooting, and escalation questions.

Rules:
- Use connected knowledge for factual answers and say when evidence is absent.
- Use tools only when needed and explain important assumptions.
- Never invent warranty, safety, escalation, customer, or account policy.
- Draft business actions only; never submit consequential actions without human approval.
- Ask for missing information when a scenario is ambiguous.
- Keep answers concise and operational.
"""
    names = {
        "prompt": optional("FOUNDRY_AGENT_NAME", "contoso-field-service-agent"),
        "quality": optional("FOUNDRY_QUALITY_AGENT_NAME", "contoso-field-service-quality"),
    }
    created: dict[str, str] = {}
    for agent_name, model in ((names["prompt"], fast_deployment), (names["quality"], quality_deployment)):
        agent = project.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(model=model, instructions=instructions),
        )
        created[agent_name] = str(getattr(agent, "version", "1"))
        print(f"[ok] agent: {agent_name} version {created[agent_name]}")

    rai_policy_name = optional("FOUNDRY_RAI_POLICY_NAME")
    if rai_policy_name:
        from azure.ai.projects.models import RaiConfig

        guarded_name = optional("FOUNDRY_GUARDED_AGENT_NAME", "contoso-field-service-guarded")
        guarded = project.agents.create_version(
            agent_name=guarded_name,
            definition=PromptAgentDefinition(
                model=fast_deployment,
                instructions=instructions,
                rai_config=RaiConfig(rai_policy_name=rai_policy_name),
            ),
        )
        created[guarded_name] = str(getattr(guarded, "version", "1"))
        print(f"[ok] guarded agent: {guarded_name} version {created[guarded_name]}")
    else:
        print("[info] guarded agent skipped; set FOUNDRY_RAI_POLICY_NAME to use an existing RAI policy")
    return created


def create_toolbox(project: Any) -> str:
    from azure.ai.projects.models import MCPToolboxTool, ToolSearchToolboxTool, WebSearchToolboxTool

    toolbox_name = optional("FOUNDRY_TOOLBOX_NAME", "contoso-field-service-tools")
    version = project.toolboxes.create_version(
        name=toolbox_name,
        description="Workshop toolbox for web search, Microsoft Learn and discoverable tools.",
        tools=[
            WebSearchToolboxTool(name="web-search"),
            MCPToolboxTool(
                server_label="microsoft-learn",
                server_url="https://learn.microsoft.com/api/mcp",
                require_approval="never",
            ),
            ToolSearchToolboxTool(name="tool-search"),
        ],
    )
    print(f"[ok] toolbox: {toolbox_name} version {version.version}")
    return str(version.version)


def create_knowledge_assets(project: Any) -> dict[str, str]:
    """Create the workshop's Azure AI Search index and Foundry IQ assets."""
    search_endpoint = optional("AZURE_SEARCH_ENDPOINT")
    data_dir = Path(optional("DEMO_DATA_DIR", str(Path.cwd() / "data")))
    if not search_endpoint:
        print("[info] knowledge assets skipped; set AZURE_SEARCH_ENDPOINT")
        return {}
    if not data_dir.is_dir():
        print(f"[info] knowledge assets skipped; data folder not found: {data_dir}")
        return {}
    source_files = sorted(
        path for path in data_dir.iterdir() if path.suffix.lower() in {".md", ".txt", ".pdf"}
    )
    if not source_files:
        print(f"[info] knowledge assets skipped; no .md, .txt or .pdf files in {data_dir}")
        return {}

    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        AzureOpenAIVectorizer,
        AzureOpenAIVectorizerParameters,
        HnswAlgorithmConfiguration,
        SearchField,
        SearchIndex,
        SemanticConfiguration,
        SemanticField,
        SemanticPrioritizedFields,
        SemanticSearch,
        VectorSearch,
        VectorSearchProfile,
    )

    index_name = optional("SEARCH_INDEX_NAME", "contoso-service-index")
    knowledge_source_name = optional("KNOWLEDGE_SOURCE_NAME", "contoso-service-knowledge-source")
    knowledge_base_name = optional("KNOWLEDGE_BASE_NAME", "contoso-service-knowledge")
    vector_profile_name = "contoso-hnsw-profile"
    vectorizer_name = "contoso-aoai-vectorizer"
    semantic_name = "contoso-semantic"
    embedding_deployment = optional("EMBEDDING_DEPLOYMENT_NAME", "contoso-embedding")
    dimensions = int(optional("EMBEDDING_DIMENSIONS", "1536"))
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint=search_endpoint.rstrip("/"), credential=credential)
    index_client.create_or_update_index(
        SearchIndex(
            name=index_name,
            fields=[
                SearchField(name="id", type="Edm.String", key=True, filterable=True),
                SearchField(name="content", type="Edm.String", searchable=True, retrievable=True),
                SearchField(name="source", type="Edm.String", searchable=True, retrievable=True),
                SearchField(
                    name="content_vector",
                    type="Collection(Edm.Single)",
                    searchable=True,
                    retrievable=False,
                    stored=False,
                    vector_search_dimensions=dimensions,
                    vector_search_profile_name=vector_profile_name,
                ),
            ],
            vector_search=VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name=vector_profile_name,
                        algorithm_configuration_name="contoso-hnsw",
                        vectorizer_name=vectorizer_name,
                    )
                ],
                algorithms=[HnswAlgorithmConfiguration(name="contoso-hnsw")],
                vectorizers=[
                    AzureOpenAIVectorizer(
                        vectorizer_name=vectorizer_name,
                        parameters=AzureOpenAIVectorizerParameters(
                            resource_url=(
                                f"https://{value('AZURE_FOUNDRY_RESOURCE_NAME', 'foundry_resource')}"
                                ".services.ai.azure.com"
                            ),
                            deployment_name=embedding_deployment,
                            model_name=value("EMBEDDING_MODEL_NAME", "embedding_model"),
                        ),
                    )
                ],
            ),
            semantic_search=SemanticSearch(
                default_configuration_name=semantic_name,
                configurations=[
                    SemanticConfiguration(
                        name=semantic_name,
                        prioritized_fields=SemanticPrioritizedFields(
                            content_fields=[SemanticField(field_name="content")]
                        ),
                    )
                ],
            ),
        )
    )

    texts: list[dict[str, str]] = []
    for source_file in source_files:
        if source_file.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            content = "\n".join(page.extract_text() or "" for page in PdfReader(source_file).pages)
        else:
            content = source_file.read_text(encoding="utf-8")
        for number, start in enumerate(range(0, len(content), 1200)):
            chunk = content[start : start + 1200].strip()
            if chunk:
                texts.append({"id": f"{source_file.stem}-{number}", "content": chunk, "source": source_file.name})
    openai_client = project.get_openai_client()
    embeddings = openai_client.embeddings.create(
        model=embedding_deployment,
        input=[item["content"] for item in texts],
    )
    documents = [
        {**item, "content_vector": embedding.embedding}
        for item, embedding in zip(texts, embeddings.data)
    ]
    SearchClient(
        endpoint=search_endpoint.rstrip("/"),
        index_name=index_name,
        credential=credential,
    ).upload_documents(documents=documents)

    from azure.search.documents.indexes.models import (
        KnowledgeBase,
        KnowledgeBaseAzureOpenAIModel,
        KnowledgeSourceReference,
        SearchIndexFieldReference,
        SearchIndexKnowledgeSource,
        SearchIndexKnowledgeSourceParameters,
    )
    from azure.search.documents.knowledgebases.models import (
        KnowledgeRetrievalAutoReasoningEffort,
        KnowledgeRetrievalOutputMode,
    )

    index_client.create_or_update_knowledge_source(
        SearchIndexKnowledgeSource(
            name=knowledge_source_name,
            description="Contoso Field Services policy and troubleshooting documents.",
            search_index_parameters=SearchIndexKnowledgeSourceParameters(
                search_index_name=index_name,
                semantic_configuration_name=semantic_name,
                source_data_fields=[
                    SearchIndexFieldReference(name="content"),
                    SearchIndexFieldReference(name="source"),
                ],
            ),
        )
    )
    index_client.create_or_update_knowledge_base(
        KnowledgeBase(
            name=knowledge_base_name,
            description="Grounded Contoso Field Services support knowledge.",
            retrieval_instructions="Retrieve precise policy, warranty and troubleshooting facts.",
            answer_instructions="Answer only from retrieved content and include the source filename.",
            output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
            knowledge_sources=[KnowledgeSourceReference(name=knowledge_source_name)],
            models=[
                KnowledgeBaseAzureOpenAIModel(
                    azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                        resource_url=(
                            f"https://{value('AZURE_FOUNDRY_RESOURCE_NAME', 'foundry_resource')}"
                            ".services.ai.azure.com"
                        ),
                        deployment_name=optional("QUALITY_DEPLOYMENT_NAME", "contoso-quality"),
                        model_name=value("QUALITY_MODEL_NAME", "quality_model"),
                    )
                )
            ],
            retrieval_reasoning_effort=KnowledgeRetrievalAutoReasoningEffort(),
        )
    )
    print(f"[ok] knowledge base: {knowledge_base_name} ({len(documents)} chunks)")
    return {
        "search_index": index_name,
        "knowledge_source": knowledge_source_name,
        "knowledge_base": knowledge_base_name,
    }


def upload_evaluation_assets(project: Any) -> dict[str, str]:
    dataset_path = optional("FOUNDRY_DATASET_PATH")
    if not dataset_path:
        print("[info] evaluation dataset skipped; set FOUNDRY_DATASET_PATH to a JSONL file")
        return {}
    dataset_name = optional("FOUNDRY_DATASET_NAME", "contoso-field-service-golden")
    dataset_version = optional("FOUNDRY_DATASET_VERSION", "1")
    dataset = project.datasets.upload_file(
        name=dataset_name,
        version=dataset_version,
        file_path=dataset_path,
    )
    print(f"[ok] evaluation dataset: {dataset.name} version {dataset.version}")
    return {"dataset_id": str(dataset.id), "dataset_name": dataset_name}


def create_evaluation(project: Any, deployment: str, dataset: dict[str, str]) -> str:
    if not dataset or optional("CREATE_EVALUATION", "true").lower() not in {"1", "true", "yes"}:
        print("[info] evaluation definition skipped")
        return ""
    from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
    from openai.types.eval_create_params import TestingCriterionTextSimilarity

    criteria = [
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="Coherence",
            evaluator_name="builtin.coherence",
            initialization_parameters={"deployment_name": deployment},
            data_mapping={"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="Groundedness",
            evaluator_name="builtin.groundedness",
            initialization_parameters={"deployment_name": deployment},
            data_mapping={
                "query": "{{item.query}}",
                "response": "{{sample.output_text}}",
                "context": "{{item.context}}",
            },
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="Safety",
            evaluator_name="builtin.violence",
            data_mapping={"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        ),
        TestingCriterionTextSimilarity(
            type="text_similarity",
            name="Reference answer similarity",
            input="{{sample.output_text}}",
            reference="{{item.expected_answer}}",
            evaluation_metric="fuzzy_match",
            pass_threshold=0.65,
        ),
    ]
    evaluation = project.get_openai_client().evals.create(
        name=optional("FOUNDRY_EVALUATION_NAME", "contoso-field-service-baseline"),
        testing_criteria=criteria,
        data_source_config={
            "type": "custom",
            "item_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {"type": "string"},
                    "expected_answer": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["query", "context", "expected_answer", "category"],
            },
            "include_sample_schema": True,
        },
    )
    print(f"[ok] evaluation: {evaluation.id}")
    return str(evaluation.id)


def write_manifest(
    agents: dict[str, str],
    dataset: dict[str, str],
    evaluation_id: str,
    toolbox_version: str,
    knowledge: dict[str, str],
) -> None:
    manifest_path = Path(optional("FOUNDRY_MANIFEST_PATH", "foundry-training-manifest.json"))
    manifest = {
        "tenant_id": value("AZURE_TENANT_ID", "tenant_id"),
        "subscription_id": value("AZURE_SUBSCRIPTION_ID", "subscription_id"),
        "resource_group": value("AZURE_RESOURCE_GROUP", "resource_group"),
        "location": value("AZURE_LOCATION", "location"),
        "foundry_resource": value("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource"),
        "foundry_project": value("AZURE_FOUNDRY_PROJECT_NAME", "foundry_project"),
        "project_endpoint": project_endpoint(value("AZURE_SUBSCRIPTION_ID", "subscription_id")),
        "deployments": {
            "fast": optional("FAST_DEPLOYMENT_NAME", "contoso-fast"),
            "quality": optional("QUALITY_DEPLOYMENT_NAME", "contoso-quality"),
            "embedding": optional("EMBEDDING_DEPLOYMENT_NAME", "contoso-embedding"),
        },
        "agents": agents,
        "toolbox_version": toolbox_version,
        "knowledge": knowledge,
        "dataset": dataset,
        "evaluation_id": evaluation_id,
        "notes": [
            "Set FOUNDRY_RAI_POLICY_NAME to create the guarded agent.",
            "Knowledge/index creation is intentionally separate because it requires an Azure AI Search endpoint and source files.",
            "Hosted-agent deployment is performed by the part8-hosted-agent sample after the shared project is ready.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[ok] manifest: {manifest_path.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-azure", action="store_true", help="Only create Foundry project assets.")
    parser.add_argument("--skip-assets", action="store_true", help="Only create Azure resource/project/deployments.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("AZURE_TENANT_ID", DEFAULTS["tenant_id"])
    os.environ.setdefault("AZURE_SUBSCRIPTION_ID", DEFAULTS["subscription_id"])
    credential = DefaultAzureCredential()
    subscription_id = value("AZURE_SUBSCRIPTION_ID", "subscription_id")

    if not args.skip_azure:
        ensure_resource_group(credential, subscription_id)
        ensure_foundry_resource(credential, subscription_id)
        ensure_project(credential, subscription_id)
        ensure_deployment(
            credential,
            subscription_id,
            optional("FAST_DEPLOYMENT_NAME", "contoso-fast"),
            value("FAST_MODEL_NAME", "fast_model"),
            value("FAST_MODEL_VERSION", "fast_version"),
            int(value("FAST_MODEL_CAPACITY", "capacity")),
        )
        ensure_deployment(
            credential,
            subscription_id,
            optional("QUALITY_DEPLOYMENT_NAME", "contoso-quality"),
            value("QUALITY_MODEL_NAME", "quality_model"),
            value("QUALITY_MODEL_VERSION", "quality_version"),
            int(value("QUALITY_MODEL_CAPACITY", "capacity")),
        )
        ensure_deployment(
            credential,
            subscription_id,
            optional("EMBEDDING_DEPLOYMENT_NAME", "contoso-embedding"),
            value("EMBEDDING_MODEL_NAME", "embedding_model"),
            value("EMBEDDING_MODEL_VERSION", "embedding_version"),
            int(value("EMBEDDING_MODEL_CAPACITY", "capacity")),
        )

    if not args.skip_assets:
        project = make_project_client(credential)
        with project:
            agents = create_agents(
                project,
                optional("FAST_DEPLOYMENT_NAME", "contoso-fast"),
                optional("QUALITY_DEPLOYMENT_NAME", "contoso-quality"),
            )
            toolbox_version = create_toolbox(project)
            knowledge = create_knowledge_assets(project)
            dataset = upload_evaluation_assets(project)
            evaluation_id = create_evaluation(
                project,
                optional("QUALITY_DEPLOYMENT_NAME", "contoso-quality"),
                dataset,
            )
            write_manifest(agents, dataset, evaluation_id, toolbox_version, knowledge)

    print("\nEnvironment preparation completed.")
    print("Open the generated manifest and the Foundry project in https://ai.azure.com.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise
