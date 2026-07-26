import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { uploadKnowledge } from "../../services/knowledgeApi";
import { useDomain } from "../../context/useDomain";

export default function TeachDropZone() {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
const { activeDomain } = useDomain();

const [isTeaching, setIsTeaching] = useState(false);
const [message, setMessage] = useState(null);
const handleTeach = async () => {
  if (!selectedFile) {
    setMessage("Select knowledge before teaching Sentinel.");
    return;
  }

  if (!activeDomain || activeDomain.id === "all") {
    setMessage(
      "Select a specific domain before teaching Sentinel.",
    );
    return;
  }

  try {
    setIsTeaching(true);
    setMessage(null);

    const result = await uploadKnowledge({
      file: selectedFile,
      domainId: activeDomain.id,
    });

    if (result.status === "indexed") {
      setMessage(
        `Sentinel successfully learned '${result.filename}'.`,
      );
    } else if (result.status === "duplicate") {
      setMessage(
        `'${result.filename}' is already part of Sentinel's knowledge.`,
      );
    } else {
      setMessage("Teaching mission completed.");
    }

    setSelectedFile(null);
  } catch (error) {
    setMessage(error.message);
  } finally {
    setIsTeaching(false);
  }
};
  return (
    <section className="remember-dropzone">
      <input
        ref={fileInputRef}
        type="file"
        hidden
        accept=".pdf"
        onChange={(event) => {
          const file = event.target.files?.[0];

          if (file) {
            setSelectedFile(file);
          }
        }}
      />

      <UploadCloud size={42} />

      <h2>Teach Sentinel</h2>

      <p>
        Teach Sentinel through trusted documents, playbooks,
        standards, and evidence.
      </p>

      {selectedFile && (
        <p className="selected-file">
          <strong>Selected Knowledge:</strong>{" "}
          {selectedFile.name}
        </p>
      )}

      <button
        className="primary-action"
        onClick={
  selectedFile
    ? handleTeach
    : () => fileInputRef.current?.click()
}
      >
        {selectedFile
  ? isTeaching
    ? "Teaching..."
    : "Begin Teaching"
  : "Select Knowledge"}
      </button>
{message && (
  <p className="teach-status">
    {message}
  </p>
)}
    </section>
  );
}
