# Source storage contract v2 — Proposed

This proposal addresses the actual intake capacity gap: the isolated v1 SQL
fixture stores at most 1 MiB of source bytes and 32 chunk locators. Those limits
cannot represent a 1 GiB source or the configured 64 MiB PDF extraction ceiling.
The frozen v1 schema, its tests and fixtures remain unchanged. This proposal is
not registered with live intake, SQL migrations, retrieval, or production routes.

## Isolated implementation and storage identity

`backend/evaluation/governed_answers/content_addressed_sources.py` supplies a
POSIX-only `ContentAddressedSourceStore(root).put(source_path,
expected_sha256=..., expected_byte_length=...)` primitive. Both paths are
absolute and component-canonical. The existing store directory must belong to
the running user and grant no group/other permissions. Every root/source path
component is opened without following symlinks. Sources must be regular,
nonempty files of at most **1,073,741,824 bytes**.

Objects have one flat canonical name: lowercase, 64-character SHA-256, with no
extension, supplied path, tenant name, or filename. The primitive streams in
1 MiB blocks into an exclusive random pending file with mode **0600**. It checks
expected length and digest, descriptor identity/size/timestamps before and after
reading, and reopens the source name to detect replacement before publication.
The completed pending file is fsynced. A same-directory hard link publishes the
canonical object exclusively; it never replaces an existing object. Pending-name
removal is followed by directory fsync. An existing object is reused only after
nofollow, regular-file, owner/mode, full length/hash, and change checks pass. Adoption also
fsyncs the verified existing descriptor before syncing the directory, so a retry
does not silently skip file durability.

No partially copied object is published. Concurrent publication can have one
creator and subsequent verified reuse; a detected concurrent metadata change
fails closed and can be retried. A failure after exclusive publication, including
directory fsync failure, may leave a **complete canonical file**. An exception is
not a rollback guarantee. Reconcile the hash key and retry rather than deleting
an object that a caller may already reference. A process crash can leave pending
files; eventual pending-file collection must be separately designed.

This is immutable-by-owner-convention content-addressed storage. The filesystem,
store owner, ancestry of the configured directory, and host are trusted. Hashes
provide byte identity, not encryption, principal authentication, permission,
content truth, a transactional index barrier, or durable backup. Mode 0600 still
allows the trusted owner to write; no kernel immutability flag is claimed.
Filesystem fsync/link semantics must be established on the eventual target
filesystem. Catalog and object cleanup must never treat this proposal as proof
that an object is unreferenced.

## Proposed SQL reference and ordered manifest

The separately versioned SQL representation should reference source objects;
it should not inline the entire source blob or manifest into a v1-size JSON row.
The following shape is a contract proposal, not executable DDL:

```text
source_object
  source_sha256: lowercase SHA-256 primary key
  source_byte_length: integer 1..1073741824
  object_store_version: "source-cas-v2"

document_version
  document_version_id: immutable identifier
  scope: authoritative organization/module/topic/collection identity
  source_sha256: foreign key -> source_object
  source_byte_length: exact source reference length
  extraction_policy_sha256: hash of exact extraction + chunking policy
  chunk_count: integer 0..100000
  lifecycle/content/index epochs: explicit authoritative version bindings
  state: explicit pending/active/archived/tombstoned/failed lifecycle

chunk_locator
  document_version_id: foreign key -> document_version
  chunk_index: integer 0..99999
  chunk_sha256: lowercase SHA-256 of exact stored UTF-8 bytes
  chunk_byte_length: integer 1..65536
  storage_reference: versioned canonical chunk-object identifier
  primary key(document_version_id, chunk_index)
```

The source CAS primitive does not implement SQL records. The separate isolated
`content_addressed_chunks.py` now supplies chunk-object publication and verified
reads as described below; versioned SQL references and a manifest publication
barrier remain open.
Human filenames and folder-relative metadata are descriptive fields, never
filesystem locations or authority. Shared source-byte hashes do not imply shared
scope, lifecycle, permission, or document identity.

Read manifests in bounded pages of at most **256 locators**, ordered by
`chunk_index`, using `(document_version_id, next_chunk_index)` keyset pagination.
A completed manifest of at most 100,000 locators therefore has at most 391 pages.
All pages must bind the same immutable document version, declared count,
extraction policy, source hash, and authoritative epochs. Enforce contiguous
indices from zero through count minus one, unique locator identities, exact
counts and bytes, and no missing, repeated, additional, or reordered pages.
An interrupted paged read must not expose a partial manifest as verified.

The current chunker uses 1,000 characters with 200-character overlap, advancing
800 characters. At the 64 MiB UTF-8 extraction ceiling, the largest character
count is 67,108,864, so at most **83,887 chunks** are produced. Multibyte text has
fewer characters for the same byte ceiling. A 1,000-character UTF-8 chunk is at
most 4,000 bytes, within the proposed 64 KiB per-chunk cap. Future chunk policies
must independently enforce both count and byte limits; truncation is not an
acceptable overflow strategy. Zero-chunk versions may preserve a source in a
stored/pending state and must not become active searchable evidence.

## Migration and verification gates

Before any live migration, bind a reviewed plan to the exact source inventory,
catalog/index checkpoint, destination store identity, schema revision, and backup.
Rehearse streamed copy, deduplication, process interruption, post-publication
fsync failure, rollback/reference reconciliation, and restart on an isolated copy.
Verify every source object's length/hash and the complete ordered manifest;
then recheck authority and lifecycle around external awaits and before exposure.
A database transaction cannot by itself atomically publish a remote index.
Define the explicit publication barrier, reader rejection behavior and recovery
journal before calling those epochs authoritative.

No existing upload, application database, index, source catalog or release flag
is changed by this proposal or primitive. Actual migration still requires its
final concrete review and authorization. Sprint completion, human acceptance,
semantic accuracy and production enablement are separate gates.

## Isolated chunk-object implementation — 2026-11-13

`ContentAddressedChunkStore` uses a separately configured private root and flat
SHA-256 names. `put` accepts a regular source file plus expected digest and length,
validates nonempty strict UTF-8 up to 65,536 bytes, then uses the streamed source
publisher to independently recheck and durably publish those exact bytes. No text
normalization or replacement occurs. Zero-chunk documents remain a catalog concern.

`read` requires the expected digest and length, opens without following symlinks,
checks regular-file identity, owner and mode 0600, bounds the read, verifies exact
length/hash/UTF-8 and descriptor stability, then reopens the canonical name to
check replacement before returning bytes. The trusted owner/filesystem assumption
still applies; returned bytes convey no scope, lifecycle, permission or authority.
Separate source/chunk roots are a caller configuration requirement. No application
writer, SQL reference, paginated manifest or production reader is registered.

Validation: 48 focused chunk/source tests passed. Cases include maximum size,
invalid UTF-8, oversized/empty objects, exact byte preservation, deduplication,
post-validation source replacement, and read rejection after byte/permission/
symlink/truncation tampering. Source publication durability tests remain included.
