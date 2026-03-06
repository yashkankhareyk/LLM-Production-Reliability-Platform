"use client";

import { useEffect, useState } from "react";
import { getDocuments, deleteDocuments } from "../../services/ingestService";

export default function DocumentsPage() {

  const [docs, setDocs] = useState<any[]>([]);

  const loadDocs = async () => {
    const data = await getDocuments();
    setDocs(data);
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleDelete = async () => {
    await deleteDocuments();
    loadDocs();
  };

  return (
    <div className="p-10 space-y-6">

      <h1 className="text-2xl font-semibold">📄 Ingested Documents</h1>

      <button
        onClick={handleDelete}
        className="bg-red-600 px-4 py-2 rounded"
      >
        Delete All Documents
      </button>

      <div className="space-y-4">

        {docs.map((doc, i) => (
          <div
            key={i}
            className="bg-slate-900 p-4 rounded"
          >
            {JSON.stringify(doc)}
          </div>
        ))}

      </div>

    </div>
  );
}