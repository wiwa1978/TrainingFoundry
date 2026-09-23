r"""
Prepare optional model deployments for the Foundry Chat App demonstrations.

This file is intentionally separate from prepare_environment.py. It does not
change the core workshop setup; it adds model deployments used by optional
media and app demonstrations:

    - Text chat/comparison: gpt-5.5 and gpt-4o-mini
    - Image generation and image-to-image editing: gpt-image-1
    - Embeddings for Document Q&A and retail search: text-embedding-3-small
      and text-embedding-3-large
    - Traditional voice: gpt-4o-mini-transcribe and gpt-audio-mini
    - Realtime voice/transcription/translation: gpt-realtime-2.1 and
      gpt-realtime-translate

Run:
    az login --tenant 1b9b5045-f788-4fc4-8a5b-b04bf80ecd9a
    python C:\Code\Training Foundry\prepare_environment_use_cases.py

The tenant and subscription defaults come from the Azure CLI context used for
the workshop. Override every setting with environment variables. This script
does not contain secrets or API keys.

Install:
    pip install azure-identity azure-mgmt-cognitiveservices

Important:
    - Model availability, model versions, regions and quota are controlled by
      the Foundry catalog. Override *_MODEL_VERSION when the catalog shows a
      different version.
    - Azure AI Speech (MAI-Transcribe-1.5), Voice Live, Azure AI Search,
      Blob Storage and Cosmos DB are separate service/resource concerns. The
      script writes their expected app settings but does not silently create
      extra billable services. Use the existing Foundry Chat App Bicep for
      those resources when you decide to demonstrate them.
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


DEFAULTS = {
    "tenant_id": "1b9b5045-f788-4fc4-8a5b-b04bf80ecd9a",
    "subscription_id": "c396918f-565f-458c-87b5-4dfe9b6959a8",
    "resource_group": "rg-training-foundry",
    "foundry_resource": "foundry-training-contoso",
    "foundry_project": "contoso-field-service",
    "location": "eastus",
    "api_version": "2025-04-01-preview",
    "sku": "GlobalStandard",
    "chat_capacity": "10",
    "media_capacity": "1",
    "embedding_capacity": "10",
}


def setting(name: str, default_key: str | None = None) -> str:
    name = name.upper()
    configured = os.getenv(name, "").strip()
    if configured:
        return configured
    if default_key is not None:
        return DEFAULTS[default_key]
    raise RuntimeError(f"Missing required setting: {name}")


def optional(name: str, default: str = "") -> str:
    return os.getenv(name.upper(), default).strip()


def project_endpoint() -> str:
    configured = optional("FOUNDRY_PROJECT_ENDPOINT") or optional("AZURE_AI_PROJECT_ENDPOINT")
    if configured:
        return configured.rstrip("/")
    return (
        f"https://{setting('AZURE_FOUNDRY_RESOURCE_NAME', 'foundry_resource')}"
        ".services.ai.azure.com/api/projects/"
        f"{setting('AZURE_FOUNDRY_PROJECT_NAME', 'foundry_project')}"
    )


def deploy(
    client: CognitiveServicesManagementClient,
    name: str,
    model: str,
    version: str,
    capacity: int,
) -> dict[str, Any]:
    result = client.deployments.begin_create_or_update(
        resource_group_name=setting("AZURE_RESOURCE_GROUP", "resource_group"),
        account_name=setting("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource"),
        deployment_name=name,
        deployment=Deployment(
            sku=Sku(name=setting("MODEL_SKU_NAME", "sku"), capacity=capacity),
            properties=DeploymentProperties(
                model=DeploymentModel(format="OpenAI", name=model, version=version)
            ),
        ),
    ).result()
    state = getattr(result.properties, "provisioning_state", "unknown")
    print(f"[ok] {name}: {model} {version} ({state})")
    return {
        "deployment": name,
        "model": model,
        "version": version,
        "capacity": capacity,
        "provisioning_state": state,
    }


def model_plan() -> list[dict[str, Any]]:
    common_version = optional("MODEL_VERSION", "2025-04-14")
    return [
        {
            "purpose": "text_chat_and_comparison",
            "name": optional("CHAT_QUALITY_DEPLOYMENT", "gpt-5.5"),
            "model": optional("CHAT_QUALITY_MODEL", "gpt-5.5"),
            "version": optional("CHAT_QUALITY_MODEL_VERSION", common_version),
            "capacity": int(optional("CHAT_QUALITY_CAPACITY", DEFAULTS["chat_capacity"])),
            "app_setting": "FOUNDRY_MODELS",
        },
        {
            "purpose": "text_chat_and_comparison",
            "name": optional("CHAT_FAST_DEPLOYMENT", "gpt-4o-mini"),
            "model": optional("CHAT_FAST_MODEL", "gpt-4o-mini"),
            "version": optional("CHAT_FAST_MODEL_VERSION", common_version),
            "capacity": int(optional("CHAT_FAST_CAPACITY", DEFAULTS["chat_capacity"])),
            "app_setting": "FOUNDRY_MODELS",
        },
        {
            "purpose": "text_to_image_and_image_to_image",
            "name": optional("IMAGE_DEPLOYMENT", "gpt-image-1"),
            "model": optional("IMAGE_MODEL", "gpt-image-1"),
            "version": optional("IMAGE_MODEL_VERSION", common_version),
            "capacity": int(optional("IMAGE_CAPACITY", DEFAULTS["media_capacity"])),
            "app_setting": "FOUNDRY_MODELS",
        },
        {
            "purpose": "document_qa_and_rag",
            "name": optional("EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
            "model": optional("EMBEDDING_MODEL", "text-embedding-3-small"),
            "version": optional("EMBEDDING_MODEL_VERSION", "1"),
            "capacity": int(optional("EMBEDDING_CAPACITY", DEFAULTS["embedding_capacity"])),
            "app_setting": "FOUNDRY_EMBEDDING_MODEL",
        },
        {
            "purpose": "retail_catalog_search_optional",
            "name": optional("RETAIL_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
            "model": optional("RETAIL_EMBEDDING_MODEL", "text-embedding-3-large"),
            "version": optional("RETAIL_EMBEDDING_MODEL_VERSION", "1"),
            "capacity": int(optional("RETAIL_EMBEDDING_CAPACITY", DEFAULTS["embedding_capacity"])),
            "app_setting": "FOUNDRY_RETAIL_CATALOG_EMBEDDING_MODEL",
        },
        {
            "purpose": "traditional_voice_transcription",
            "name": optional("TRANSCRIPTION_DEPLOYMENT", "gpt-4o-mini-transcribe"),
            "model": optional("TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
            "version": optional("TRANSCRIPTION_MODEL_VERSION", common_version),
            "capacity": int(optional("MEDIA_CAPACITY", DEFAULTS["media_capacity"])),
            "app_setting": "FOUNDRY_TRANSCRIPTION_MODEL",
        },
        {
            "purpose": "traditional_voice_tts",
            "name": optional("TTS_DEPLOYMENT", "gpt-audio-mini"),
            "model": optional("TTS_MODEL", "gpt-audio-mini"),
            "version": optional("TTS_MODEL_VERSION", common_version),
            "capacity": int(optional("MEDIA_CAPACITY", DEFAULTS["media_capacity"])),
            "app_setting": "FOUNDRY_TTS_MODEL",
        },
        {
            "purpose": "realtime_voice",
            "name": optional("REALTIME_DEPLOYMENT", "gpt-realtime-2.1"),
            "model": optional("REALTIME_MODEL", "gpt-realtime-2.1"),
            "version": optional("REALTIME_MODEL_VERSION", common_version),
            "capacity": int(optional("REALTIME_CAPACITY", DEFAULTS["media_capacity"])),
            "app_setting": "FOUNDRY_REALTIME_MODEL",
        },
        {
            "purpose": "realtime_translation",
            "name": optional("REALTIME_TRANSLATION_DEPLOYMENT", "gpt-realtime-translate"),
            "model": optional("REALTIME_TRANSLATION_MODEL", "gpt-realtime-translate"),
            "version": optional("REALTIME_TRANSLATION_MODEL_VERSION", common_version),
            "capacity": int(optional("REALTIME_TRANSLATION_CAPACITY", DEFAULTS["media_capacity"])),
            "app_setting": "FOUNDRY_REALTIME_TRANSLATION_MODEL",
        },
    ]


def write_manifest(deployments: list[dict[str, Any]]) -> Path:
    output = Path(
        optional(
            "FOUNDRY_USE_CASE_MANIFEST_PATH",
            str(Path.cwd() / "foundry-chat-use-cases-manifest.json"),
        )
    )
    by_setting: dict[str, list[str]] = {}
    for item in deployments:
        by_setting.setdefault(item["app_setting"], []).append(
            item.get("deployment", item["name"])
        )
    manifest = {
        "tenant_id": setting("AZURE_TENANT_ID", "tenant_id"),
        "subscription_id": setting("AZURE_SUBSCRIPTION_ID", "subscription_id"),
        "resource_group": setting("AZURE_RESOURCE_GROUP", "resource_group"),
        "foundry_resource": setting("AZURE_FOUNDRY_RESOURCE_NAME", "foundry_resource"),
        "foundry_project": setting("AZURE_FOUNDRY_PROJECT_NAME", "foundry_project"),
        "project_endpoint": project_endpoint(),
        "deployments": deployments,
        "app_settings": {
            "FOUNDRY_PROJECT_ENDPOINT": project_endpoint(),
            "FOUNDRY_MODELS": ",".join(
                by_setting.get("FOUNDRY_MODELS", [])
            ),
            "FOUNDRY_EMBEDDING_MODEL": optional(
                "EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
            ),
            "FOUNDRY_RETAIL_CATALOG_EMBEDDING_MODEL": optional(
                "RETAIL_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"
            ),
            "FOUNDRY_TRANSCRIPTION_MODEL": optional(
                "TRANSCRIPTION_DEPLOYMENT", "gpt-4o-mini-transcribe"
            ),
            "FOUNDRY_TTS_MODEL": optional("TTS_DEPLOYMENT", "gpt-audio-mini"),
            "FOUNDRY_REALTIME_MODEL": optional("REALTIME_DEPLOYMENT", "gpt-realtime-2.1"),
            "FOUNDRY_REALTIME_TRANSLATION_MODEL": optional(
                "REALTIME_TRANSLATION_DEPLOYMENT", "gpt-realtime-translate"
            ),
            "AZURE_SPEECH_TRANSCRIPTION_MODEL": optional(
                "AZURE_SPEECH_TRANSCRIPTION_MODEL", "MAI-Transcribe-1.5"
            ),
            "AZURE_VOICELIVE_MODEL": optional("AZURE_VOICELIVE_MODEL", "gpt-realtime"),
            "AZURE_VOICELIVE_VOICE": optional(
                "AZURE_VOICELIVE_VOICE", "en-US-Ava:DragonHDLatestNeural"
            ),
            "AZURE_STORAGE_CONTAINER_NAME": optional(
                "AZURE_STORAGE_CONTAINER_NAME", "foundry-rag-documents"
            ),
            "AZURE_SEARCH_INDEX_NAME": optional(
                "AZURE_SEARCH_INDEX_NAME", "foundry-document-rag"
            ),
        },
        "external_services_to_configure_if_used": {
            "AZURE_SPEECH_ENDPOINT": "Azure AI Speech resource endpoint",
            "AZURE_VOICELIVE_ENDPOINT": "Voice Live resource root endpoint",
            "AZURE_STORAGE_ACCOUNT_URL": "Blob Storage account URL",
            "AZURE_SEARCH_ENDPOINT": "Azure AI Search endpoint",
            "AZURE_COSMOS_ENDPOINT": "Cosmos DB endpoint for hosted app persistence",
        },
    }
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[ok] manifest: {output.resolve()}")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-optional-embeddings",
        action="store_true",
        help="Skip text-embedding-3-large, which is only needed for the retail catalog demo.",
    )
    parser.add_argument(
        "--only",
        choices=("all", "image", "voice", "realtime", "rag", "chat"),
        default="all",
        help="Deploy only a selected group of use-case models.",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Write the configuration manifest without calling Azure.",
    )
    return parser.parse_args()


def selected(item: dict[str, Any], group: str) -> bool:
    if group == "all":
        return True
    purpose = item["purpose"]
    return {
        "image": "image" in purpose,
        "voice": "traditional_voice" in purpose,
        "realtime": "realtime" in purpose,
        "rag": "rag" in purpose,
        "chat": "text_chat" in purpose,
    }[group]


def main() -> None:
    args = parse_args()
    os.environ.setdefault("AZURE_TENANT_ID", DEFAULTS["tenant_id"])
    os.environ.setdefault("AZURE_SUBSCRIPTION_ID", DEFAULTS["subscription_id"])
    plan = [
        item
        for item in model_plan()
        if selected(item, args.only)
        and not (args.skip_optional_embeddings and item["purpose"] == "retail_catalog_search_optional")
    ]
    if args.manifest_only:
        write_manifest(plan)
        return

    credential = DefaultAzureCredential()
    client = CognitiveServicesManagementClient(
        credential=credential,
        subscription_id=setting("AZURE_SUBSCRIPTION_ID", "subscription_id"),
        api_version=setting("COGNITIVE_SERVICES_API_VERSION", "api_version"),
    )
    deployed = [
        deploy(client, item["name"], item["model"], item["version"], item["capacity"])
        for item in plan
    ]
    write_manifest(deployed)
    print("\nOptional Foundry Chat App model preparation completed.")
    print("Use the manifest values in the app's .env and configure external services only for demos you select.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise
