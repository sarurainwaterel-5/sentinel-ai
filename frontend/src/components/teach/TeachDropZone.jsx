import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { submitTeachingMission } from "../../services/knowledgeApi";
import { useDomain } from "../../context/useDomain";
import { useWorkspaceData } from "../workspaces/useWorkspaceData";
import { ResourceState } from "../workspaces/WorkspaceParts";

function normalizeRelativePath(value) {
  if (!value) return "";
  if (typeof value !== "string" || value.length > 1024 || (value.includes("\\") || Array.from(value).some((char) => char.charCodeAt(0) < 32)) || value.startsWith("/") || /^[a-z]:/i.test(value)) return null;
  const parts = value.split("/");
  return parts.some((part) => !part || part === "." || part === "..") ? null : parts.join("/");
}

export default function TeachDropZone({ onAccepted }) {
  const uploading = useRef(false);
  const { activeDomain } = useDomain();
  const config = useWorkspaceData("/teach/config");
  const [files, setFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);
  const [topic, setTopic] = useState("general");
  const [description, setDescription] = useState("");
  const limit = config.data?.max_upload_bytes;
  const formats = config.data?.supported_formats ?? ["pdf"];
  const extensions = formats.map((format) => format.toLowerCase().replace(/^\./, ""));
  const batchLimit = Math.min(100, config.data?.max_batch_files ?? 100);
  const specificDomain = activeDomain && activeDomain.id !== "all";
  const validate = (file, path) => {
    const ext = file.name.split(".").pop().toLowerCase();
    if (path === null) return "Invalid folder-relative path.";
    if (!config.data?.allow_other_files && !extensions.includes(ext)) return "Unsupported file format.";
    if (!file.size) return "Empty file.";
    if (file.size > Math.min(limit ?? 0, config.data?.format_limits?.[ext] ?? limit ?? 0)) return "File exceeds the upload size limit.";
    return null;
  };
  const selectFiles = (selection) => {
    if (uploading.current) return;
    if (selection.length > batchLimit) { setFiles([]); setMessage(`Select at most ${batchLimit} files per batch.`); return; }
    setFiles(Array.from(selection, (file, index) => {
      const relativePath = normalizeRelativePath(file.webkitRelativePath);
      const error = validate(file, relativePath);
      return { file, relativePath, key: index, status: error ? "invalid" : "ready", error };
    }));
    setMessage(null);
  };
  const submit = async (event) => {
    event.preventDefault();
    if (!specificDomain || !limit || uploading.current) return;
    uploading.current = true; setSubmitting(true); setMessage(null);
    let accepted = 0;
    try {
      for (const item of files.filter((entry) => ["ready", "failed"].includes(entry.status))) {
        const error = validate(item.file, item.relativePath);
        const update = (changes) => setFiles((current) => current.map((entry) => entry.key === item.key ? { ...entry, ...changes } : entry));
        if (error) { update({ status: "invalid", error }); continue; }
        update({ status: "uploading", error: null });
        let mission;
        try {
          mission = await submitTeachingMission({ file: item.file, domainId: activeDomain.id, topic, description, ...(item.relativePath ? { relativePath: item.relativePath } : {}) });
        } catch (failure) {
          update({ status: failure.submissionUnconfirmed ? "unconfirmed" : "failed", error: failure.message });
          continue;
        }
        accepted += 1; update({ status: "accepted", error: null });
        onAccepted?.(mission);
      }
      setMessage(`${accepted} mission${accepted === 1 ? "" : "s"} accepted. Follow observed progress below. Failed files remain available for retry; accepted files will not be resent.`);
    } finally { uploading.current = false; setSubmitting(false); }
  };
  return <section className="remember-dropzone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => {
    event.preventDefault(); if (uploading.current) return;
    if (Array.from(event.dataTransfer.items ?? []).some((item) => item.webkitGetAsEntry?.()?.isDirectory)) { setMessage("For folders, use Choose folder so relative paths and file limits can be checked."); return; }
    selectFiles(event.dataTransfer.files);
  }}>
    <UploadCloud size={32} aria-hidden="true" /><h2>Teach Sentinel</h2>
    <p>Choose trusted files or a folder. Each file creates its own mission in the selected domain.</p>
    <ResourceState resource={config} label="upload limits"><p className="muted">{extensions.join(", ").toUpperCase()} · Up to {Math.round((limit ?? 0) / 1024 / 1024)} MB per file · At most {batchLimit} files.</p></ResourceState>
    <p className="muted">{config.data?.image_ocr_available ? "PNG and JPEG images use local text recognition (OCR)." : "Image OCR is currently unavailable on the server; images can still be stored."} {config.data?.audio_transcription_available ? "Video speech is transcribed locally with timestamps, alongside sampled visual text." : "Videos provide sampled visual text. Local speech transcription is currently unavailable."} A stored source may not be indexed or available in Recall.</p>
    {!specificDomain && <p className="workspace-notice">Choose a specific domain in the header before beginning a mission.</p>}
    <form className="workspace-form teach-form" onSubmit={submit}>
      <label>Files<input type="file" multiple accept={config.data?.allow_other_files ? undefined : extensions.map((ext) => `.${ext}`).join(",")} disabled={submitting || !limit} onChange={(event) => selectFiles(event.target.files)} /></label>
      <label>Choose folder<input type="file" multiple webkitdirectory="" disabled={submitting || !limit} onChange={(event) => selectFiles(event.target.files)} /></label>
      <ul aria-label="Selected files">{files.map((item) => <li key={item.key}>{item.relativePath || item.file.name} · {item.status}{item.error && `: ${item.error}`}{item.status === "unconfirmed" && " Refresh mission history before choosing this file again."}</li>)}</ul>
      <div className="workspace-grid"><label>Topic<input value={topic} maxLength={200} disabled={submitting} onChange={(event) => setTopic(event.target.value)} /></label><label>Teaching context<textarea value={description} maxLength={2000} disabled={submitting} placeholder="Optional source context for future retrieval" onChange={(event) => setDescription(event.target.value)} /></label></div>
      <p className="muted">Destination: {activeDomain?.name ?? "All Domains"}. Folder paths are descriptive metadata. Exact duplicates are detected across the catalog.</p>
      <button className="primary-action" type="submit" disabled={submitting || !files.some((item) => ["ready", "failed"].includes(item.status)) || !specificDomain || !limit}>{submitting ? "Receiving files…" : "Begin Teaching"}</button>
    </form>
    {message && <p className="teach-status" role="status">{message}</p>}
  </section>;
}
