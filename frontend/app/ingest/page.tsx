"use client";

import { useState } from "react";
import { uploadFile, uploadFiles } from "../../services/ingestService";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSingleUpload = async () => {
    if (!file) return;

    setLoading(true);
    await uploadFile(file);
    alert("File uploaded successfully");
    setLoading(false);
  };

  const handleMultiUpload = async () => {
    if (!files.length) return;

    setLoading(true);
    await uploadFiles(files);
    alert("Files uploaded successfully");
    setLoading(false);
  };

  return (
    <div className="p-10 space-y-10">

      <h1 className="text-2xl font-semibold">📂 Document Ingestion</h1>

      {/* Single Upload */}
      <div className="bg-slate-900 p-6 rounded-xl space-y-4">
        <h2 className="text-lg">Upload Single File</h2>

        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <button
          onClick={handleSingleUpload}
          className="bg-indigo-600 px-4 py-2 rounded"
        >
          Upload File
        </button>
      </div>

      {/* Multiple Upload */}
      <div className="bg-slate-900 p-6 rounded-xl space-y-4">
        <h2 className="text-lg">Upload Multiple Files</h2>

        <input
          type="file"
          multiple
          onChange={(e) =>
            setFiles(Array.from(e.target.files || []))
          }
        />

        <button
          onClick={handleMultiUpload}
          className="bg-indigo-600 px-4 py-2 rounded"
        >
          Upload Files
        </button>
      </div>

    </div>
  );
}