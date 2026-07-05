import { UploadCloud } from "lucide-react";

export default function RememberDropZone() {
  return (
    <section className="remember-dropzone">
      <UploadCloud size={42} />
      <h2>Drop knowledge here</h2>
      <p>PDF, Markdown, text, and runbooks are ready to be remembered.</p>
      <button className="primary-action">Choose Files</button>
    </section>
  );
}
