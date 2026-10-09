import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { submitTeachingMission } from "../../services/knowledgeApi";
import { useDomain } from "../../context/useDomain";
import { useWorkspaceData } from "../workspaces/useWorkspaceData";
import { ResourceState } from "../workspaces/WorkspaceParts";

export default function TeachDropZone({ onAccepted }) {
  const fileInputRef = useRef(null);
  const { activeDomain } = useDomain();
  const config = useWorkspaceData("/teach/config");
  const [selectedFile, setSelectedFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);
  const [topic, setTopic] = useState("general");
  const [description, setDescription] = useState("");
  const limit = config.data?.max_upload_bytes;
  const specificDomain = activeDomain && activeDomain.id !== "all";
  const selectFile = (files) => {
    if (submitting) return;
    setSelectedFile(null);
    if (files?.length !== 1) { setMessage("Select one PDF per mission. You can queue additional missions separately."); return; }
    const file = files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) { setMessage("Only PDF documents are supported."); return; }
    if (!file.size || (limit && file.size > limit)) { setMessage("Select a non-empty PDF within the upload size limit."); return; }
    setSelectedFile(file); setMessage(null);
  };
  const submit = async (event) => {
    event.preventDefault();
    if (!selectedFile || !specificDomain || !limit || submitting) return;
    if (selectedFile.size > limit) { setMessage("This PDF exceeds the current upload size limit."); return; }
    try {
      setSubmitting(true); setMessage(null);
      const mission = await submitTeachingMission({ file: selectedFile, domainId: activeDomain.id, topic, description });
      onAccepted(mission);
      setSelectedFile(null); fileInputRef.current.value = "";
      setMessage("Mission accepted. Follow its observed progress below; you may leave this workspace while it runs.");
    } catch (error) { setMessage(error.message); }
    finally { setSubmitting(false); }
  };
  return <section className="remember-dropzone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); selectFile(event.dataTransfer.files); }}>
    <UploadCloud size={32} aria-hidden="true" /><h2>Teach Sentinel</h2>
    <p>Choose a trusted, text-based PDF. Each mission preserves its source and selected domain.</p>
    <ResourceState resource={config} label="upload limits"><p className="muted">PDF only · Up to {Math.round((limit ?? 0) / 1024 / 1024)} MB · Scanned PDFs require OCR before upload.</p></ResourceState>
    {!specificDomain && <p className="workspace-notice">Choose a specific domain in the header before beginning a mission.</p>}
    <form className="workspace-form teach-form" onSubmit={submit}>
      <label>PDF document<input ref={fileInputRef} type="file" accept=".pdf,application/pdf" disabled={submitting} onChange={(event) => selectFile(event.target.files)} /></label>
      {selectedFile && <p>Selected: <strong>{selectedFile.name}</strong> · {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>}
      <div className="workspace-grid"><label>Topic<input value={topic} maxLength={200} disabled={submitting} onChange={(event) => setTopic(event.target.value)} /></label><label>Teaching context<textarea value={description} maxLength={2000} disabled={submitting} placeholder="Optional source context for future retrieval" onChange={(event) => setDescription(event.target.value)} /></label></div>
      <p className="muted">Destination: {activeDomain?.name ?? "All Domains"}. Exact duplicates are detected across the catalog; they are not silently moved between domains.</p>
      <button className="primary-action" type="submit" disabled={submitting || !selectedFile || !specificDomain || !limit}>{submitting ? "Receiving PDF…" : "Begin Teaching"}</button>
    </form>
    {message && <p className="teach-status" role="status">{message}</p>}
  </section>;
}
