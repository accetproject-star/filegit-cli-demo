import json
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class VerificationMethod(BaseModel):
    type: str = "Ed25519VerificationKey2020"
    public_key_multibase: str


class OwnerConfig(BaseModel):
    did: str
    verification_method: VerificationMethod


class Policy(BaseModel):
    id: str
    title: str
    path: str
    hash: str
    level: str


class Spec(BaseModel):
    id: str
    title: str
    path: str
    hash: str


class Rule(BaseModel):
    id: str
    title: str
    path: str
    hash: str


class ContextBlock(BaseModel):
    specs: List[Spec] = Field(default_factory=list)
    rules: List[Rule] = Field(default_factory=list)


class Permissions(BaseModel):
    allowed_agents: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)


class Revocation(BaseModel):
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    reason: Optional[str] = None


class Signature(BaseModel):
    algorithm: str = "Ed25519"
    key_id: str
    signature: str


class FileGitManifest(BaseModel):
    version: str = "1.0.0"
    id: str
    owner: OwnerConfig
    created_at: datetime
    valid_from: datetime
    valid_until: datetime
    status: str = "active"
    policies: List[Policy] = Field(default_factory=list)
    context: ContextBlock = Field(default_factory=ContextBlock)
    permissions: Permissions = Field(default_factory=Permissions)
    dependencies: List[str] = Field(default_factory=list)
    revocation: Revocation = Field(default_factory=Revocation)
    signatures: List[Signature] = Field(default_factory=list)

    def to_signable_bytes(self) -> bytes:
        """
        Returns the deterministic JSON byte representation of the manifest
        excluding the 'signatures' field, which is used for
        creating/verifying signatures.
        """
        data = self.model_dump(mode="json", exclude={"signatures"})
        # Use Pydantic's JSON serialization to ensure deterministic
        # datetime formatting etc.
        # But we must ensure keys are sorted for deterministic hashing.
        import json

        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


class TraceAction(BaseModel):
    action_type: str
    description: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionTrace(BaseModel):
    trace_id: str
    agent_id: str
    prompt: str
    actions: List[TraceAction] = []
    bundle_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signature: Optional[Signature] = None

    def to_signable_bytes(self) -> bytes:
        dump = self.model_dump(exclude={"signature"}, mode="json")
        return json.dumps(dump, sort_keys=True).encode("utf-8")
